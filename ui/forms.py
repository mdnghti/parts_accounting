from datetime import datetime
from typing import List, Optional
from PySide6.QtCore import QDateTime, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableView,
    QTextEdit,
    QVBoxLayout,
)

from db.repositories import (
    get_brands,
    get_categories,
    get_customers,
    get_models,
    get_parts,
    get_suppliers,
)
from models.car import CarBrand, CarModel
from models.category import Category
from models.counterparty import Customer, Supplier
from models.document import Document, DocumentItem
from models.part import Part
from models.user import User
from services.inventory_service import (
    DocumentValidationError,
    InsufficientStockError,
    generate_doc_number,
    process_incoming_document,
    process_outgoing_document,
)
from ui.models import DocumentItemsTableModel


# ==========================================
# ДІАЛОГ ЗАПЧАСТИНИ (PART DIALOG)
# ==========================================

class PartDialog(QDialog):
    """Форма додавання або редагування запчастини."""

    def __init__(self, parent=None, part: Optional[Part] = None):
        super().__init__(parent)
        self.part = part
        self.setWindowTitle("Редагування запчастини" if part else "Додавання запчастини")
        self.setFixedSize(480, 560)
        self._init_ui()
        if self.part:
            self._load_data()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.part_number_input = QLineEdit()
        self.part_number_input.setPlaceholderText("напр. OF-1001")

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("напр. Фільтр масляний Mann W67/2")

        self.category_cb = QComboBox()
        self.categories = get_categories()
        for cat in self.categories:
            self.category_cb.addItem(cat.name, cat.id)

        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0.0, 1_000_000.0)
        self.price_input.setDecimals(2)
        self.price_input.setSuffix(" грн")

        self.stock_input = QSpinBox()
        self.stock_input.setRange(0, 100_000)

        self.min_stock_input = QSpinBox()
        self.min_stock_input.setRange(0, 100_000)

        self.unit_input = QLineEdit()
        self.unit_input.setText("шт.")

        form.addRow("Артикул:*", self.part_number_input)
        form.addRow("Назва запчастини:*", self.name_input)
        form.addRow("Категорія:*", self.category_cb)
        form.addRow("Ціна продажу:*", self.price_input)
        form.addRow("Поточний залишок:", self.stock_input)
        form.addRow("Мінімальний залишок:", self.min_stock_input)
        form.addRow("Одиниця виміру:", self.unit_input)

        layout.addLayout(form)

        # Список сумісних моделей авто (чекбокси)
        layout.addWidget(QLabel("Сумісність з моделями автомобілів:"))
        self.models_list = QListWidget()
        self.models = get_models()
        for m in self.models:
            item = QListWidgetItem(m.display_name)
            item.setData(Qt.ItemDataRole.UserRole, m.id)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.models_list.addItem(item)
        layout.addWidget(self.models_list)

        # Кнопки
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Зберегти")
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self._save)

        self.cancel_btn = QPushButton("Скасувати")
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def _load_data(self) -> None:
        if not self.part:
            return
        self.part_number_input.setText(self.part.part_number)
        self.name_input.setText(self.part.name)

        idx = self.category_cb.findData(self.part.category_id)
        if idx >= 0:
            self.category_cb.setCurrentIndex(idx)

        self.price_input.setValue(self.part.price)
        self.stock_input.setValue(self.part.stock_quantity)
        self.min_stock_input.setValue(self.part.min_stock_quantity)
        self.unit_input.setText(self.part.unit)

        # Відмічаємо сумісні моделі
        compat_ids = set(self.part.compatible_model_ids)
        for i in range(self.models_list.count()):
            item = self.models_list.item(i)
            m_id = item.data(Qt.ItemDataRole.UserRole)
            if m_id in compat_ids:
                item.setCheckState(Qt.CheckState.Checked)

    def _save(self) -> None:
        part_num = self.part_number_input.text().strip()
        name = self.name_input.text().strip()

        if not part_num:
            QMessageBox.warning(self, "Помилка валідації", "Артикул не може бути порожнім.")
            return
        if not name:
            QMessageBox.warning(self, "Помилка валідації", "Назва запчастини є обов'язковою.")
            return

        cat_id = self.category_cb.currentData()
        if cat_id is None:
            QMessageBox.warning(self, "Помилка валідації", "Оберіть категорію.")
            return

        # Збираємо вибрані моделі
        selected_model_ids = []
        for i in range(self.models_list.count()):
            item = self.models_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_model_ids.append(item.data(Qt.ItemDataRole.UserRole))

        self.result_part = Part(
            id=self.part.id if self.part else None,
            part_number=part_num,
            name=name,
            category_id=cat_id,
            price=self.price_input.value(),
            stock_quantity=self.stock_input.value(),
            min_stock_quantity=self.min_stock_input.value(),
            unit=self.unit_input.text().strip() or "шт.",
            compatible_model_ids=selected_model_ids,
        )
        self.accept()


# ==========================================
# ДІАЛОГИ ДОВІДНИКІВ
# ==========================================

class CategoryDialog(QDialog):
    """Форма додавання/редагування категорії."""

    def __init__(self, parent=None, category: Optional[Category] = None):
        super().__init__(parent)
        self.category = category
        self.setWindowTitle("Редагування категорії" if category else "Нова категорія")
        self.setFixedSize(380, 240)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit()
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(80)

        if self.category:
            self.name_input.setText(self.category.name)
            self.desc_input.setPlainText(self.category.description or "")

        form.addRow("Назва категорії:*", self.name_input)
        form.addRow("Опис:", self.desc_input)
        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Зберегти")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Скасувати")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _save(self) -> None:
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Помилка", "Назва категорії є обов'язковою.")
            return

        self.result_category = Category(
            id=self.category.id if self.category else None,
            name=name,
            description=self.desc_input.toPlainText().strip() or None,
        )
        self.accept()


class BrandDialog(QDialog):
    """Форма додавання/редагування марки авто."""

    def __init__(self, parent=None, brand: Optional[CarBrand] = None):
        super().__init__(parent)
        self.brand = brand
        self.setWindowTitle("Редагування марки" if brand else "Нова марка авто")
        self.setFixedSize(340, 160)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit()
        if self.brand:
            self.name_input.setText(self.brand.name)

        form.addRow("Марка автомобіля:*", self.name_input)
        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Зберегти")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Скасувати")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _save(self) -> None:
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Помилка", "Введіть назву марки авто.")
            return

        self.result_brand = CarBrand(
            id=self.brand.id if self.brand else None,
            name=name,
        )
        self.accept()


class ModelDialog(QDialog):
    """Форма додавання/редагування моделі авто."""

    def __init__(self, parent=None, model: Optional[CarModel] = None):
        super().__init__(parent)
        self.model = model
        self.setWindowTitle("Редагування моделі" if model else "Нова модель авто")
        self.setFixedSize(380, 240)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.brand_cb = QComboBox()
        self.brands = get_brands()
        for b in self.brands:
            self.brand_cb.addItem(b.name, b.id)

        self.name_input = QLineEdit()

        self.year_from_input = QSpinBox()
        self.year_from_input.setRange(1950, 2030)
        self.year_from_input.setSpecialValueText("—")
        self.year_from_input.setValue(1950)

        self.year_to_input = QSpinBox()
        self.year_to_input.setRange(1950, 2030)
        self.year_to_input.setSpecialValueText("—")
        self.year_to_input.setValue(1950)

        if self.model:
            idx = self.brand_cb.findData(self.model.brand_id)
            if idx >= 0:
                self.brand_cb.setCurrentIndex(idx)
            self.name_input.setText(self.model.name)
            if self.model.year_from:
                self.year_from_input.setValue(self.model.year_from)
            if self.model.year_to:
                self.year_to_input.setValue(self.model.year_to)

        form.addRow("Марка авто:*", self.brand_cb)
        form.addRow("Назва моделі:*", self.name_input)
        form.addRow("Рік випуску з:", self.year_from_input)
        form.addRow("Рік випуску по:", self.year_to_input)
        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Зберегти")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Скасувати")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _save(self) -> None:
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Помилка", "Введіть назву моделі авто.")
            return

        brand_id = self.brand_cb.currentData()
        y_from = self.year_from_input.value() if self.year_from_input.value() > 1950 else None
        y_to = self.year_to_input.value() if self.year_to_input.value() > 1950 else None

        self.result_model = CarModel(
            id=self.model.id if self.model else None,
            brand_id=brand_id,
            name=name,
            year_from=y_from,
            year_to=y_to,
        )
        self.accept()


class CounterpartyDialog(QDialog):
    """Форма додавання/редагування контрагента (постачальника чи клієнта)."""

    def __init__(self, parent=None, title: str = "Постачальник", entity: Optional[Any] = None):
        super().__init__(parent)
        self.entity = entity
        self.setWindowTitle(f"Редагування: {title}" if entity else f"Новий {title}")
        self.setFixedSize(380, 240)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+380...")
        self.email_input = QLineEdit()
        self.address_input = QLineEdit()

        if self.entity:
            self.name_input.setText(self.entity.name)
            self.phone_input.setText(self.entity.phone or "")
            self.email_input.setText(self.entity.email or "")
            self.address_input.setText(self.entity.address or "")

        form.addRow("Назва / ПІБ:*", self.name_input)
        form.addRow("Телефон:", self.phone_input)
        form.addRow("Email:", self.email_input)
        form.addRow("Адреса:", self.address_input)
        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Зберегти")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Скасувати")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _save(self) -> None:
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Помилка", "Назва або ПІБ є обов'язковим полем.")
            return

        self.result_data = {
            "name": name,
            "phone": self.phone_input.text().strip() or None,
            "email": self.email_input.text().strip() or None,
            "address": self.address_input.text().strip() or None,
        }
        self.accept()


# ==========================================
# ДІАЛОГ ОФОРМЛЕННЯ НАКЛАДНОЇ (DOCUMENT CREATE)
# ==========================================

class AddDocumentItemDialog(QDialog):
    """Піддіалог вибору запчастини, кількості та ціни для накладної."""

    def __init__(self, parent=None, is_outgoing: bool = False):
        super().__init__(parent)
        self.is_outgoing = is_outgoing
        self.setWindowTitle("Додати позицію до накладної")
        self.setFixedSize(420, 240)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.part_cb = QComboBox()
        self.parts = get_parts()
        for p in self.parts:
            stock_info = f" [залишок: {p.stock_quantity} {p.unit}]"
            self.part_cb.addItem(f"{p.part_number} — {p.name}{stock_info}", p)

        self.part_cb.currentIndexChanged.connect(self._on_part_changed)

        self.qty_input = QSpinBox()
        self.qty_input.setRange(1, 100_000)
        self.qty_input.setValue(1)

        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0.0, 1_000_000.0)
        self.price_input.setDecimals(2)
        self.price_input.setSuffix(" грн")

        form.addRow("Запчастина:*", self.part_cb)
        form.addRow("Кількість:*", self.qty_input)
        form.addRow("Ціна за одиницю:*", self.price_input)
        layout.addLayout(form)

        if self.parts:
            self._on_part_changed(0)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Додати позицію")
        add_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Скасувати")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _on_part_changed(self, index: int) -> None:
        part: Optional[Part] = self.part_cb.currentData()
        if part:
            self.price_input.setValue(part.price)
            if self.is_outgoing:
                # Обмежуємо максимум поточним залишком для зручності
                self.qty_input.setMaximum(max(1, part.stock_quantity))

    def _save(self) -> None:
        part: Optional[Part] = self.part_cb.currentData()
        if not part:
            QMessageBox.warning(self, "Помилка", "Оберіть запчастину.")
            return

        qty = self.qty_input.value()
        if self.is_outgoing and qty > part.stock_quantity:
            QMessageBox.warning(
                self,
                "Недостатньо товару",
                f"На складі лише {part.stock_quantity} {part.unit} товару. Неможливо видати {qty}.",
            )
            return

        self.result_item = DocumentItem(
            id=None,
            document_id=None,
            part_id=part.id,
            quantity=qty,
            price=self.price_input.value(),
            part_number=part.part_number,
            part_name=part.name,
            unit=part.unit,
        )
        self.accept()


class DocumentCreateDialog(QDialog):
    """Діалогове вікно оформлення прибуткової або видаткової накладної."""

    def __init__(self, parent=None, doc_type: str = "incoming", user: Optional[User] = None):
        super().__init__(parent)
        self.doc_type = doc_type
        self.user = user
        is_incoming = self.doc_type == "incoming"
        self.setWindowTitle(
            "Оформлення прибуткової накладної" if is_incoming else "Оформлення видаткової накладної"
        )
        self.resize(750, 520)

        self.items: List[DocumentItem] = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Шапка документу
        header_form = QFormLayout()

        # Автономер
        self.doc_number_input = QLineEdit()
        self.doc_number_input.setText(generate_doc_number(self.doc_type))

        # Дата документу
        self.date_input = QDateTimeEdit()
        self.date_input.setDateTime(QDateTime.currentDateTime())
        self.date_input.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.date_input.setCalendarPopup(True)

        # Контрагент (Постачальник або Клієнт)
        self.counterparty_cb = QComboBox()
        if self.doc_type == "incoming":
            suppliers = get_suppliers()
            for s in suppliers:
                self.counterparty_cb.addItem(s.name, s.id)
            counterparty_label = "Постачальник:*"
        else:
            customers = get_customers()
            for c in customers:
                self.counterparty_cb.addItem(c.name, c.id)
            counterparty_label = "Клієнт (покупець):*"

        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Додаткові коментарі чи примітки")

        header_form.addRow("Номер накладної:*", self.doc_number_input)
        header_form.addRow("Дата документу:*", self.date_input)
        header_form.addRow(counterparty_label, self.counterparty_cb)
        header_form.addRow("Примітки:", self.notes_input)

        layout.addLayout(header_form)

        # Таблиця позицій
        layout.addWidget(QLabel("Позиції документу:"))
        self.table_view = QTableView()
        self.table_model = DocumentItemsTableModel(self.items)
        self.table_view.setModel(self.table_model)
        self.table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table_view)

        # Панель дій над позиціями
        items_btn_layout = QHBoxLayout()
        self.add_item_btn = QPushButton("Додати позицію...")
        self.add_item_btn.clicked.connect(self._add_item)

        self.remove_item_btn = QPushButton("Видалити вибрану позицію")
        self.remove_item_btn.clicked.connect(self._remove_item)

        self.total_label = QLabel("Загальна сума: 0.00 грн (позицій: 0)")
        font = self.total_label.font()
        font.setBold(True)
        self.total_label.setFont(font)

        items_btn_layout.addWidget(self.add_item_btn)
        items_btn_layout.addWidget(self.remove_item_btn)
        items_btn_layout.addStretch()
        items_btn_layout.addWidget(self.total_label)
        layout.addLayout(items_btn_layout)

        # Нижні кнопки проведення документу
        bottom_layout = QHBoxLayout()
        self.submit_btn = QPushButton("Провести документ")
        self.submit_btn.setStyleSheet("font-weight: bold; padding: 6px 14px;")
        self.submit_btn.clicked.connect(self._submit_document)

        self.cancel_btn = QPushButton("Скасувати")
        self.cancel_btn.clicked.connect(self.reject)

        bottom_layout.addStretch()
        bottom_layout.addWidget(self.submit_btn)
        bottom_layout.addWidget(self.cancel_btn)
        layout.addLayout(bottom_layout)

    def _update_totals(self) -> None:
        total = sum(i.total_price for i in self.items)
        qty = sum(i.quantity for i in self.items)
        self.total_label.setText(f"Загальна сума: {total:.2f} грн (кількість: {qty} шт.)")

    def _add_item(self) -> None:
        dlg = AddDocumentItemDialog(self, is_outgoing=(self.doc_type == "outgoing"))
        if dlg.exec():
            item = dlg.result_item
            # Перевіряємо чи позиція вже є в списку, якщо так — об'єднуємо
            for existing in self.items:
                if existing.part_id == item.part_id:
                    existing.quantity += item.quantity
                    existing.price = item.price
                    self.table_model.set_items(self.items)
                    self._update_totals()
                    return

            self.items.append(item)
            self.table_model.set_items(self.items)
            self._update_totals()

    def _remove_item(self) -> None:
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.information(self, "Повідомлення", "Виберіть рядок для видалення.")
            return

        row = selected_indexes[0].row()
        del self.items[row]
        self.table_model.set_items(self.items)
        self._update_totals()

    def _submit_document(self) -> None:
        doc_num = self.doc_number_input.text().strip()
        if not doc_num:
            QMessageBox.warning(self, "Помилка валідації", "Номер документа є обов'язковим.")
            return

        counterparty_id = self.counterparty_cb.currentData()
        if counterparty_id is None:
            QMessageBox.warning(self, "Помилка валідації", "Оберіть контрагента.")
            return

        if not self.items:
            QMessageBox.warning(self, "Помилка", "Додайте щонайменше одну позицію до документа.")
            return

        date_str = self.date_input.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        user_id = self.user.id if self.user and self.user.id else 1

        doc = Document(
            id=None,
            doc_type=self.doc_type,
            doc_number=doc_num,
            doc_date=date_str,
            counterparty_id=counterparty_id,
            user_id=user_id,
            notes=self.notes_input.text().strip() or None,
            items=self.items,
        )

        try:
            if self.doc_type == "incoming":
                process_incoming_document(doc)
            else:
                process_outgoing_document(doc)

            QMessageBox.information(
                self,
                "Успіх",
                f"Документ {doc_num} успішно проведено, залишки оновлено.",
            )
            self.accept()
        except InsufficientStockError as e:
            QMessageBox.critical(self, "Недостатньо залишку на складі", str(e))
        except DocumentValidationError as e:
            QMessageBox.warning(self, "Помилка валідації документа", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Критична помилка", f"Не вдалося провести документ:\n{str(e)}")


# ==========================================
# ДІАЛОГ ПЕРЕГЛЯДУ НАКЛАДНОЇ
# ==========================================

class DocumentViewDialog(QDialog):
    """Перегляд деталей та рядків збереженої накладної."""

    def __init__(self, parent=None, document: Optional[Document] = None):
        super().__init__(parent)
        self.document = document
        self.setWindowTitle(f"Перегляд документу {document.doc_number if document else ''}")
        self.resize(700, 460)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        if not self.document:
            return

        form = QFormLayout()
        form.addRow("Номер документу:", QLabel(self.document.doc_number))
        form.addRow("Тип:", QLabel(self.document.doc_type_ukr))
        form.addRow("Дата:", QLabel(self.document.doc_date))
        form.addRow("Контрагент:", QLabel(self.document.counterparty_name or "—"))
        form.addRow("Оформив користувач:", QLabel(self.document.user_name or "—"))
        form.addRow("Примітки:", QLabel(self.document.notes or "—"))
        layout.addLayout(form)

        layout.addWidget(QLabel("Склад позицій:"))
        table = QTableView()
        model = DocumentItemsTableModel(self.document.items)
        table.setModel(model)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(table)

        total_lbl = QLabel(
            f"Загальна сума: {self.document.total_amount:.2f} грн | Кількість: {self.document.total_quantity} шт."
        )
        font = total_lbl.font()
        font.setBold(True)
        total_lbl.setFont(font)
        total_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(total_lbl)

        close_btn = QPushButton("Закрити")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
