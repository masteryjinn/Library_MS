from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox
)
import requests
import re
from user_session.current_user import CurrentUser

class ReaderDialog(QDialog):
    def __init__(self, api_url, reader=None, parent=None):
        super().__init__(parent)
        self.api_url = api_url
        self.reader = reader  
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Редагувати читача" if self.reader else "Додати читача")
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Поля введення
        self.first_name_input = QLineEdit()
        self.last_name_input = QLineEdit()
        self.email_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.address_input = QLineEdit()

        # Маска та поведінка поля телефону
        self.phone_input.setInputMask("+380999999999;_")
        self.phone_input.focusInEvent = self.phone_focus_in
        self.phone_input.focusOutEvent = self.phone_focus_out

        layout.addLayout(self._create_row("Ім'я:", self.first_name_input))
        layout.addLayout(self._create_row("Прізвище:", self.last_name_input))
        layout.addLayout(self._create_row("Email:", self.email_input))
        layout.addLayout(self._create_row("Телефон:", self.phone_input))
        layout.addLayout(self._create_row("Адреса:", self.address_input))

        if self.reader:
            self.first_name_input.setText(self.reader.get("first_name", ""))
            self.last_name_input.setText(self.reader.get("last_name", ""))
            self.email_input.setText(self.reader.get("email", ""))
            self.phone_input.setText(self.reader.get("phone", ""))
            self.address_input.setText(self.reader.get("address", ""))

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_save = QPushButton("Зберегти")
        self.btn_cancel = QPushButton("Відміна")

        self.btn_save.setFixedHeight(32)
        self.btn_cancel.setFixedHeight(32)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)

        layout.addStretch()
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        self.btn_save.clicked.connect(self.on_save)
        self.btn_cancel.clicked.connect(self.reject)

        # Стилізація
        self.setStyleSheet("""
            QLabel {
                font-size: 14px;
            }
            QLineEdit {
                font-size: 14px;
                padding: 4px;
            }
            QPushButton {
                font-size: 14px;
                padding: 6px 16px;
            }
        """)

    def _create_row(self, label_text, widget):
        layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setFixedWidth(80)
        layout.addWidget(label)
        layout.addWidget(widget)
        return layout

    def phone_focus_in(self, event):
        text = self.phone_input.text()
        if not text.startswith("+38"):
            self.phone_input.setText("+380")
        QLineEdit.focusInEvent(self.phone_input, event)

    def phone_focus_out(self, event):
        text = self.phone_input.text().strip()
        if text == "+380" or not text.replace("+", "").isdigit():
            self.phone_input.clear()
        QLineEdit.focusOutEvent(self.phone_input, event)

    def on_save(self):
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        email = self.email_input.text().strip()
        phone = self.phone_input.text().strip()
        address = self.address_input.text().strip()

    # Обов’язкові поля: ім'я, прізвище, телефон, адреса
        if not first_name or not last_name:
            QMessageBox.warning(self, "Помилка", "Ім'я і прізвище обов'язкові")
            return

        if not phone:
            QMessageBox.warning(self, "Помилка", "Телефон обов'язковий")
            return

        if not phone.startswith("+380") or len(phone) != 13 or not phone[1:].isdigit():
            QMessageBox.warning(self, "Помилка", "Телефон має починатися з +380 та містити 9 цифр після коду")
            return

        if not address:
            QMessageBox.warning(self, "Помилка", "Адреса обов'язкова")
            return
        
        if email:
            email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
            if not re.match(email_pattern, email):
                QMessageBox.warning(self, "Помилка", "Невірний формат email")
                return

        data = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "address": address,
        }

        try:
            if self.reader:
                reader_id = self.reader.get("id")
                response = requests.put(f"{self.api_url}/{reader_id}", json=data, headers=CurrentUser().get_auth_header())
            else:
                response = requests.post(self.api_url, json=data, headers=CurrentUser().get_auth_header())

            if response.status_code in (200, 201):
                QMessageBox.information(self, "Успіх", "Дані збережено")
                self.accept()
            else:
                QMessageBox.warning(self, "Помилка", f"Не вдалося зберегти: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Сталася помилка: {e}")
