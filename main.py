import sys
from pathlib import Path

# Додаємо корінь проекту в sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtWidgets import QApplication

from db.connection import init_db
from ui.login_dialog import LoginDialog
from ui.main_window import MainWindow


def main() -> None:
    """Точка входу додатку."""
    # Ініціалізація БД (створює файл та початкові дані, якщо їх нема)
    init_db()

    app = QApplication(sys.argv)
    app.setApplicationName("PartsAccounting")

    login_dlg = LoginDialog()
    if login_dlg.exec():
        user = login_dlg.user
        window = MainWindow(user)
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
