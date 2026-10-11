from datetime import datetime
from pathlib import Path
from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QDateEdit,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from reports.services import generate_report


class ReportsWidget(QWidget):
    """Вкладка генерації звітів системи в Excel та PDF."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # 1. Вибір типу звіту
        type_group = QGroupBox("1. Оберіть тип звіту")
        type_layout = QVBoxLayout(type_group)

        self.rb_stock = QRadioButton("📦 Залишки автозапчастин на складі (з відміткою дефіциту)")
        self.rb_stock.setChecked(True)
        self.rb_stock.toggled.connect(self._on_type_changed)

        self.rb_movement = QRadioButton("🔄 Рух товарів за період (прихід і розхід по накладних)")
        self.rb_movement.toggled.connect(self._on_type_changed)

        self.rb_counterparties = QRadioButton("🤝 Обороти по контрагентах (поставки від постачальників та продажі клієнтам)")
        self.rb_counterparties.toggled.connect(self._on_type_changed)

        type_layout.addWidget(self.rb_stock)
        type_layout.addWidget(self.rb_movement)
        type_layout.addWidget(self.rb_counterparties)
        layout.addWidget(type_group)

        # 2. Період дат (активний для звіту руху)
        self.period_group = QGroupBox("2. Період формування звіту")
        period_layout = QFormLayout(self.period_group)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())

        period_layout.addRow("Початкова дата (з):", self.date_from)
        period_layout.addRow("Кінцева дата (по):", self.date_to)
        self.period_group.setEnabled(False)  # За замовчуванням вимкнено для залишків
        layout.addWidget(self.period_group)

        # 3. Вибір формату
        format_group = QGroupBox("3. Формат експорту")
        format_layout = QHBoxLayout(format_group)

        self.rb_excel = QRadioButton("📊 Microsoft Excel (.xlsx)")
        self.rb_excel.setChecked(True)
        self.rb_pdf = QRadioButton("📄 Документ PDF (.pdf)")

        format_layout.addWidget(self.rb_excel)
        format_layout.addWidget(self.rb_pdf)
        format_layout.addStretch()
        layout.addWidget(format_group)

        # 4. Кнопка формування звіту
        action_layout = QHBoxLayout()
        self.generate_btn = QPushButton("🚀 Сформувати та експортувати звіт...")
        self.generate_btn.setStyleSheet(
            "font-size: 14px; font-weight: bold; padding: 10px 20px; background-color: #1F497D; color: white;"
        )
        self.generate_btn.clicked.connect(self._generate_report)

        action_layout.addWidget(self.generate_btn)
        action_layout.addStretch()
        layout.addLayout(action_layout)

        layout.addStretch()

    def _on_type_changed(self) -> None:
        """Активація вибору дат лише для звіту руху."""
        self.period_group.setEnabled(self.rb_movement.isChecked())

    def _generate_report(self) -> None:
        today_str = datetime.now().strftime("%Y%m%d")
        ext = ".xlsx" if self.rb_excel.isChecked() else ".pdf"
        filter_str = "Excel Files (*.xlsx)" if self.rb_excel.isChecked() else "PDF Files (*.pdf)"
        fmt = "excel" if self.rb_excel.isChecked() else "pdf"

        if self.rb_stock.isChecked():
            report_type = "stock"
            default_name = f"zvit_zalyshky_{today_str}{ext}"
        elif self.rb_movement.isChecked():
            report_type = "movement"
            default_name = f"zvit_rukh_tovariv_{today_str}{ext}"
        else:
            report_type = "counterparties"
            default_name = f"zvit_kontragenty_{today_str}{ext}"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Зберегти звіт",
            str(Path.home() / default_name),
            filter_str,
        )

        if not file_path:
            return

        date_from_str = self.date_from.date().toString("yyyy-MM-dd 00:00:00")
        date_to_str = self.date_to.date().toString("yyyy-MM-dd 23:59:59")

        try:
            saved_file = generate_report(
                report_type=report_type,
                export_format=fmt,
                output_path=file_path,
                date_from=date_from_str if self.rb_movement.isChecked() else None,
                date_to=date_to_str if self.rb_movement.isChecked() else None,
            )

            QMessageBox.information(
                self,
                "Звіт успішно створено",
                f"Звіт збережено у файл:\n{saved_file}",
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Помилка створення звіту",
                f"Не вдалося сформувати звіт:\n{str(e)}",
            )
