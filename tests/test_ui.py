import os
import sys
import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

# Встановлюємо платформу offscreen для тестів без графічного дисплея
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from models import Part, Document, User
from ui.models import PartsTableModel, DocumentsTableModel
from ui.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp():
    """Фікстура для єдиного екземпляра QApplication на сесію."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def test_parts_table_model(qapp):
    normal_part = Part(
        id=1,
        part_number="OF-1001",
        name="Фільтр звичайний",
        category_id=1,
        price=200.0,
        stock_quantity=10,
        min_stock_quantity=2,
        unit="шт.",
        category_name="Фільтри",
    )
    low_stock_part = Part(
        id=2,
        part_number="BP-2001",
        name="Колодки дефіцитні",
        category_id=2,
        price=500.0,
        stock_quantity=1,
        min_stock_quantity=3,
        unit="компл.",
        category_name="Гальма",
    )

    model = PartsTableModel([normal_part, low_stock_part])
    assert model.rowCount() == 2
    assert model.columnCount() == 8

    # Перевірка назв колонок
    assert model.headerData(1, Qt.Orientation.Horizontal) == "Артикул"
    assert model.headerData(2, Qt.Orientation.Horizontal) == "Назва запчастини"

    # Перевірка даних нормальної запчастини (рядок 0)
    idx_norm_art = model.index(0, 1)
    assert model.data(idx_norm_art, Qt.ItemDataRole.DisplayRole) == "OF-1001"
    assert model.data(idx_norm_art, Qt.ItemDataRole.BackgroundRole) is None

    # Перевірка підсвічування дефіцитної запчастини (рядок 1)
    idx_low_art = model.index(1, 1)
    bg_color = model.data(idx_low_art, Qt.ItemDataRole.BackgroundRole)
    assert isinstance(bg_color, QColor)
    assert bg_color.red() == 255  # М'який червоний фон


def test_documents_table_model(qapp):
    doc1 = Document(
        id=1,
        doc_type="incoming",
        doc_number="ПР-2026-0001",
        doc_date="2026-10-11 10:00:00",
        counterparty_id=1,
        user_id=1,
        counterparty_name="Постачальник 1",
        user_name="Адміністратор",
    )
    doc2 = Document(
        id=2,
        doc_type="outgoing",
        doc_number="ВР-2026-0001",
        doc_date="2026-10-11 11:00:00",
        counterparty_id=2,
        user_id=2,
        counterparty_name="Клієнт 1",
        user_name="Комірник",
    )

    model = DocumentsTableModel([doc1, doc2])
    assert model.rowCount() == 2

    idx_doc1_type = model.index(0, 1)
    assert model.data(idx_doc1_type, Qt.ItemDataRole.DisplayRole) == "Прибуткова накладна"
    fg_incoming = model.data(idx_doc1_type, Qt.ItemDataRole.ForegroundRole)
    assert isinstance(fg_incoming, QColor)

    idx_doc2_type = model.index(1, 1)
    assert model.data(idx_doc2_type, Qt.ItemDataRole.DisplayRole) == "Видаткова накладна"


def test_main_window_role_permissions(qapp):
    admin_user = User(
        id=1,
        username="admin",
        password_hash="hash",
        salt="salt",
        role="admin",
        full_name="Адмін",
    )
    keeper_user = User(
        id=2,
        username="keeper",
        password_hash="hash",
        salt="salt",
        role="storekeeper",
        full_name="Комірник",
    )

    # Адміністратор має активні кнопки видалення
    win_admin = MainWindow(admin_user)
    assert win_admin.del_part_btn.isEnabled() is True
    assert win_admin.del_cat_btn.isEnabled() is True
    win_admin.deleteLater()
    qapp.processEvents()

    # Комірник має вимкнені кнопки видалення
    win_keeper = MainWindow(keeper_user)
    assert win_keeper.del_part_btn.isEnabled() is False
    assert win_keeper.del_cat_btn.isEnabled() is False
    assert win_keeper.del_brand_btn.isEnabled() is False
    assert win_keeper.del_sup_btn.isEnabled() is False
    assert win_keeper.del_cust_btn.isEnabled() is False
    win_keeper.deleteLater()
    qapp.processEvents()
