import sqlite3
import pytest
from pathlib import Path

from db.repositories import (
    create_category, get_categories, get_category_by_id, update_category, delete_category,
    create_brand, get_brands, get_brand_by_id, update_brand, delete_brand,
    create_model, get_models, get_model_by_id, update_model, delete_model,
    create_part, get_parts, get_part_by_id, get_part_by_number, update_part, delete_part, update_part_stock,
    create_supplier, get_suppliers, get_supplier_by_id, update_supplier, delete_supplier,
    create_customer, get_customers, get_customer_by_id, update_customer, delete_customer,
    create_user, get_users, get_user_by_id, get_user_by_username, update_user, delete_user,
)
from models import Category, CarBrand, CarModel, Part, Supplier, Customer, User


@pytest.fixture
def db_conn(tmp_path: Path):
    """Створення чистої тестової БД з актуальною схемою."""
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    schema_file = Path(__file__).resolve().parent.parent / "db" / "schema.sql"
    with open(schema_file, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    yield conn
    conn.close()


def test_category_crud(db_conn):
    cat = Category(id=None, name="Тестова категорія", description="Опис")
    cat_id = create_category(cat, conn=db_conn)
    assert cat_id > 0

    fetched = get_category_by_id(cat_id, conn=db_conn)
    assert fetched is not None
    assert fetched.name == "Тестова категорія"

    fetched.name = "Оновлена назва"
    assert update_category(fetched, conn=db_conn) is True

    updated = get_category_by_id(cat_id, conn=db_conn)
    assert updated.name == "Оновлена назва"

    all_cats = get_categories(conn=db_conn)
    assert len(all_cats) == 1

    assert delete_category(cat_id, conn=db_conn) is True
    assert get_category_by_id(cat_id, conn=db_conn) is None


def test_car_brand_and_model_crud(db_conn):
    brand = CarBrand(id=None, name="Audi")
    b_id = create_brand(brand, conn=db_conn)
    assert b_id > 0

    model = CarModel(id=None, brand_id=b_id, name="A4", year_from=2015, year_to=2020)
    m_id = create_model(model, conn=db_conn)
    assert m_id > 0

    fetched_m = get_model_by_id(m_id, conn=db_conn)
    assert fetched_m is not None
    assert fetched_m.brand_name == "Audi"
    assert fetched_m.name == "A4"
    assert "Audi A4 (2015-2020)" in fetched_m.display_name

    models = get_models(brand_id=b_id, conn=db_conn)
    assert len(models) == 1

    # CASCADE видалення моделі при видаленні бренду
    delete_brand(b_id, conn=db_conn)
    assert get_model_by_id(m_id, conn=db_conn) is None


def test_part_crud_and_stock(db_conn):
    cat_id = create_category(Category(id=None, name="Гальма"), conn=db_conn)
    b_id = create_brand(CarBrand(id=None, name="BMW"), conn=db_conn)
    m_id = create_model(CarModel(id=None, brand_id=b_id, name="X5"), conn=db_conn)

    part = Part(
        id=None,
        part_number="BRK-001",
        name="Гальмівні колодки",
        category_id=cat_id,
        price=1500.0,
        stock_quantity=10,
        min_stock_quantity=5,
        unit="компл.",
        compatible_model_ids=[m_id],
    )
    p_id = create_part(part, conn=db_conn)
    assert p_id > 0

    fetched = get_part_by_id(p_id, conn=db_conn)
    assert fetched is not None
    assert fetched.part_number == "BRK-001"
    assert m_id in fetched.compatible_model_ids
    assert fetched.is_low_stock is False

    # Фільтрація за брендом та пошуком
    found = get_parts(search="колодки", brand_id=b_id, conn=db_conn)
    assert len(found) == 1

    # Зміна залишку
    update_part_stock(p_id, -6, conn=db_conn)
    p_after = get_part_by_id(p_id, conn=db_conn)
    assert p_after.stock_quantity == 4
    assert p_after.is_low_stock is True

    # Фільтр за низьким залишком
    low_stock = get_parts(low_stock_only=True, conn=db_conn)
    assert len(low_stock) == 1


def test_counterparty_crud(db_conn):
    sup = Supplier(id=None, name="Постачальник 1", phone="123", email="sup@test.ua", address="Київ")
    s_id = create_supplier(sup, conn=db_conn)
    assert s_id > 0
    assert get_supplier_by_id(s_id, conn=db_conn).name == "Постачальник 1"

    cust = Customer(id=None, name="Клієнт 1", phone="456", email="cust@test.ua", address="Львів")
    c_id = create_customer(cust, conn=db_conn)
    assert c_id > 0
    assert get_customer_by_id(c_id, conn=db_conn).name == "Клієнт 1"


def test_user_crud(db_conn):
    u = User(id=None, username="manager", password_hash="hash123", salt="salt123", role="storekeeper", full_name="Менеджер")
    u_id = create_user(u, conn=db_conn)
    assert u_id > 0

    fetched = get_user_by_username("manager", conn=db_conn)
    assert fetched is not None
    assert fetched.full_name == "Менеджер"
    assert fetched.is_admin is False
