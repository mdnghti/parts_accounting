import os
import pytest
from db.connection import init_db

# Забезпечуємо роботу PySide6 без графічного сервера
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Автоматична ініціалізація бази даних перед початком тестів."""
    init_db()
