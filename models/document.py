from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DocumentItem:
    """Рядок накладної (позиція товару)."""
    id: Optional[int]
    document_id: Optional[int]
    part_id: int
    quantity: int
    price: float
    part_number: Optional[str] = None
    part_name: Optional[str] = None
    unit: Optional[str] = "шт."

    @property
    def total_price(self) -> float:
        return round(self.quantity * self.price, 2)


@dataclass
class Document:
    """Документ руху товару (прихід або розхід)."""
    id: Optional[int]
    doc_type: str  # 'incoming' або 'outgoing'
    doc_number: str
    doc_date: str  # 'YYYY-MM-DD HH:MM:SS' або 'YYYY-MM-DD'
    counterparty_id: int
    user_id: int
    notes: Optional[str] = None
    created_at: Optional[str] = None
    counterparty_name: Optional[str] = None
    user_name: Optional[str] = None
    items: List[DocumentItem] = field(default_factory=list)

    @property
    def total_amount(self) -> float:
        return round(sum(item.total_price for item in self.items), 2)

    @property
    def total_quantity(self) -> int:
        return sum(item.quantity for item in self.items)

    @property
    def doc_type_ukr(self) -> str:
        return "Прибуткова накладна" if self.doc_type == "incoming" else "Видаткова накладна"
