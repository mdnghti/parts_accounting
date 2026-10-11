import hashlib
import os
import sqlite3
from typing import Optional

from db.connection import get_connection
from db.repositories import create_user, get_user_by_id, get_user_by_username, update_user
from models.user import User


def hash_password(password: str, salt_hex: Optional[str] = None) -> tuple[str, str]:
    """Хешування пароля за допомогою PBKDF2-HMAC-SHA256 з 16-байтовою сіллю."""
    if salt_hex is None:
        salt = os.urandom(16)
        salt_hex = salt.hex()
    else:
        salt = bytes.fromhex(salt_hex)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return key.hex(), salt_hex


def verify_password(password: str, password_hash: str, salt_hex: str) -> bool:
    """Перевірка відповідності введеного пароля збереженому хешу."""
    computed_hash, _ = hash_password(password, salt_hex)
    return hashlib.sha256(computed_hash.encode()).digest() == hashlib.sha256(password_hash.encode()).digest()


def authenticate_user(username: str, password: str, conn: Optional[sqlite3.Connection] = None) -> Optional[User]:
    """
    Аутентифікація користувача за логіном і паролем.
    Повертає об'єкт User при успіху, або None при невірних даних.
    """
    should_close = conn is None
    c = conn or get_connection()
    try:
        user = get_user_by_username(username.strip(), conn=c)
        if not user:
            return None
        if verify_password(password, user.password_hash, user.salt):
            return user
        return None
    finally:
        if should_close:
            c.close()


def register_user(
    username: str,
    password: str,
    role: str,
    full_name: str,
    conn: Optional[sqlite3.Connection] = None,
) -> User:
    """Реєстрація нового користувача з валідацією ролі та хешуванням пароля."""
    if role not in ("admin", "storekeeper"):
        raise ValueError(f"Неприпустима роль користувача: {role}")

    if len(password.strip()) < 4:
        raise ValueError("Пароль повинен містити щонайменше 4 символи.")

    pwd_hash, salt = hash_password(password.strip())
    new_user = User(
        id=None,
        username=username.strip(),
        password_hash=pwd_hash,
        salt=salt,
        role=role,
        full_name=full_name.strip(),
    )

    should_close = conn is None
    c = conn or get_connection()
    try:
        user_id = create_user(new_user, conn=c)
        new_user.id = user_id
        return new_user
    finally:
        if should_close:
            c.close()


def change_password(
    user_id: int,
    old_password: str,
    new_password: str,
    conn: Optional[sqlite3.Connection] = None,
) -> bool:
    """Зміна пароля користувачем з перевіркою старого пароля."""
    should_close = conn is None
    c = conn or get_connection()
    try:
        user = get_user_by_id(user_id, conn=c)
        if not user:
            raise ValueError(f"Користувача з ID {user_id} не знайдено.")

        if not verify_password(old_password, user.password_hash, user.salt):
            return False

        if len(new_password.strip()) < 4:
            raise ValueError("Новий пароль повинен містити щонайменше 4 символи.")

        pwd_hash, salt = hash_password(new_password.strip())
        user.password_hash = pwd_hash
        user.salt = salt
        return update_user(user, conn=c)
    finally:
        if should_close:
            c.close()
