import sys
from pathlib import Path

# Додаємо корінь проекту в sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from db.connection import get_db_path, init_db


def main() -> None:
    """Точка входу додатку."""
    print("Ініціалізація бази даних...")
    init_db()
    db_path = get_db_path()
    print(f"База даних готова: {db_path} (існує: {db_path.exists()})")


if __name__ == "__main__":
    main()
