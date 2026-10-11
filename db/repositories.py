import sqlite3
from typing import List, Optional

from db.connection import get_connection
from models.car import CarBrand, CarModel
from models.category import Category
from models.counterparty import Customer, Supplier
from models.document import Document, DocumentItem
from models.part import Part
from models.user import User


# ==========================================
# КАТЕГОРІЇ (CATEGORIES)
# ==========================================

def get_categories(conn: Optional[sqlite3.Connection] = None) -> List[Category]:
    """Отримати всі категорії запчастин."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute("SELECT id, name, description FROM categories ORDER BY name ASC")
        return [Category(id=r["id"], name=r["name"], description=r["description"]) for r in cur.fetchall()]
    finally:
        if should_close:
            c.close()


def get_category_by_id(cat_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Category]:
    """Отримати категорію за ID."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute("SELECT id, name, description FROM categories WHERE id = ?", (cat_id,))
        row = cur.fetchone()
        return Category(id=row["id"], name=row["name"], description=row["description"]) if row else None
    finally:
        if should_close:
            c.close()


def create_category(category: Category, conn: Optional[sqlite3.Connection] = None) -> int:
    """Створити нову категорію."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute(
            "INSERT INTO categories (name, description) VALUES (?, ?)",
            (category.name.strip(), category.description),
        )
        if should_close:
            c.commit()
        return cur.lastrowid
    finally:
        if should_close:
            c.close()


def update_category(category: Category, conn: Optional[sqlite3.Connection] = None) -> bool:
    """Оновити існуючу категорію."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute(
            "UPDATE categories SET name = ?, description = ? WHERE id = ?",
            (category.name.strip(), category.description, category.id),
        )
        if should_close:
            c.commit()
        return cur.rowcount > 0
    finally:
        if should_close:
            c.close()


def delete_category(cat_id: int, conn: Optional[sqlite3.Connection] = None) -> bool:
    """Видалити категорію (заборонено, якщо є прив'язані запчастини)."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
        if should_close:
            c.commit()
        return cur.rowcount > 0
    finally:
        if should_close:
            c.close()


# ==========================================
# МАРКИ ТА МОДЕЛІ АВТО (BRANDS & MODELS)
# ==========================================

def get_brands(conn: Optional[sqlite3.Connection] = None) -> List[CarBrand]:
    """Отримати всі марки авто."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute("SELECT id, name FROM car_brands ORDER BY name ASC")
        return [CarBrand(id=r["id"], name=r["name"]) for r in cur.fetchall()]
    finally:
        if should_close:
            c.close()


def get_brand_by_id(brand_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[CarBrand]:
    """Отримати марку авто за ID."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute("SELECT id, name FROM car_brands WHERE id = ?", (brand_id,))
        row = cur.fetchone()
        return CarBrand(id=row["id"], name=row["name"]) if row else None
    finally:
        if should_close:
            c.close()


def create_brand(brand: CarBrand, conn: Optional[sqlite3.Connection] = None) -> int:
    """Створити марку авто."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute("INSERT INTO car_brands (name) VALUES (?)", (brand.name.strip(),))
        if should_close:
            c.commit()
        return cur.lastrowid
    finally:
        if should_close:
            c.close()


def update_brand(brand: CarBrand, conn: Optional[sqlite3.Connection] = None) -> bool:
    """Оновити марку авто."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute("UPDATE car_brands SET name = ? WHERE id = ?", (brand.name.strip(), brand.id))
        if should_close:
            c.commit()
        return cur.rowcount > 0
    finally:
        if should_close:
            c.close()


def delete_brand(brand_id: int, conn: Optional[sqlite3.Connection] = None) -> bool:
    """Видалити марку авто."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute("DELETE FROM car_brands WHERE id = ?", (brand_id,))
        if should_close:
            c.commit()
        return cur.rowcount > 0
    finally:
        if should_close:
            c.close()


def get_models(brand_id: Optional[int] = None, conn: Optional[sqlite3.Connection] = None) -> List[CarModel]:
    """Отримати моделі авто (опціонально з фільтром за маркою)."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        if brand_id is not None:
            cur.execute(
                """
                SELECT m.id, m.brand_id, m.name, m.year_from, m.year_to, b.name AS brand_name
                FROM car_models m
                JOIN car_brands b ON m.brand_id = b.id
                WHERE m.brand_id = ?
                ORDER BY m.name ASC
                """,
                (brand_id,),
            )
        else:
            cur.execute(
                """
                SELECT m.id, m.brand_id, m.name, m.year_from, m.year_to, b.name AS brand_name
                FROM car_models m
                JOIN car_brands b ON m.brand_id = b.id
                ORDER BY b.name ASC, m.name ASC
                """
            )
        return [
            CarModel(
                id=r["id"],
                brand_id=r["brand_id"],
                name=r["name"],
                year_from=r["year_from"],
                year_to=r["year_to"],
                brand_name=r["brand_name"],
            )
            for r in cur.fetchall()
        ]
    finally:
        if should_close:
            c.close()


def get_model_by_id(model_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[CarModel]:
    """Отримати модель авто за ID."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute(
            """
            SELECT m.id, m.brand_id, m.name, m.year_from, m.year_to, b.name AS brand_name
            FROM car_models m
            JOIN car_brands b ON m.brand_id = b.id
            WHERE m.id = ?
            """,
            (model_id,),
        )
        r = cur.fetchone()
        if not r:
            return None
        return CarModel(
            id=r["id"],
            brand_id=r["brand_id"],
            name=r["name"],
            year_from=r["year_from"],
            year_to=r["year_to"],
            brand_name=r["brand_name"],
        )
    finally:
        if should_close:
            c.close()


def create_model(model: CarModel, conn: Optional[sqlite3.Connection] = None) -> int:
    """Створити модель авто."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute(
            """
            INSERT INTO car_models (brand_id, name, year_from, year_to)
            VALUES (?, ?, ?, ?)
            """,
            (model.brand_id, model.name.strip(), model.year_from, model.year_to),
        )
        if should_close:
            c.commit()
        return cur.lastrowid
    finally:
        if should_close:
            c.close()


def update_model(model: CarModel, conn: Optional[sqlite3.Connection] = None) -> bool:
    """Оновити модель авто."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute(
            """
            UPDATE car_models
            SET brand_id = ?, name = ?, year_from = ?, year_to = ?
            WHERE id = ?
            """,
            (model.brand_id, model.name.strip(), model.year_from, model.year_to, model.id),
        )
        if should_close:
            c.commit()
        return cur.rowcount > 0
    finally:
        if should_close:
            c.close()


def delete_model(model_id: int, conn: Optional[sqlite3.Connection] = None) -> bool:
    """Видалити модель авто."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute("DELETE FROM car_models WHERE id = ?", (model_id,))
        if should_close:
            c.commit()
        return cur.rowcount > 0
    finally:
        if should_close:
            c.close()


# ==========================================
# ЗАПЧАСТИНИ (PARTS)
# ==========================================

def get_parts(
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    brand_id: Optional[int] = None,
    low_stock_only: bool = False,
    conn: Optional[sqlite3.Connection] = None,
) -> List[Part]:
    """
    Отримати список запчастин з фільтрацією за пошуковим рядком, категорією, маркою та залишком.
    """
    should_close = conn is None
    c = conn or get_connection()
    try:
        query = """
            SELECT DISTINCT p.id, p.part_number, p.name, p.category_id, p.price,
                   p.stock_quantity, p.min_stock_quantity, p.unit, c.name AS category_name
            FROM parts p
            JOIN categories c ON p.category_id = c.id
        """
        joins = []
        where_clauses = []
        params = []

        if brand_id is not None:
            joins.append("JOIN part_compatibility pc ON p.id = pc.part_id")
            joins.append("JOIN car_models cm ON pc.model_id = cm.id")
            where_clauses.append("cm.brand_id = ?")
            params.append(brand_id)

        try:
            c.create_function("py_lower", 1, lambda s: s.lower() if s is not None else "")
        except Exception:
            pass

        if search:
            search_pattern = f"%{search.strip().lower()}%"
            where_clauses.append("(py_lower(p.part_number) LIKE ? OR py_lower(p.name) LIKE ?)")
            params.extend([search_pattern, search_pattern])

        if category_id is not None:
            where_clauses.append("p.category_id = ?")
            params.append(category_id)

        if low_stock_only:
            where_clauses.append("p.stock_quantity <= p.min_stock_quantity")

        if joins:
            query += " " + " ".join(joins)
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        query += " ORDER BY p.name ASC"

        cur = c.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()

        parts_list = []
        for r in rows:
            parts_list.append(
                Part(
                    id=r["id"],
                    part_number=r["part_number"],
                    name=r["name"],
                    category_id=r["category_id"],
                    price=r["price"],
                    stock_quantity=r["stock_quantity"],
                    min_stock_quantity=r["min_stock_quantity"],
                    unit=r["unit"],
                    category_name=r["category_name"],
                )
            )
        return parts_list
    finally:
        if should_close:
            c.close()


def get_part_by_id(part_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Part]:
    """Отримати запчастину за ID разом із сумісними моделями."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute(
            """
            SELECT p.id, p.part_number, p.name, p.category_id, p.price,
                   p.stock_quantity, p.min_stock_quantity, p.unit, c.name AS category_name
            FROM parts p
            JOIN categories c ON p.category_id = c.id
            WHERE p.id = ?
            """,
            (part_id,),
        )
        r = cur.fetchone()
        if not r:
            return None

        # Отримуємо ID сумісних моделей
        cur.execute("SELECT model_id FROM part_compatibility WHERE part_id = ?", (part_id,))
        model_ids = [row[0] for row in cur.fetchall()]

        return Part(
            id=r["id"],
            part_number=r["part_number"],
            name=r["name"],
            category_id=r["category_id"],
            price=r["price"],
            stock_quantity=r["stock_quantity"],
            min_stock_quantity=r["min_stock_quantity"],
            unit=r["unit"],
            category_name=r["category_name"],
            compatible_model_ids=model_ids,
        )
    finally:
        if should_close:
            c.close()


def get_part_by_number(part_number: str, conn: Optional[sqlite3.Connection] = None) -> Optional[Part]:
    """Отримати запчастину за артикулом."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute("SELECT id FROM parts WHERE part_number = ?", (part_number.strip(),))
        row = cur.fetchone()
        return get_part_by_id(row["id"], conn=c) if row else None
    finally:
        if should_close:
            c.close()


def create_part(part: Part, conn: Optional[sqlite3.Connection] = None) -> int:
    """Створити нову запчастину з прив'язкою сумісності."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute(
            """
            INSERT INTO parts (part_number, name, category_id, price, stock_quantity, min_stock_quantity, unit)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                part.part_number.strip(),
                part.name.strip(),
                part.category_id,
                part.price,
                part.stock_quantity,
                part.min_stock_quantity,
                part.unit.strip(),
            ),
        )
        part_id = cur.lastrowid

        if part.compatible_model_ids:
            cur.executemany(
                "INSERT OR IGNORE INTO part_compatibility (part_id, model_id) VALUES (?, ?)",
                [(part_id, m_id) for m_id in part.compatible_model_ids],
            )

        if should_close:
            c.commit()
        return part_id
    finally:
        if should_close:
            c.close()


def update_part(part: Part, conn: Optional[sqlite3.Connection] = None) -> bool:
    """Оновити запчастину та її сумісність."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute(
            """
            UPDATE parts
            SET part_number = ?, name = ?, category_id = ?, price = ?,
                stock_quantity = ?, min_stock_quantity = ?, unit = ?
            WHERE id = ?
            """,
            (
                part.part_number.strip(),
                part.name.strip(),
                part.category_id,
                part.price,
                part.stock_quantity,
                part.min_stock_quantity,
                part.unit.strip(),
                part.id,
            ),
        )

        # Оновлення списку сумісності
        cur.execute("DELETE FROM part_compatibility WHERE part_id = ?", (part.id,))
        if part.compatible_model_ids:
            cur.executemany(
                "INSERT INTO part_compatibility (part_id, model_id) VALUES (?, ?)",
                [(part.id, m_id) for m_id in part.compatible_model_ids],
            )

        if should_close:
            c.commit()
        return cur.rowcount > 0
    finally:
        if should_close:
            c.close()


def delete_part(part_id: int, conn: Optional[sqlite3.Connection] = None) -> bool:
    """Видалити запчастину (заборонено, якщо фігурує в документах)."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute("DELETE FROM parts WHERE id = ?", (part_id,))
        if should_close:
            c.commit()
        return cur.rowcount > 0
    finally:
        if should_close:
            c.close()


def update_part_stock(part_id: int, quantity_delta: int, conn: sqlite3.Connection) -> None:
    """
    Змінити залишок запчастини на задану величину (+ для приходу, - для розходу).
    Викликається обов'язково в транзакції зовнішнього з'єднання.
    """
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE parts
        SET stock_quantity = stock_quantity + ?
        WHERE id = ?
        """,
        (quantity_delta, part_id),
    )
    if cur.rowcount == 0:
        raise ValueError(f"Запчастину з ID {part_id} не знайдено.")


# ==========================================
# ПОСТАЧАЛЬНИКИ ТА КЛІЄНТИ (COUNTERPARTIES)
# ==========================================

def get_suppliers(conn: Optional[sqlite3.Connection] = None) -> List[Supplier]:
    """Отримати всіх постачальників."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute("SELECT id, name, phone, email, address FROM suppliers ORDER BY name ASC")
        return [
            Supplier(
                id=r["id"],
                name=r["name"],
                phone=r["phone"],
                email=r["email"],
                address=r["address"],
            )
            for r in cur.fetchall()
        ]
    finally:
        if should_close:
            c.close()


def get_supplier_by_id(supplier_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Supplier]:
    """Отримати постачальника за ID."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute("SELECT id, name, phone, email, address FROM suppliers WHERE id = ?", (supplier_id,))
        r = cur.fetchone()
        return Supplier(id=r["id"], name=r["name"], phone=r["phone"], email=r["email"], address=r["address"]) if r else None
    finally:
        if should_close:
            c.close()


def create_supplier(supplier: Supplier, conn: Optional[sqlite3.Connection] = None) -> int:
    """Створити нового постачальника."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute(
            "INSERT INTO suppliers (name, phone, email, address) VALUES (?, ?, ?, ?)",
            (supplier.name.strip(), supplier.phone, supplier.email, supplier.address),
        )
        if should_close:
            c.commit()
        return cur.lastrowid
    finally:
        if should_close:
            c.close()


def update_supplier(supplier: Supplier, conn: Optional[sqlite3.Connection] = None) -> bool:
    """Оновити постачальника."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute(
            "UPDATE suppliers SET name = ?, phone = ?, email = ?, address = ? WHERE id = ?",
            (supplier.name.strip(), supplier.phone, supplier.email, supplier.address, supplier.id),
        )
        if should_close:
            c.commit()
        return cur.rowcount > 0
    finally:
        if should_close:
            c.close()


def delete_supplier(supplier_id: int, conn: Optional[sqlite3.Connection] = None) -> bool:
    """Видалити постачальника."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
        if should_close:
            c.commit()
        return cur.rowcount > 0
    finally:
        if should_close:
            c.close()


def get_customers(conn: Optional[sqlite3.Connection] = None) -> List[Customer]:
    """Отримати всіх покупців (клієнтів)."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute("SELECT id, name, phone, email, address FROM customers ORDER BY name ASC")
        return [
            Customer(
                id=r["id"],
                name=r["name"],
                phone=r["phone"],
                email=r["email"],
                address=r["address"],
            )
            for r in cur.fetchall()
        ]
    finally:
        if should_close:
            c.close()


def get_customer_by_id(customer_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Customer]:
    """Отримати клієнта за ID."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute("SELECT id, name, phone, email, address FROM customers WHERE id = ?", (customer_id,))
        r = cur.fetchone()
        return Customer(id=r["id"], name=r["name"], phone=r["phone"], email=r["email"], address=r["address"]) if r else None
    finally:
        if should_close:
            c.close()


def create_customer(customer: Customer, conn: Optional[sqlite3.Connection] = None) -> int:
    """Створити нового клієнта."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute(
            "INSERT INTO customers (name, phone, email, address) VALUES (?, ?, ?, ?)",
            (customer.name.strip(), customer.phone, customer.email, customer.address),
        )
        if should_close:
            c.commit()
        return cur.lastrowid
    finally:
        if should_close:
            c.close()


def update_customer(customer: Customer, conn: Optional[sqlite3.Connection] = None) -> bool:
    """Оновити дані клієнта."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute(
            "UPDATE customers SET name = ?, phone = ?, email = ?, address = ? WHERE id = ?",
            (customer.name.strip(), customer.phone, customer.email, customer.address, customer.id),
        )
        if should_close:
            c.commit()
        return cur.rowcount > 0
    finally:
        if should_close:
            c.close()


def delete_customer(customer_id: int, conn: Optional[sqlite3.Connection] = None) -> bool:
    """Видалити клієнта."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
        if should_close:
            c.commit()
        return cur.rowcount > 0
    finally:
        if should_close:
            c.close()


# ==========================================
# КОРИСТУВАЧІ (USERS)
# ==========================================

def get_users(conn: Optional[sqlite3.Connection] = None) -> List[User]:
    """Отримати всіх користувачів."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute("SELECT id, username, password_hash, salt, role, full_name, created_at FROM users ORDER BY id ASC")
        return [
            User(
                id=r["id"],
                username=r["username"],
                password_hash=r["password_hash"],
                salt=r["salt"],
                role=r["role"],
                full_name=r["full_name"],
                created_at=r["created_at"],
            )
            for r in cur.fetchall()
        ]
    finally:
        if should_close:
            c.close()


def get_user_by_id(user_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[User]:
    """Отримати користувача за ID."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute(
            "SELECT id, username, password_hash, salt, role, full_name, created_at FROM users WHERE id = ?",
            (user_id,),
        )
        r = cur.fetchone()
        if not r:
            return None
        return User(
            id=r["id"],
            username=r["username"],
            password_hash=r["password_hash"],
            salt=r["salt"],
            role=r["role"],
            full_name=r["full_name"],
            created_at=r["created_at"],
        )
    finally:
        if should_close:
            c.close()


def get_user_by_username(username: str, conn: Optional[sqlite3.Connection] = None) -> Optional[User]:
    """Отримати користувача за логіном."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute(
            "SELECT id, username, password_hash, salt, role, full_name, created_at FROM users WHERE username = ?",
            (username.strip(),),
        )
        r = cur.fetchone()
        if not r:
            return None
        return User(
            id=r["id"],
            username=r["username"],
            password_hash=r["password_hash"],
            salt=r["salt"],
            role=r["role"],
            full_name=r["full_name"],
            created_at=r["created_at"],
        )
    finally:
        if should_close:
            c.close()


def create_user(user: User, conn: Optional[sqlite3.Connection] = None) -> int:
    """Створити нового користувача."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute(
            """
            INSERT INTO users (username, password_hash, salt, role, full_name)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user.username.strip(), user.password_hash, user.salt, user.role, user.full_name.strip()),
        )
        if should_close:
            c.commit()
        return cur.lastrowid
    finally:
        if should_close:
            c.close()


def update_user(user: User, conn: Optional[sqlite3.Connection] = None) -> bool:
    """Оновити дані користувача (роль, повне ім'я, пароль якщо змінено)."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute(
            """
            UPDATE users
            SET username = ?, password_hash = ?, salt = ?, role = ?, full_name = ?
            WHERE id = ?
            """,
            (user.username.strip(), user.password_hash, user.salt, user.role, user.full_name.strip(), user.id),
        )
        if should_close:
            c.commit()
        return cur.rowcount > 0
    finally:
        if should_close:
            c.close()


def delete_user(user_id: int, conn: Optional[sqlite3.Connection] = None) -> bool:
    """Видалити користувача."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
        if should_close:
            c.commit()
        return cur.rowcount > 0
    finally:
        if should_close:
            c.close()


# ==========================================
# ДОКУМЕНТИ ТА ПОЗИЦІЇ (DOCUMENTS & ITEMS)
# ==========================================

def get_documents(
    doc_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> List[Document]:
    """Отримати список документів із назвами контрагентів та користувачів."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        query = """
            SELECT d.id, d.doc_type, d.doc_number, d.doc_date, d.counterparty_id,
                   d.user_id, d.notes, d.created_at, u.full_name AS user_name,
                   CASE
                       WHEN d.doc_type = 'incoming' THEN s.name
                       ELSE cust.name
                   END AS counterparty_name
            FROM documents d
            JOIN users u ON d.user_id = u.id
            LEFT JOIN suppliers s ON d.doc_type = 'incoming' AND d.counterparty_id = s.id
            LEFT JOIN customers cust ON d.doc_type = 'outgoing' AND d.counterparty_id = cust.id
        """
        where_clauses = []
        params = []

        if doc_type:
            where_clauses.append("d.doc_type = ?")
            params.append(doc_type)

        if date_from:
            where_clauses.append("d.doc_date >= ?")
            params.append(date_from)

        if date_to:
            where_clauses.append("d.doc_date <= ?")
            params.append(date_to)

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        query += " ORDER BY d.doc_date DESC, d.id DESC"

        cur.execute(query, params)
        rows = cur.fetchall()

        documents = []
        for r in rows:
            doc = Document(
                id=r["id"],
                doc_type=r["doc_type"],
                doc_number=r["doc_number"],
                doc_date=r["doc_date"],
                counterparty_id=r["counterparty_id"],
                user_id=r["user_id"],
                notes=r["notes"],
                created_at=r["created_at"],
                counterparty_name=r["counterparty_name"] or "Невідомий",
                user_name=r["user_name"],
            )
            documents.append(doc)
        return documents
    finally:
        if should_close:
            c.close()


def get_document_items(document_id: int, conn: Optional[sqlite3.Connection] = None) -> List[DocumentItem]:
    """Отримати всі позиції документу з назвами та артикулами запчастин."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute(
            """
            SELECT di.id, di.document_id, di.part_id, di.quantity, di.price,
                   p.part_number, p.name AS part_name, p.unit
            FROM document_items di
            JOIN parts p ON di.part_id = p.id
            WHERE di.document_id = ?
            ORDER BY di.id ASC
            """,
            (document_id,),
        )
        return [
            DocumentItem(
                id=r["id"],
                document_id=r["document_id"],
                part_id=r["part_id"],
                quantity=r["quantity"],
                price=r["price"],
                part_number=r["part_number"],
                part_name=r["part_name"],
                unit=r["unit"],
            )
            for r in cur.fetchall()
        ]
    finally:
        if should_close:
            c.close()


def get_document_by_id(doc_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Document]:
    """Отримати документ за ID разом із позиціями."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        cur = c.cursor()
        cur.execute(
            """
            SELECT d.id, d.doc_type, d.doc_number, d.doc_date, d.counterparty_id,
                   d.user_id, d.notes, d.created_at, u.full_name AS user_name,
                   CASE
                       WHEN d.doc_type = 'incoming' THEN s.name
                       ELSE cust.name
                   END AS counterparty_name
            FROM documents d
            JOIN users u ON d.user_id = u.id
            LEFT JOIN suppliers s ON d.doc_type = 'incoming' AND d.counterparty_id = s.id
            LEFT JOIN customers cust ON d.doc_type = 'outgoing' AND d.counterparty_id = cust.id
            WHERE d.id = ?
            """,
            (doc_id,),
        )
        r = cur.fetchone()
        if not r:
            return None

        items = get_document_items(doc_id, conn=c)
        return Document(
            id=r["id"],
            doc_type=r["doc_type"],
            doc_number=r["doc_number"],
            doc_date=r["doc_date"],
            counterparty_id=r["counterparty_id"],
            user_id=r["user_id"],
            notes=r["notes"],
            created_at=r["created_at"],
            counterparty_name=r["counterparty_name"] or "Невідомий",
            user_name=r["user_name"],
            items=items,
        )
    finally:
        if should_close:
            c.close()
