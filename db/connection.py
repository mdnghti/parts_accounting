import sqlite3
import sys
from pathlib import Path


def get_app_dir() -> Path:
    """Шлях до каталогу з виконуваним файлом або кореня проекту."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def get_resource_dir() -> Path:
    """Шлях до вбудованих ресурсів PyInstaller (_MEIPASS) або кореню проекту."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS).resolve()
    return Path(__file__).resolve().parent.parent


def get_db_path() -> Path:
    """Шлях до файлу БД поруч з додатком."""
    return get_app_dir() / "parts_accounting.db"


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Створення та налаштування з'єднання з SQLite."""
    target_path = Path(db_path) if db_path else get_db_path()
    conn = sqlite3.connect(str(target_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    # Реєстрація функції переведення в нижній регістр для повноцінного пошуку кирилицею
    conn.create_function("py_lower", 1, lambda s: s.lower() if s is not None else "")
    return conn


def init_db(db_path: Path | str | None = None) -> None:
    """Ініціалізація схеми БД та первинних даних при першому запуску."""
    target_path = Path(db_path) if db_path else get_db_path()

    schema_file = get_resource_dir() / "db" / "schema.sql"
    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with get_connection(target_path) as conn:
        conn.executescript(schema_sql)

        # Якщо база нова або порожня — заповнюємо початковими даними
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            from db.seed_data import seed_initial_data
            seed_initial_data(conn)
