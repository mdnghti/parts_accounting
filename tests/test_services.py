import sqlite3
from pathlib import Path
import pytest

from db.repositories import (
    create_category, create_customer, create_part, create_supplier,
    get_document_by_id, get_part_by_id,
)
from models import Category, Customer, Document, DocumentItem, Part, Supplier, User
from services.auth_service import (
    authenticate_user, change_password, register_user, verify_password,
)
from services.inventory_service import (
    DocumentValidationError, InsufficientStockError, generate_doc_number,
    process_incoming_document, process_outgoing_document,
)


@pytest.fixture
def db_conn(tmp_path: Path):
    """Створення чистої БД для тестів сервісів."""
    db_file = tmp_path / "test_services.db"
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    schema_file = Path(__file__).resolve().parent.parent / "db" / "schema.sql"
    with open(schema_file, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    yield conn
    conn.close()


def test_auth_service(db_conn):
    # Реєстрація нового користувача
    user = register_user("ivan", "pass1234", "storekeeper", "Іван Петренко", conn=db_conn)
    assert user.id is not None
    assert user.username == "ivan"

    # Невірний пароль при реєстрації (короткий)
    with pytest.raises(ValueError, match="щонайменше 4 символи"):
        register_user("petro", "123", "admin", "Петро", conn=db_conn)

    # Неприпустима роль
    with pytest.raises(ValueError, match="Неприпустима роль"):
        register_user("olena", "pass1234", "guest", "Олена", conn=db_conn)

    # Успішна аутентифікація
    auth_user = authenticate_user("ivan", "pass1234", conn=db_conn)
    assert auth_user is not None
    assert auth_user.full_name == "Іван Петренко"

    # Помилкова аутентифікація
    assert authenticate_user("ivan", "wrongpass", conn=db_conn) is None
    assert authenticate_user("nonexistent", "pass1234", conn=db_conn) is None

    # Зміна пароля
    assert change_password(user.id, "wrong_old", "newpass123", conn=db_conn) is False
    assert change_password(user.id, "pass1234", "newpass123", conn=db_conn) is True
    assert authenticate_user("ivan", "newpass123", conn=db_conn) is not None


def test_inventory_incoming_process(db_conn):
    # Підготовка даних
    user = register_user("admin_test", "admin123", "admin", "Адмін", conn=db_conn)
    cat_id = create_category(Category(id=None, name="Фільтри"), conn=db_conn)
    sup_id = create_supplier(Supplier(id=None, name="АвтоПостач"), conn=db_conn)

    part = Part(
        id=None,
        part_number="OF-TEST-1",
        name="Тестовий масляний фільтр",
        category_id=cat_id,
        price=300.0,
        stock_quantity=5,
        min_stock_quantity=2,
    )
    p_id = create_part(part, conn=db_conn)

    doc_num = generate_doc_number("incoming", conn=db_conn)
    assert doc_num.startswith("ПР-")

    doc = Document(
        id=None,
        doc_type="incoming",
        doc_number=doc_num,
        doc_date="2026-10-11 12:00:00",
        counterparty_id=sup_id,
        user_id=user.id,
        items=[
            DocumentItem(id=None, document_id=None, part_id=p_id, quantity=10, price=250.0),
        ],
    )

    doc_id = process_incoming_document(doc, conn=db_conn)
    assert doc_id > 0

    # Перевірка збільшення залишків (5 + 10 = 15)
    updated_part = get_part_by_id(p_id, conn=db_conn)
    assert updated_part.stock_quantity == 15

    # Перевірка збереження документа та рядків
    saved_doc = get_document_by_id(doc_id, conn=db_conn)
    assert saved_doc is not None
    assert len(saved_doc.items) == 1
    assert saved_doc.items[0].quantity == 10
    assert saved_doc.total_amount == 2500.0


def test_inventory_outgoing_process(db_conn):
    user = register_user("admin_test2", "admin123", "admin", "Адмін", conn=db_conn)
    cat_id = create_category(Category(id=None, name="Гальма"), conn=db_conn)
    cust_id = create_customer(Customer(id=None, name="АвтоМайстерня"), conn=db_conn)

    p_id = create_part(
        Part(
            id=None,
            part_number="BRK-TEST-1",
            name="Тестовий гальмівний диск",
            category_id=cat_id,
            price=1200.0,
            stock_quantity=8,
            min_stock_quantity=2,
        ),
        conn=db_conn,
    )

    doc_num = generate_doc_number("outgoing", conn=db_conn)
    assert doc_num.startswith("ВР-")

    doc = Document(
        id=None,
        doc_type="outgoing",
        doc_number=doc_num,
        doc_date="2026-10-11 14:00:00",
        counterparty_id=cust_id,
        user_id=user.id,
        items=[
            DocumentItem(id=None, document_id=None, part_id=p_id, quantity=3, price=1200.0),
        ],
    )

    doc_id = process_outgoing_document(doc, conn=db_conn)
    assert doc_id > 0

    # Перевірка зменшення залишків (8 - 3 = 5)
    updated_part = get_part_by_id(p_id, conn=db_conn)
    assert updated_part.stock_quantity == 5


def test_inventory_outgoing_insufficient_stock_rollback(db_conn):
    user = register_user("admin_test3", "admin123", "admin", "Адмін", conn=db_conn)
    cat_id = create_category(Category(id=None, name="Підвіска"), conn=db_conn)
    cust_id = create_customer(Customer(id=None, name="Клієнт 2"), conn=db_conn)

    p_id = create_part(
        Part(
            id=None,
            part_number="SA-TEST-1",
            name="Амортизатор тестовий",
            category_id=cat_id,
            price=2000.0,
            stock_quantity=3,  # всього 3 шт
            min_stock_quantity=1,
        ),
        conn=db_conn,
    )
    db_conn.commit()

    # Спроба списати 5 шт при залишку 3 шт
    doc = Document(
        id=None,
        doc_type="outgoing",
        doc_number="ВР-ERR-001",
        doc_date="2026-10-11 15:00:00",
        counterparty_id=cust_id,
        user_id=user.id,
        items=[
            DocumentItem(id=None, document_id=None, part_id=p_id, quantity=5, price=2000.0),
        ],
    )

    with pytest.raises(InsufficientStockError, match="Недостатньо товару на складі"):
        process_outgoing_document(doc, conn=db_conn)

    # Перевірка відкату транзакції: залишок має залишитися 3
    part_after = get_part_by_id(p_id, conn=db_conn)
    assert part_after.stock_quantity == 3

    # Документ не повинен бути створений в базі
    cur = db_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM documents WHERE doc_number = 'ВР-ERR-001'")
    assert cur.fetchone()[0] == 0


def test_inventory_validation_errors(db_conn):
    user = register_user("admin_test4", "admin123", "admin", "Адмін", conn=db_conn)
    sup_id = create_supplier(Supplier(id=None, name="Постачальник Тest"), conn=db_conn)

    # Порожній документ
    doc = Document(
        id=None,
        doc_type="incoming",
        doc_number="ПР-EMPTY-1",
        doc_date="2026-10-11",
        counterparty_id=sup_id,
        user_id=user.id,
        items=[],
    )
    with pytest.raises(DocumentValidationError, match="не може бути порожньою"):
        process_incoming_document(doc, conn=db_conn)

    # Неіснуючий постачальник
    doc.items = [DocumentItem(id=None, document_id=None, part_id=1, quantity=1, price=100.0)]
    doc.counterparty_id = 99999
    with pytest.raises(DocumentValidationError, match="не знайдено"):
        process_incoming_document(doc, conn=db_conn)
