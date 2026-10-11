from dataclasses import dataclass
from typing import Optional


@dataclass
class CarBrand:
    """Модель марки автомобіля."""
    id: Optional[int]
    name: str


@dataclass
class CarModel:
    """Модель автомобіля певної марки."""
    id: Optional[int]
    brand_id: int
    name: str
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    brand_name: Optional[str] = None

    @property
    def display_name(self) -> str:
        years = ""
        if self.year_from or self.year_to:
            y_from = self.year_from or "..."
            y_to = self.year_to or "..."
            years = f" ({y_from}-{y_to})"
        prefix = f"{self.brand_name} " if self.brand_name else ""
        return f"{prefix}{self.name}{years}"
