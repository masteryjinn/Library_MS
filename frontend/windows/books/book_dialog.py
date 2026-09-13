from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox
)
import datetime

class BookDialog(QDialog):
    def __init__(self, parent=None, book=None):
        super().__init__(parent)
        self.setWindowTitle("Редагувати книгу" if book else "Додати книгу")
        self.setMinimumSize(420, 300)  

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Поля вводу
        self.title_input = QLineEdit()
        self.author_input = QLineEdit()
        self.year_input = QLineEdit()
        self.publisher_input = QLineEdit()
        self.location_input = QLineEdit()

        layout.addLayout(self._create_row("Назва:", self.title_input))
        layout.addLayout(self._create_row("Автор:", self.author_input))
        layout.addLayout(self._create_row("Рік видання:", self.year_input))
        layout.addLayout(self._create_row("Видавець:", self.publisher_input))
        layout.addLayout(self._create_row("Місцезнаходження:", self.location_input))

        if book:
            self.title_input.setText(book["title"])
            self.author_input.setText(book["author"])
            self.year_input.setText(str(book["year"]))
            self.publisher_input.setText(book["publisher"])
            self.location_input.setText(book["location"])

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

        self.btn_save.clicked.connect(self.validate)
        self.btn_cancel.clicked.connect(self.reject)

        # Стилі (такі ж як у ReaderDialog)
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
        label.setFixedWidth(140)
        layout.addWidget(label)
        layout.addWidget(widget)
        return layout

    def validate(self):
        year_text = self.year_input.text().strip()
        current_year = datetime.datetime.now().year

        if year_text:
            if not year_text.isdigit():
                QMessageBox.warning(self, "Помилка", "Рік видання має містити лише цифри.")
                return
            year = int(year_text)
            if year > current_year:
                QMessageBox.warning(self, "Помилка", f"Рік видання не може бути більшим за {current_year}.")
                return

        # Перевірка обов’язкових полів
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Помилка", "Назва книги обов'язкова.")
            return
        if not self.author_input.text().strip():
            QMessageBox.warning(self, "Помилка", "Автор обов'язковий.")
            return
        if not self.location_input.text().strip():
            QMessageBox.warning(self, "Помилка", "Місцезнаходження обов'язкове.")
            return

        self.accept()

    def get_data(self):
        year_text = self.year_input.text().strip()
        return {
            "title": self.title_input.text().strip(),
            "author": self.author_input.text().strip(),
            "year": int(year_text) if year_text else None,
            "publisher": self.publisher_input.text().strip(),
            "location": self.location_input.text().strip()
        }
