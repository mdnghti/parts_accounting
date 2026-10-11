from pathlib import Path
import sqlite3
import pytest

from db.repositories import (
    create_category,
    create_customer,
    create_part,
    create_supplier,
    delete_category,
    delete_part,
    get_part_by_id,
    get_parts,
)
from models import Category, Customer, Document, DocumentItem, Part, Supplier
from services.auth_service import register_user, verify_password
from services.inventory_service import (
    InsufficientStockError,
    process_incoming_document,
    process_outgoing_document,
)


@pytest.fixture
def clean_db(tmp_path: Path):
    """Створення чистої БД з активними foreign keys."""
    db_file = tmp_path / "edge_test.db"
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    schema_file = Path(__file__).resolve().parent.parent / "db" / "schema.sql"
    with open(schema_file, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    yield conn
    conn.close()


def test_multi_item_outgoing_atomic_rollback(clean_db):
    """
    Граничний випадок: багатопозиційна видаткова накладна.
    Позиція 1 має достатній залишок (є 10, списуємо 2).
    Позиція 2 НЕ має достатнього залишку (є 3, списуємо 5).
    Перевірка: транзакція відкочується повністю, залишок товару 1 НЕ зменшується!
    """
    user = register_user("admin_edge", "admin123", "admin", "Адмін", conn=clean_db)
    cat_id = create_category(Category(id=None, name="Тест Категорія"), conn=clean_db)
    cust_id = create_customer(Customer(id=None, name="Клієнт"), conn=clean_db)

    p1_id = create_part(
        Part(id=None, part_number="P1", name="Товар 1", category_id=cat_id, price=100.0, stock_quantity=10, min_stock_quantity=2),
        conn=clean_db,
    )
    p2_id = create_part(
        Part(id=None, part_number="P2", name="Товар 2", category_id=cat_id, price=200.0, stock_quantity=3, min_stock_quantity=1),
        conn=clean_db,
    )
    clean_db.commit()

    doc = Document(
        id=None,
        doc_type="outgoing",
        doc_number="ВР-EDGE-01",
        doc_date="2026-10-11 12:00:00",
        counterparty_id=cust_id,
        user_id=user.id,
        items=[
            DocumentItem(id=None, document_id=None, part_id=p1_id, quantity=2, price=100.0),  # Списання можливе
            DocumentItem(id=None, document_id=None, part_id=p2_id, quantity=5, price=200.0),  # Помилка! Недостатньо
        ],
    )

    with pytest.raises(InsufficientStockError) as exc_info:
        process_outgoing_document(doc, conn=clean_db)

    assert "Товар 2" in str(exc_info.value)
    assert "арт. P2" in str(exc_info.value)

    # Перевірка: залишок першого товару НЕ змінився (залишився 10, а не 8)
    p1_after = get_part_by_id(p1_id, conn=clean_db)
    p2_after = get_part_by_id(p2_id, conn=clean_db)
    assert p1_after.stock_quantity == 10
    assert p2_after.stock_quantity == 3

    # Документ не створений
    cur = clean_db.cursor()
    cur.execute("SELECT COUNT(*) FROM documents WHERE doc_number = 'ВР-EDGE-01'")
    assert cur.fetchone()[0] == 0


def test_zero_stock_boundary(clean_db):
    """
    Граничний випадок: списання до рівно 0 дозволене.
    Наступне списання навіть 1 шт заборонене.
    """
    user = register_user("admin_zero", "admin123", "admin", "Адмін", conn=clean_db)
    cat_id = create_category(Category(id=None, name="Категорія 0"), conn=clean_db)
    cust_id = create_customer(Customer(id=None, name="Клієнт 0"), conn=clean_db)

    p_id = create_part(
        Part(id=None, part_number="P-ZERO", name="Товар Останній", category_id=cat_id, price=50.0, stock_quantity=1, min_stock_quantity=0),
        conn=clean_db,
    )
    clean_db.commit()

    # Списання в 0
    doc1 = Document(
        id=None,
        doc_type="outgoing",
        doc_number="ВР-ZERO-1",
        doc_date="2026-10-11",
        counterparty_id=cust_id,
        user_id=user.id,
        items=[DocumentItem(id=None, document_id=None, part_id=p_id, quantity=1, price=50.0)],
    )
    process_outgoing_document(doc1, conn=clean_db)

    p_after = get_part_by_id(p_id, conn=clean_db)
    assert p_after.stock_quantity == 0

    # Спроба списати з 0
    doc2 = Document(
        id=None,
        doc_type="outgoing",
        doc_number="ВР-ZERO-2",
        doc_date="2026-10-11",
        counterparty_id=cust_id,
        user_id=user.id,
        items=[DocumentItem(id=None, document_id=None, part_id=p_id, quantity=1, price=50.0)],
    )
    with pytest.raises(InsufficientStockError):
        process_outgoing_document(doc2, conn=clean_db)


def test_foreign_key_restrict_category_deletion(clean_db):
    """
    Цілісність БД: видалення категорії, до якої прив'язані запчастини,
    блокується базою даних (RESTRICT foreign key).
    """
    cat_id = create_category(Category(id=None, name="Категорія захищена"), conn=clean_db)
    create_part(
        Part(id=None, part_number="P-FK", name="Запчастина прив'язана", category_id=cat_id, price=10.0),
        conn=clean_db,
    )
    clean_db.commit()

    with pytest.raises(sqlite3.IntegrityError):
        delete_category(cat_id, conn=clean_db)


def test_foreign_key_restrict_part_deletion_with_documents(clean_db):
    """
    Цілісність БД: видалення запчастини, яка фігурує в накладній,
    блокується (RESTRICT foreign key).
    """
    user = register_user("admin_fk", "admin123", "admin", "Адмін", conn=clean_db)
    cat_id = create_category(Category(id=None, name="Категорія"), conn=clean_db)
    sup_id = create_supplier(Supplier(id=None, name="Постачальник"), conn=clean_db)
    p_id = create_part(
        Part(id=None, part_number="P-DOC", name="Запчастина в накладній", category_id=cat_id, price=10.0),
        conn=clean_db,
    )
    clean_db.commit()

    doc = Document(
        id=None,
        doc_type="incoming",
        doc_number="ПР-FK-1",
        doc_date="2026-10-11",
        counterparty_id=sup_id,
        user_id=user.id,
        items=[DocumentItem(id=None, document_id=None, part_id=p_id, quantity=5, price=10.0)],
    )
    process_incoming_document(doc, conn=clean_db)

    with pytest.raises(sqlite3.IntegrityError):
        delete_part(p_id, conn=clean_db)


def test_unique_part_number_constraint(clean_db):
    """Унікальність артикулу в базі."""
    cat_id = create_category(Category(id=None, name="Кат"), conn=clean_db)
    p1 = Part(id=None, part_number="UNIQUE-123", name="Перша", category_id=cat_id, price=10.0)
    create_part(p1, conn=clean_db)
    clean_db.commit()

    p2 = Part(id=None, part_number="UNIQUE-123", name="Дублікат", category_id=cat_id, price=20.0)
    with pytest.raises(sqlite3.IntegrityError):
        create_part(p2, conn=clean_db)


def test_search_cyrillic_case_insensitivity(clean_db):
    """Пошук запчастин за кирилицею."""
    cat_id = create_category(Category(id=None, name="Підвіска"), conn=clean_db)
    create_part(
        Part(id=None, part_number="SA-UA-1", name="Важіль передньої підвіски", category_id=cat_id, price=500.0),
        conn=clean_db,
    )
    clean_db.commit()

    # Пошук за словом "важіль"
    found1 = get_parts(search="важіль", conn=clean_db)
    assert len(found1) == 1
    assert found1[0].part_number == "SA-UA-1"

    # Пошук за частиною слова "підвіски"
    found2 = get_parts(search="підвіски", conn=clean_db)
    assert len(found2) == 1


def test_corrupted_auth_hash(clean_db):
    """Перевірка стійкості перевірки паролів при пошкодженому хеші чи солі."""
    try:
        res = verify_password("test", "corrupted_hash", "invalid_salt_not_hex")
        assert res is False
    except ValueError:
        pass
