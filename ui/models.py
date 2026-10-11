from typing import Any, List, Optional
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from models.car import CarBrand, CarModel
from models.category import Category
from models.counterparty import Customer, Supplier
from models.document import Document, DocumentItem
from models.part import Part


class PartsTableModel(QAbstractTableModel):
    """Модель таблиці запчастин із підсвічуванням низького залишку."""

    COLUMNS = [
        ("ID", 40),
        ("Артикул", 110),
        ("Назва запчастини", 220),
        ("Категорія", 140),
        ("Ціна (грн)", 90),
        ("Залишок", 75),
        ("Мін. залишок", 85),
        ("Од. вим.", 70),
    ]

    def __init__(self, parts: Optional[List[Part]] = None):
        super().__init__()
        self.parts: List[Part] = parts or []

    def set_parts(self, parts: List[Part]) -> None:
        self.beginResetModel()
        self.parts = parts
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.parts)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.COLUMNS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.COLUMNS[section][0]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self.parts)):
            return None

        part = self.parts[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return part.id
            elif col == 1:
                return part.part_number
            elif col == 2:
                return part.name
            elif col == 3:
                return part.category_name or "—"
            elif col == 4:
                return f"{part.price:.2f}"
            elif col == 5:
                return part.stock_quantity
            elif col == 6:
                return part.min_stock_quantity
            elif col == 7:
                return part.unit

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (0, 5, 6, 7):
                return int(Qt.AlignmentFlag.AlignCenter)
            elif col == 4:
                return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        elif role == Qt.ItemDataRole.BackgroundRole:
            # Якщо залишок менший або дорівнює мінімальному — виділяємо м'яким червоно-рожевим фоном
            if part.is_low_stock:
                return QColor(255, 230, 230)

        elif role == Qt.ItemDataRole.ForegroundRole:
            if part.is_low_stock and col in (5, 6):
                return QColor(180, 20, 20)

        return None

    def get_part_at(self, row: int) -> Optional[Part]:
        if 0 <= row < len(self.parts):
            return self.parts[row]
        return None


class CategoriesTableModel(QAbstractTableModel):
    """Модель таблиці категорій."""

    COLUMNS = ["ID", "Назва категорії", "Опис"]

    def __init__(self, categories: Optional[List[Category]] = None):
        super().__init__()
        self.categories: List[Category] = categories or []

    def set_categories(self, categories: List[Category]) -> None:
        self.beginResetModel()
        self.categories = categories
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.categories)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.COLUMNS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.COLUMNS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self.categories)):
            return None

        cat = self.categories[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return cat.id
            elif col == 1:
                return cat.name
            elif col == 2:
                return cat.description or "—"

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col == 0:
                return int(Qt.AlignmentFlag.AlignCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        return None

    def get_category_at(self, row: int) -> Optional[Category]:
        if 0 <= row < len(self.categories):
            return self.categories[row]
        return None


class BrandsTableModel(QAbstractTableModel):
    """Модель таблиці марок авто."""

    COLUMNS = ["ID", "Марка автомобіля"]

    def __init__(self, brands: Optional[List[CarBrand]] = None):
        super().__init__()
        self.brands: List[CarBrand] = brands or []

    def set_brands(self, brands: List[CarBrand]) -> None:
        self.beginResetModel()
        self.brands = brands
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.brands)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.COLUMNS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.COLUMNS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self.brands)):
            return None

        brand = self.brands[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return brand.id
            elif col == 1:
                return brand.name

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col == 0:
                return int(Qt.AlignmentFlag.AlignCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        return None

    def get_brand_at(self, row: int) -> Optional[CarBrand]:
        if 0 <= row < len(self.brands):
            return self.brands[row]
        return None


class ModelsTableModel(QAbstractTableModel):
    """Модель таблиці моделей авто."""

    COLUMNS = ["ID", "Марка", "Модель", "Роки випуску"]

    def __init__(self, models: Optional[List[CarModel]] = None):
        super().__init__()
        self.models: List[CarModel] = models or []

    def set_models(self, models: List[CarModel]) -> None:
        self.beginResetModel()
        self.models = models
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.models)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.COLUMNS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.COLUMNS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self.models)):
            return None

        model = self.models[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return model.id
            elif col == 1:
                return model.brand_name or "—"
            elif col == 2:
                return model.name
            elif col == 3:
                y_from = str(model.year_from) if model.year_from else "..."
                y_to = str(model.year_to) if model.year_to else "..."
                return f"{y_from} - {y_to}" if (model.year_from or model.year_to) else "—"

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (0, 3):
                return int(Qt.AlignmentFlag.AlignCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        return None

    def get_model_at(self, row: int) -> Optional[CarModel]:
        if 0 <= row < len(self.models):
            return self.models[row]
        return None


class CounterpartiesTableModel(QAbstractTableModel):
    """Модель таблиці контрагентів (постачальників або клієнтів)."""

    COLUMNS = ["ID", "Назва / ПІБ", "Телефон", "Email", "Адреса"]

    def __init__(self, items: Optional[List[Any]] = None):
        super().__init__()
        self.items: List[Any] = items or []

    def set_items(self, items: List[Any]) -> None:
        self.beginResetModel()
        self.items = items
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.items)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.COLUMNS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.COLUMNS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self.items)):
            return None

        item = self.items[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return item.id
            elif col == 1:
                return item.name
            elif col == 2:
                return item.phone or "—"
            elif col == 3:
                return item.email or "—"
            elif col == 4:
                return item.address or "—"

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col == 0:
                return int(Qt.AlignmentFlag.AlignCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        return None

    def get_item_at(self, row: int) -> Optional[Any]:
        if 0 <= row < len(self.items):
            return self.items[row]
        return None


class DocumentsTableModel(QAbstractTableModel):
    """Модель таблиці документів руху товарів."""

    COLUMNS = [
        "ID",
        "Тип документа",
        "Номер накладної",
        "Дата",
        "Контрагент",
        "Користувач",
        "Примітки",
    ]

    def __init__(self, documents: Optional[List[Document]] = None):
        super().__init__()
        self.documents: List[Document] = documents or []

    def set_documents(self, documents: List[Document]) -> None:
        self.beginResetModel()
        self.documents = documents
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.documents)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.COLUMNS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.COLUMNS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self.documents)):
            return None

        doc = self.documents[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return doc.id
            elif col == 1:
                return doc.doc_type_ukr
            elif col == 2:
                return doc.doc_number
            elif col == 3:
                return doc.doc_date
            elif col == 4:
                return doc.counterparty_name
            elif col == 5:
                return doc.user_name
            elif col == 6:
                return doc.notes or "—"

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (0, 3):
                return int(Qt.AlignmentFlag.AlignCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        elif role == Qt.ItemDataRole.ForegroundRole:
            if col == 1:
                if doc.doc_type == "incoming":
                    return QColor(20, 120, 40)  # Зелений для приходу
                else:
                    return QColor(160, 40, 20)  # Червоний для розходу

        return None

    def get_document_at(self, row: int) -> Optional[Document]:
        if 0 <= row < len(self.documents):
            return self.documents[row]
        return None


class DocumentItemsTableModel(QAbstractTableModel):
    """Модель рядків накладної (позицій товарів)."""

    COLUMNS = [
        "Артикул",
        "Назва запчастини",
        "Кількість",
        "Од. вим.",
        "Ціна (грн)",
        "Сума (грн)",
    ]

    def __init__(self, items: Optional[List[DocumentItem]] = None):
        super().__init__()
        self.items: List[DocumentItem] = items or []

    def set_items(self, items: List[DocumentItem]) -> None:
        self.beginResetModel()
        self.items = items
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.items)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.COLUMNS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.COLUMNS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self.items)):
            return None

        item = self.items[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return item.part_number or "—"
            elif col == 1:
                return item.part_name or "—"
            elif col == 2:
                return item.quantity
            elif col == 3:
                return item.unit or "шт."
            elif col == 4:
                return f"{item.price:.2f}"
            elif col == 5:
                return f"{item.total_price:.2f}"

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (2, 3):
                return int(Qt.AlignmentFlag.AlignCenter)
            elif col in (4, 5):
                return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        return None
