from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    """Модель користувача системи."""
    id: Optional[int]
    username: str
    password_hash: str
    salt: str
    role: str  # 'admin' або 'storekeeper'
    full_name: str
    created_at: Optional[str] = None

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"
