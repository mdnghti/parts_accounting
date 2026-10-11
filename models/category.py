from dataclasses import dataclass
from typing import Optional


@dataclass
class Category:
    """Модель категорії автозапчастин."""
    id: Optional[int]
    name: str
    description: Optional[str] = None
