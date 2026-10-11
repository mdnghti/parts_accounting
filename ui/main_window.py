from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTabWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from db.repositories import (
    create_brand,
    create_category,
    create_customer,
    create_model,
    create_part,
    create_supplier,
    delete_brand,
    delete_category,
    delete_customer,
    delete_model,
    delete_part,
    delete_supplier,
    get_brands,
    get_categories,
    get_customers,
    get_documents,
    get_models,
    get_parts,
    get_suppliers,
    update_brand,
    update_category,
    update_customer,
    update_model,
    update_part,
    update_supplier,
)
from models.car import CarBrand, CarModel
from models.category import Category
from models.counterparty import Customer, Supplier
from models.document import Document
from models.part import Part
from models.user import User
from ui.forms import (
    BrandDialog,
    CategoryDialog,
    CounterpartyDialog,
    DocumentCreateDialog,
    DocumentViewDialog,
    ModelDialog,
    PartDialog,
)
from ui.models import (
    BrandsTableModel,
    CategoriesTableModel,
    CounterpartiesTableModel,
    DocumentsTableModel,
    ModelsTableModel,
    PartsTableModel,
)


class MainWindow(QMainWindow):
    """Головне вікно автоматизованої системи обліку автозапчастин."""

    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self.setWindowTitle(
            f"Автоматизована система обліку автозапчастин — {self.user.full_name} ({self.user.role})"
        )
        self.resize(1100, 700)
        self.setMinimumSize(900, 600)

        self._init_ui()
        self._apply_role_permissions()
        self.refresh_all_data()

    def _init_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Верхня панель користувача
        top_bar = QHBoxLayout()
        role_title = "Адміністратор" if self.user.is_admin else "Комірник"
        self.user_info_label = QLabel(
            f"👤 Користувач: <b>{self.user.full_name}</b> | Роль: <b>{role_title}</b>"
        )
        self.logout_btn = QPushButton("Змінити користувача")
        self.logout_btn.clicked.connect(self._handle_logout)

        top_bar.addWidget(self.user_info_label)
        top_bar.addStretch()
        top_bar.addWidget(self.logout_btn)
        main_layout.addLayout(top_bar)

        # Вкладки додатку
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # 1. Вкладка "Склад та запчастини"
        self._init_parts_tab()

        # 2. Вкладка "Рух товарів (Накладні)"
        self._init_documents_tab()

        # 3. Вкладка "Довідники"
        self._init_catalogs_tab()

        # Статус-бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Система готова до роботи.")

    def _apply_role_permissions(self) -> None:
        """Обмеження функціоналу для ролі комірника (storekeeper)."""
        if not self.user.is_admin:
            # Комірник не має права видаляти запчастини та довідники
            self.del_part_btn.setEnabled(False)
            self.del_part_btn.setToolTip("Видалення запчастин доступне лише адміністратору.")

            self.del_cat_btn.setEnabled(False)
            self.del_brand_btn.setEnabled(False)
            self.del_model_btn.setEnabled(False)
            self.del_sup_btn.setEnabled(False)
            self.del_cust_btn.setEnabled(False)

    def _handle_logout(self) -> None:
        """Вихід з облікового запису та повторний вхід."""
        from ui.login_dialog import LoginDialog

        login_dlg = LoginDialog(self)
        if login_dlg.exec():
            self.user = login_dlg.user
            role_title = "Адміністратор" if self.user.is_admin else "Комірник"
            self.user_info_label.setText(
                f"👤 Користувач: <b>{self.user.full_name}</b> | Роль: <b>{role_title}</b>"
            )
            self.setWindowTitle(
                f"Автоматизована система обліку автозапчастин — {self.user.full_name} ({self.user.role})"
            )
            self._apply_role_permissions()
            self.refresh_all_data()

    # ==========================================
    # ВКЛАДКА 1: ЗАПЧАСТИНИ НА СКЛАДІ
    # ==========================================

    def _init_parts_tab(self) -> None:
        parts_widget = QWidget()
        layout = QVBoxLayout(parts_widget)

        # Панель пошуку та фільтрації
        filter_layout = QHBoxLayout()

        self.parts_search_input = QLineEdit()
        self.parts_search_input.setPlaceholderText("🔍 Пошук за назвою або артикулом...")
        self.parts_search_input.textChanged.connect(self._filter_parts)

        self.parts_cat_filter = QComboBox()
        self.parts_cat_filter.addItem("Всі категорії", None)
        self.parts_cat_filter.currentIndexChanged.connect(self._filter_parts)

        self.parts_brand_filter = QComboBox()
        self.parts_brand_filter.addItem("Всі марки авто", None)
        self.parts_brand_filter.currentIndexChanged.connect(self._filter_parts)

        self.parts_low_stock_cb = QCheckBox("Лише дефіцит (≤ мін. залишку)")
        self.parts_low_stock_cb.toggled.connect(self._filter_parts)

        self.reset_filter_btn = QPushButton("Скинути фільтри")
        self.reset_filter_btn.clicked.connect(self._reset_parts_filters)

        filter_layout.addWidget(self.parts_search_input, stretch=2)
        filter_layout.addWidget(self.parts_cat_filter, stretch=1)
        filter_layout.addWidget(self.parts_brand_filter, stretch=1)
        filter_layout.addWidget(self.parts_low_stock_cb)
        filter_layout.addWidget(self.reset_filter_btn)
        layout.addLayout(filter_layout)

        # Таблиця запчастин
        self.parts_table_view = QTableView()
        self.parts_table_model = PartsTableModel()
        self.parts_table_view.setModel(self.parts_table_model)
        self.parts_table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.parts_table_view.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.parts_table_view.doubleClicked.connect(self._edit_part)
        layout.addWidget(self.parts_table_view)

        # Кнопки дій над запчастинами
        actions_layout = QHBoxLayout()
        self.add_part_btn = QPushButton("➕ Додати запчастину")
        self.add_part_btn.clicked.connect(self._add_part)

        self.edit_part_btn = QPushButton("✏️ Редагувати")
        self.edit_part_btn.clicked.connect(self._edit_part)

        self.del_part_btn = QPushButton("🗑️ Видалити")
        self.del_part_btn.clicked.connect(self._delete_part)

        self.refresh_parts_btn = QPushButton("🔄 Оновити")
        self.refresh_parts_btn.clicked.connect(self._load_parts)

        actions_layout.addWidget(self.add_part_btn)
        actions_layout.addWidget(self.edit_part_btn)
        actions_layout.addWidget(self.del_part_btn)
        actions_layout.addStretch()
        actions_layout.addWidget(self.refresh_parts_btn)
        layout.addLayout(actions_layout)

        self.tabs.addTab(parts_widget, "📦 Склад та запчастини")

    def _reset_parts_filters(self) -> None:
        self.parts_search_input.clear()
        self.parts_cat_filter.setCurrentIndex(0)
        self.parts_brand_filter.setCurrentIndex(0)
        self.parts_low_stock_cb.setChecked(False)
        self._load_parts()

    def _filter_parts(self) -> None:
        search_txt = self.parts_search_input.text().strip() or None
        cat_id = self.parts_cat_filter.currentData()
        brand_id = self.parts_brand_filter.currentData()
        low_stock = self.parts_low_stock_cb.isChecked()

        parts = get_parts(
            search=search_txt,
            category_id=cat_id,
            brand_id=brand_id,
            low_stock_only=low_stock,
        )
        self.parts_table_model.set_parts(parts)
        self.status_bar.showMessage(f"Знайдено запчастин: {len(parts)}")

    def _load_parts(self) -> None:
        self._filter_parts()

    def _add_part(self) -> None:
        dlg = PartDialog(self)
        if dlg.exec():
            try:
                create_part(dlg.result_part)
                self._load_parts()
                self.status_bar.showMessage("Запчастину успішно додано.", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Помилка додавання", str(e))

    def _edit_part(self) -> None:
        idx = self.parts_table_view.selectionModel().selectedRows()
        if not idx:
            QMessageBox.information(self, "Повідомлення", "Виберіть запчастину для редагування.")
            return

        part = self.parts_table_model.get_part_at(idx[0].row())
        if not part:
            return

        dlg = PartDialog(self, part=part)
        if dlg.exec():
            try:
                update_part(dlg.result_part)
                self._load_parts()
                self.status_bar.showMessage("Запчастину оновлено.", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Помилка збереження", str(e))

    def _delete_part(self) -> None:
        idx = self.parts_table_view.selectionModel().selectedRows()
        if not idx:
            QMessageBox.information(self, "Повідомлення", "Виберіть запчастину для видалення.")
            return

        part = self.parts_table_model.get_part_at(idx[0].row())
        if not part:
            return

        reply = QMessageBox.question(
            self,
            "Підтвердження видалення",
            f"Ви дійсно бажаєте видалити запчастину '{part.name}' (арт. {part.part_number})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                delete_part(part.id)
                self._load_parts()
                self.status_bar.showMessage("Запчастину видалено.", 3000)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Помилка видалення",
                    f"Неможливо видалити запчастину. Можливо, вона використовується в накладних.\n{str(e)}",
                )

    # ==========================================
    # ВКЛАДКА 2: ДОКУМЕНТИ ОБЛІКУ (ПРИХІД / РОЗХІД)
    # ==========================================

    def _init_documents_tab(self) -> None:
        doc_widget = QWidget()
        layout = QVBoxLayout(doc_widget)

        # Панель фільтрів документів
        filter_layout = QHBoxLayout()
        self.doc_type_filter = QComboBox()
        self.doc_type_filter.addItem("Всі типи документів", None)
        self.doc_type_filter.addItem("Прибуткові накладні", "incoming")
        self.doc_type_filter.addItem("Видаткові накладні", "outgoing")
        self.doc_type_filter.currentIndexChanged.connect(self._load_documents)

        filter_layout.addWidget(QLabel("Фільтр за типом:"))
        filter_layout.addWidget(self.doc_type_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Таблиця документів
        self.docs_table_view = QTableView()
        self.docs_table_model = DocumentsTableModel()
        self.docs_table_view.setModel(self.docs_table_model)
        self.docs_table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.docs_table_view.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.docs_table_view.doubleClicked.connect(self._view_document)
        layout.addWidget(self.docs_table_view)

        # Кнопки дій з накладними
        actions_layout = QHBoxLayout()
        self.incoming_doc_btn = QPushButton("📥 Оформити прихід (від постачальника)")
        self.incoming_doc_btn.setStyleSheet("font-weight: bold; color: green;")
        self.incoming_doc_btn.clicked.connect(lambda: self._create_document("incoming"))

        self.outgoing_doc_btn = QPushButton("📤 Оформити розхід (клієнту)")
        self.outgoing_doc_btn.setStyleSheet("font-weight: bold; color: darkred;")
        self.outgoing_doc_btn.clicked.connect(lambda: self._create_document("outgoing"))

        self.view_doc_btn = QPushButton("🔍 Переглянути накладну")
        self.view_doc_btn.clicked.connect(self._view_document)

        self.refresh_docs_btn = QPushButton("🔄 Оновити список")
        self.refresh_docs_btn.clicked.connect(self._load_documents)

        actions_layout.addWidget(self.incoming_doc_btn)
        actions_layout.addWidget(self.outgoing_doc_btn)
        actions_layout.addWidget(self.view_doc_btn)
        actions_layout.addStretch()
        actions_layout.addWidget(self.refresh_docs_btn)
        layout.addLayout(actions_layout)

        self.tabs.addTab(doc_widget, "📋 Прихід та розхід")

    def _load_documents(self) -> None:
        doc_type = self.doc_type_filter.currentData()
        docs = get_documents(doc_type=doc_type)
        self.docs_table_model.set_documents(docs)

    def _create_document(self, doc_type: str) -> None:
        dlg = DocumentCreateDialog(self, doc_type=doc_type, user=self.user)
        if dlg.exec():
            self._load_documents()
            self._load_parts()  # Оновлюємо також залишки запчастин

    def _view_document(self) -> None:
        from db.repositories import get_document_by_id

        idx = self.docs_table_view.selectionModel().selectedRows()
        if not idx:
            QMessageBox.information(self, "Повідомлення", "Виберіть накладну для перегляду.")
            return

        doc_summary = self.docs_table_model.get_document_at(idx[0].row())
        if not doc_summary:
            return

        full_doc = get_document_by_id(doc_summary.id)
        if full_doc:
            dlg = DocumentViewDialog(self, document=full_doc)
            dlg.exec()

    # ==========================================
    # ВКЛАДКА 3: ДОВІДНИКИ (КАТЕГОРІЇ, АВТО, КОНТРАГЕНТИ)
    # ==========================================

    def _init_catalogs_tab(self) -> None:
        catalogs_widget = QWidget()
        layout = QVBoxLayout(catalogs_widget)

        self.catalog_tabs = QTabWidget()
        layout.addWidget(self.catalog_tabs)

        # 3.1 Категорії
        self._init_categories_subtab()

        # 3.2 Марки та моделі авто
        self._init_cars_subtab()

        # 3.3 Постачальники
        self._init_suppliers_subtab()

        # 3.4 Клієнти
        self._init_customers_subtab()

        self.tabs.addTab(catalogs_widget, "🗂️ Довідники")

    def _init_categories_subtab(self) -> None:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.cat_table = QTableView()
        self.cat_model = CategoriesTableModel()
        self.cat_table.setModel(self.cat_model)
        self.cat_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.cat_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.cat_table)

        btn_box = QHBoxLayout()
        add_btn = QPushButton("➕ Додати категорію")
        add_btn.clicked.connect(self._add_category)
        edit_btn = QPushButton("✏️ Редагувати")
        edit_btn.clicked.connect(self._edit_category)
        self.del_cat_btn = QPushButton("🗑️ Видалити")
        self.del_cat_btn.clicked.connect(self._delete_category)

        btn_box.addWidget(add_btn)
        btn_box.addWidget(edit_btn)
        btn_box.addWidget(self.del_cat_btn)
        btn_box.addStretch()
        layout.addLayout(btn_box)

        self.catalog_tabs.addTab(widget, "Категорії запчастин")

    def _load_categories(self) -> None:
        cats = get_categories()
        self.cat_model.set_categories(cats)

        # Оновлюємо фільтр категорій на головній вкладці
        current_cat_id = self.parts_cat_filter.currentData()
        self.parts_cat_filter.blockSignals(True)
        self.parts_cat_filter.clear()
        self.parts_cat_filter.addItem("Всі категорії", None)
        for c in cats:
            self.parts_cat_filter.addItem(c.name, c.id)
        idx = self.parts_cat_filter.findData(current_cat_id)
        if idx >= 0:
            self.parts_cat_filter.setCurrentIndex(idx)
        self.parts_cat_filter.blockSignals(False)

    def _add_category(self) -> None:
        dlg = CategoryDialog(self)
        if dlg.exec():
            try:
                create_category(dlg.result_category)
                self._load_categories()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", str(e))

    def _edit_category(self) -> None:
        idx = self.cat_table.selectionModel().selectedRows()
        if not idx:
            QMessageBox.information(self, "Повідомлення", "Виберіть категорію.")
            return
        cat = self.cat_model.get_category_at(idx[0].row())
        dlg = CategoryDialog(self, category=cat)
        if dlg.exec():
            try:
                update_category(dlg.result_category)
                self._load_categories()
                self._load_parts()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", str(e))

    def _delete_category(self) -> None:
        idx = self.cat_table.selectionModel().selectedRows()
        if not idx:
            return
        cat = self.cat_model.get_category_at(idx[0].row())
        reply = QMessageBox.question(
            self,
            "Видалення",
            f"Видалити категорію '{cat.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                delete_category(cat.id)
                self._load_categories()
                self._load_parts()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Неможливо видалити категорію:\n{str(e)}")

    def _init_cars_subtab(self) -> None:
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Ліва колонка: Марки
        brand_box = QVBoxLayout()
        brand_box.addWidget(QLabel("<b>Марки автомобілів:</b>"))
        self.brand_table = QTableView()
        self.brand_model = BrandsTableModel()
        self.brand_table.setModel(self.brand_model)
        self.brand_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.brand_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.brand_table.selectionModel().selectionChanged.connect(self._on_brand_selected)
        brand_box.addWidget(self.brand_table)

        b_btns = QHBoxLayout()
        b_add = QPushButton("➕ Додати")
        b_add.clicked.connect(self._add_brand)
        b_edit = QPushButton("✏️ Змінити")
        b_edit.clicked.connect(self._edit_brand)
        self.del_brand_btn = QPushButton("🗑️ Видалити")
        self.del_brand_btn.clicked.connect(self._delete_brand)
        b_btns.addWidget(b_add)
        b_btns.addWidget(b_edit)
        b_btns.addWidget(self.del_brand_btn)
        brand_box.addLayout(b_btns)

        # Права колонка: Моделі
        model_box = QVBoxLayout()
        model_box.addWidget(QLabel("<b>Моделі автомобілів:</b>"))
        self.model_table = QTableView()
        self.model_model = ModelsTableModel()
        self.model_table.setModel(self.model_model)
        self.model_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.model_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        model_box.addWidget(self.model_table)

        m_btns = QHBoxLayout()
        m_add = QPushButton("➕ Додати модель")
        m_add.clicked.connect(self._add_model)
        m_edit = QPushButton("✏️ Змінити")
        m_edit.clicked.connect(self._edit_model)
        self.del_model_btn = QPushButton("🗑️ Видалити")
        self.del_model_btn.clicked.connect(self._delete_model)
        m_btns.addWidget(m_add)
        m_btns.addWidget(m_edit)
        m_btns.addWidget(self.del_model_btn)
        model_box.addLayout(m_btns)

        layout.addLayout(brand_box, stretch=1)
        layout.addLayout(model_box, stretch=2)

        self.catalog_tabs.addTab(widget, "Марки та моделі авто")

    def _load_brands_and_models(self) -> None:
        brands = get_brands()
        self.brand_model.set_brands(brands)
        self.model_model.set_models(get_models())

        # Оновлюємо фільтр марок на вкладці складу
        current_b_id = self.parts_brand_filter.currentData()
        self.parts_brand_filter.blockSignals(True)
        self.parts_brand_filter.clear()
        self.parts_brand_filter.addItem("Всі марки авто", None)
        for b in brands:
            self.parts_brand_filter.addItem(b.name, b.id)
        idx = self.parts_brand_filter.findData(current_b_id)
        if idx >= 0:
            self.parts_brand_filter.setCurrentIndex(idx)
        self.parts_brand_filter.blockSignals(False)

    def _on_brand_selected(self) -> None:
        idx = self.brand_table.selectionModel().selectedRows()
        if idx:
            brand = self.brand_model.get_brand_at(idx[0].row())
            if brand:
                self.model_model.set_models(get_models(brand_id=brand.id))
        else:
            self.model_model.set_models(get_models())

    def _add_brand(self) -> None:
        dlg = BrandDialog(self)
        if dlg.exec():
            try:
                create_brand(dlg.result_brand)
                self._load_brands_and_models()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", str(e))

    def _edit_brand(self) -> None:
        idx = self.brand_table.selectionModel().selectedRows()
        if not idx:
            return
        brand = self.brand_model.get_brand_at(idx[0].row())
        dlg = BrandDialog(self, brand=brand)
        if dlg.exec():
            try:
                update_brand(dlg.result_brand)
                self._load_brands_and_models()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", str(e))

    def _delete_brand(self) -> None:
        idx = self.brand_table.selectionModel().selectedRows()
        if not idx:
            return
        brand = self.brand_model.get_brand_at(idx[0].row())
        reply = QMessageBox.question(
            self,
            "Видалення",
            f"Видалити марку '{brand.name}' та всі її моделі?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                delete_brand(brand.id)
                self._load_brands_and_models()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", str(e))

    def _add_model(self) -> None:
        dlg = ModelDialog(self)
        if dlg.exec():
            try:
                create_model(dlg.result_model)
                self._load_brands_and_models()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", str(e))

    def _edit_model(self) -> None:
        idx = self.model_table.selectionModel().selectedRows()
        if not idx:
            return
        model = self.model_model.get_model_at(idx[0].row())
        dlg = ModelDialog(self, model=model)
        if dlg.exec():
            try:
                update_model(dlg.result_model)
                self._load_brands_and_models()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", str(e))

    def _delete_model(self) -> None:
        idx = self.model_table.selectionModel().selectedRows()
        if not idx:
            return
        model = self.model_model.get_model_at(idx[0].row())
        reply = QMessageBox.question(
            self,
            "Видалення",
            f"Видалити модель '{model.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                delete_model(model.id)
                self._load_brands_and_models()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", str(e))

    def _init_suppliers_subtab(self) -> None:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.sup_table = QTableView()
        self.sup_model = CounterpartiesTableModel()
        self.sup_table.setModel(self.sup_model)
        self.sup_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.sup_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.sup_table)

        btn_box = QHBoxLayout()
        add_btn = QPushButton("➕ Додати постачальника")
        add_btn.clicked.connect(self._add_supplier)
        edit_btn = QPushButton("✏️ Редагувати")
        edit_btn.clicked.connect(self._edit_supplier)
        self.del_sup_btn = QPushButton("🗑️ Видалити")
        self.del_sup_btn.clicked.connect(self._delete_supplier)

        btn_box.addWidget(add_btn)
        btn_box.addWidget(edit_btn)
        btn_box.addWidget(self.del_sup_btn)
        btn_box.addStretch()
        layout.addLayout(btn_box)

        self.catalog_tabs.addTab(widget, "Постачальники")

    def _load_suppliers(self) -> None:
        sups = get_suppliers()
        self.sup_model.set_items(sups)

    def _add_supplier(self) -> None:
        dlg = CounterpartyDialog(self, title="Постачальник")
        if dlg.exec():
            try:
                data = dlg.result_data
                create_supplier(Supplier(id=None, **data))
                self._load_suppliers()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", str(e))

    def _edit_supplier(self) -> None:
        idx = self.sup_table.selectionModel().selectedRows()
        if not idx:
            return
        sup = self.sup_model.get_item_at(idx[0].row())
        dlg = CounterpartyDialog(self, title="Постачальник", entity=sup)
        if dlg.exec():
            try:
                data = dlg.result_data
                update_supplier(Supplier(id=sup.id, **data))
                self._load_suppliers()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", str(e))

    def _delete_supplier(self) -> None:
        idx = self.sup_table.selectionModel().selectedRows()
        if not idx:
            return
        sup = self.sup_model.get_item_at(idx[0].row())
        reply = QMessageBox.question(
            self,
            "Видалення",
            f"Видалити постачальника '{sup.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                delete_supplier(sup.id)
                self._load_suppliers()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Неможливо видалити:\n{str(e)}")

    def _init_customers_subtab(self) -> None:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.cust_table = QTableView()
        self.cust_model = CounterpartiesTableModel()
        self.cust_table.setModel(self.cust_model)
        self.cust_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.cust_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.cust_table)

        btn_box = QHBoxLayout()
        add_btn = QPushButton("➕ Додати клієнта")
        add_btn.clicked.connect(self._add_customer)
        edit_btn = QPushButton("✏️ Редагувати")
        edit_btn.clicked.connect(self._edit_customer)
        self.del_cust_btn = QPushButton("🗑️ Видалити")
        self.del_cust_btn.clicked.connect(self._delete_customer)

        btn_box.addWidget(add_btn)
        btn_box.addWidget(edit_btn)
        btn_box.addWidget(self.del_cust_btn)
        btn_box.addStretch()
        layout.addLayout(btn_box)

        self.catalog_tabs.addTab(widget, "Клієнти (покупці)")

    def _load_customers(self) -> None:
        custs = get_customers()
        self.cust_model.set_items(custs)

    def _add_customer(self) -> None:
        dlg = CounterpartyDialog(self, title="Клієнт")
        if dlg.exec():
            try:
                data = dlg.result_data
                create_customer(Customer(id=None, **data))
                self._load_customers()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", str(e))

    def _edit_customer(self) -> None:
        idx = self.cust_table.selectionModel().selectedRows()
        if not idx:
            return
        cust = self.cust_model.get_item_at(idx[0].row())
        dlg = CounterpartyDialog(self, title="Клієнт", entity=cust)
        if dlg.exec():
            try:
                data = dlg.result_data
                update_customer(Customer(id=cust.id, **data))
                self._load_customers()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", str(e))

    def _delete_customer(self) -> None:
        idx = self.cust_table.selectionModel().selectedRows()
        if not idx:
            return
        cust = self.cust_model.get_item_at(idx[0].row())
        reply = QMessageBox.question(
            self,
            "Видалення",
            f"Видалити клієнта '{cust.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                delete_customer(cust.id)
                self._load_customers()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Неможливо видалити:\n{str(e)}")

    def refresh_all_data(self) -> None:
        """Повне оновлення даних у всіх вкладках."""
        self._load_parts()
        self._load_documents()
        self._load_categories()
        self._load_brands_and_models()
        self._load_suppliers()
        self._load_customers()
