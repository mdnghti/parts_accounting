from datetime import datetime
import sqlite3
from typing import Optional

from db.connection import get_connection
from db.repositories import get_customer_by_id, get_supplier_by_id
from models.document import Document


class InventoryError(Exception):
    """Базовий клас для помилок складського обліку."""
    pass


class InsufficientStockError(InventoryError):
    """Помилка недостатньої кількості товару на складі."""
    pass


class DocumentValidationError(InventoryError):
    """Помилка валідації документу."""
    pass


def generate_doc_number(doc_type: str, conn: Optional[sqlite3.Connection] = None) -> str:
    """Генерація послідовного номера накладної (наприклад, ПР-2026-0001)."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        year = datetime.now().year
        prefix = "ПР" if doc_type == "incoming" else "ВР"
        like_pattern = f"{prefix}-{year}-%"

        cur.execute(
            "SELECT COUNT(*) FROM documents WHERE doc_type = ? AND doc_number LIKE ?",
            (doc_type, like_pattern),
        )
        count = cur.fetchone()[0] + 1
        return f"{prefix}-{year}-{count:04d}"
    finally:
        if should_close:
            c.close()


def process_incoming_document(doc: Document, conn: Optional[sqlite3.Connection] = None) -> int:
    """
    Проведення прибуткової накладної:
    - Валідація даних документа та контрагента-постачальника
    - Додавання документа та його рядків
    - Збільшення залишків запчастин на складі
    Все виконується в одній неподільній транзакції з відкатом при помилці.
    """
    if doc.doc_type != "incoming":
        raise DocumentValidationError("Тип документу повинен бути 'incoming' для приходу.")

    if not doc.doc_number or not doc.doc_number.strip():
        raise DocumentValidationError("Номер документу є обов'язковим.")

    if not doc.items:
        raise DocumentValidationError("Накладна не може бути порожньою (додайте хоча б одну позицію).")

    should_close = conn is None
    c = conn or get_connection()
    try:
        # Перевірка постачальника
        supplier = get_supplier_by_id(doc.counterparty_id, conn=c)
        if not supplier:
            raise DocumentValidationError(f"Постачальника з ID {doc.counterparty_id} не знайдено.")

        # Валідація позицій
        for item in doc.items:
            if item.quantity <= 0:
                raise DocumentValidationError(f"Кількість для запчастини ID {item.part_id} має бути більше 0.")
            if item.price < 0:
                raise DocumentValidationError(f"Ціна для запчастини ID {item.part_id} не може бути від'ємною.")

        # Проведення операцій у транзакції
        with c:
            cur = c.cursor()
            # 1. Запис документа в таблицю documents
            cur.execute(
                """
                INSERT INTO documents (doc_type, doc_number, doc_date, counterparty_id, user_id, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    doc.doc_type,
                    doc.doc_number.strip(),
                    doc.doc_date,
                    doc.counterparty_id,
                    doc.user_id,
                    doc.notes,
                ),
            )
            doc_id = cur.lastrowid

            # 2. Запис рядків та збільшення залишків
            for item in doc.items:
                # Перевіряємо існування запчастини
                cur.execute("SELECT id FROM parts WHERE id = ?", (item.part_id,))
                if not cur.fetchone():
                    raise DocumentValidationError(f"Запчастину з ID {item.part_id} не знайдено в базі.")

                cur.execute(
                    """
                    INSERT INTO document_items (document_id, part_id, quantity, price)
                    VALUES (?, ?, ?, ?)
                    """,
                    (doc_id, item.part_id, item.quantity, item.price),
                )

                # Збільшуємо залишок
                cur.execute(
                    "UPDATE parts SET stock_quantity = stock_quantity + ? WHERE id = ?",
                    (item.quantity, item.part_id),
                )

        return doc_id
    finally:
        if should_close:
            c.close()


def process_outgoing_document(doc: Document, conn: Optional[sqlite3.Connection] = None) -> int:
    """
    Проведення видаткової накладної:
    - Валідація даних документа та контрагента-покупця
    - Перевірка наявності товару на складі (заборона при недостачі)
    - Додавання документа та його рядків
    - Зменшення залишків запчастин на складі
    Все виконується в одній неподільній транзакції з відкатом при помилці.
    """
    if doc.doc_type != "outgoing":
        raise DocumentValidationError("Тип документу повинен бути 'outgoing' для розходу.")

    if not doc.doc_number or not doc.doc_number.strip():
        raise DocumentValidationError("Номер документу є обов'язковим.")

    if not doc.items:
        raise DocumentValidationError("Накладна не може бути порожньою (додайте хоча б одну позицію).")

    should_close = conn is None
    c = conn or get_connection()
    try:
        # Перевірка клієнта
        customer = get_customer_by_id(doc.counterparty_id, conn=c)
        if not customer:
            raise DocumentValidationError(f"Клієнта з ID {doc.counterparty_id} не знайдено.")

        # Валідація позицій
        for item in doc.items:
            if item.quantity <= 0:
                raise DocumentValidationError(f"Кількість для запчастини ID {item.part_id} має бути більше 0.")
            if item.price < 0:
                raise DocumentValidationError(f"Ціна для запчастини ID {item.part_id} не може бути від'ємною.")

        # Проведення операцій у транзакції
        with c:
            cur = c.cursor()
            # 1. Перевірка достатності залишків для кожної позиції
            for item in doc.items:
                cur.execute("SELECT part_number, name, stock_quantity FROM parts WHERE id = ?", (item.part_id,))
                part_row = cur.fetchone()
                if not part_row:
                    raise DocumentValidationError(f"Запчастину з ID {item.part_id} не знайдено в базі.")

                available_stock = part_row["stock_quantity"]
                if item.quantity > available_stock:
                    raise InsufficientStockError(
                        f"Недостатньо товару на складі для позиції '{part_row['name']}' "
                        f"(арт. {part_row['part_number']}). "
                        f"Запитувана кількість: {item.quantity}, в наявності: {available_stock}."
                    )

            # 2. Запис документа в таблицю documents
            cur.execute(
                """
                INSERT INTO documents (doc_type, doc_number, doc_date, counterparty_id, user_id, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    doc.doc_type,
                    doc.doc_number.strip(),
                    doc.doc_date,
                    doc.counterparty_id,
                    doc.user_id,
                    doc.notes,
                ),
            )
            doc_id = cur.lastrowid

            # 3. Запис рядків та списання залишків
            for item in doc.items:
                cur.execute(
                    """
                    INSERT INTO document_items (document_id, part_id, quantity, price)
                    VALUES (?, ?, ?, ?)
                    """,
                    (doc_id, item.part_id, item.quantity, item.price),
                )

                # Списуємо залишок
                cur.execute(
                    "UPDATE parts SET stock_quantity = stock_quantity - ? WHERE id = ?",
                    (item.quantity, item.part_id),
                )

        return doc_id
    finally:
        if should_close:
            c.close()
