from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Part:
    """Модель автозапчастини."""
    id: Optional[int]
    part_number: str
    name: str
    category_id: int
    price: float
    stock_quantity: int = 0
    min_stock_quantity: int = 0
    unit: str = "шт."
    category_name: Optional[str] = None
    compatible_model_ids: List[int] = field(default_factory=list)

    @property
    def is_low_stock(self) -> bool:
        """Перевірка чи залишок нижчий або дорівнює мінімальному."""
        return self.stock_quantity <= self.min_stock_quantity
