from dataclasses import dataclass
from typing import Optional


@dataclass
class Supplier:
    """Модель постачальника."""
    id: Optional[int]
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None


@dataclass
class Customer:
    """Модель клієнта (покупця)."""
    id: Optional[int]
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
