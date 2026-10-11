from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from models.user import User
from services.auth_service import authenticate_user


class LoginDialog(QDialog):
    """Діалогове вікно авторизації користувача."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Вхід до системи обліку")
        self.setFixedSize(360, 220)
        self.user: Optional[User] = None

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Заголовок
        title_label = QLabel("Авторизація в системі")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title_label.font()
        font.setPointSize(14)
        font.setBold(True)
        title_label.setFont(font)
        layout.addWidget(title_label)

        # Форма введення
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Введіть логін (напр. admin або keeper)")
        self.username_input.setText("admin")  # Зручно для курсової

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Введіть пароль")
        self.password_input.setText("admin123")  # За замовчуванням для демонстрації

        form_layout.addRow("Логін:", self.username_input)
        form_layout.addRow("Пароль:", self.password_input)
        layout.addLayout(form_layout)

        # Кнопки
        btn_layout = QHBoxLayout()
        self.login_btn = QPushButton("Увійти")
        self.login_btn.setDefault(True)
        self.login_btn.clicked.connect(self._handle_login)

        self.cancel_btn = QPushButton("Вийти")
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.login_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def _handle_login(self) -> None:
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Помилка", "Будь ласка, заповніть логін та пароль.")
            return

        user = authenticate_user(username, password)
        if not user:
            QMessageBox.critical(
                self,
                "Помилка входу",
                "Невірний логін або пароль. Перевірте введені дані.",
            )
            return

        self.user = user
        self.accept()
