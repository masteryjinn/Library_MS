from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt

class PasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Введіть пароль")
        self.setFixedSize(300, 180)
        self.setup_ui()
        self.password = None

    def setup_ui(self):
        layout = QVBoxLayout(self)

        label = QLabel("Будь ласка, введіть пароль для \nпідтвердження видалення:")
        label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50;")
        layout.addWidget(label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Пароль")
        layout.addWidget(self.password_input)

        self.show_password_checkbox = QCheckBox("Показати пароль")
        self.show_password_checkbox.stateChanged.connect(self.toggle_password_visibility)
        self.show_password_checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #3498db;
                border-radius: 4px;
                background-color: #fff;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border: 2px solid #2980b9;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #2980b9;
                background-color: #ecf6fc;
            }
        """)
        layout.addWidget(self.show_password_checkbox)

        self.confirm_button = QPushButton("Підтвердити")
        self.confirm_button.clicked.connect(self.on_confirm)
        self.confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                padding: 6px 12px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #d0d3d4;
            }
        """)
        layout.addWidget(self.confirm_button, alignment=Qt.AlignmentFlag.AlignCenter)

    def toggle_password_visibility(self):
        if self.show_password_checkbox.isChecked():
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.password_input.setStyleSheet("color: #2c3e50;")
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

    def on_confirm(self):
        entered_password = self.password_input.text().strip()
        print(f"Entered password: {entered_password}")
        if not entered_password:
            QMessageBox.warning(self, "Помилка", "Пароль не може бути порожнім.")
            return
        self.password = entered_password
        self.accept()
