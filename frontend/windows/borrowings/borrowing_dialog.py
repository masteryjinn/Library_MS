from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtCore import QDateTime
from windows.books.select_book_dialog import SelectBookDialog
from windows.readers.select_reader_dialog import SelectReaderDialog
from utils.datatime import format_date

class LoanDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Нове позичання")
        self.setMinimumSize(460, 200)

        self.selected_book = None
        self.selected_reader = None

        self.book_line = QLineEdit()
        self.book_line.setReadOnly(True)

        self.reader_line = QLineEdit()
        self.reader_line.setReadOnly(True)

        self.start_date_label = QLabel(format_date(QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")))

        # Кнопки вибору
        self.btn_choose_book = QPushButton("Обрати книгу")
        self.btn_choose_reader = QPushButton("Обрати читача")

        self.btn_choose_book.clicked.connect(self.choose_book)
        self.btn_choose_reader.clicked.connect(self.choose_reader)

        # Layout
        layout = QVBoxLayout()
        layout.addLayout(self._row("Книга:", self.book_line, self.btn_choose_book))
        layout.addLayout(self._row("Читач:", self.reader_line, self.btn_choose_reader))
        layout.addLayout(self._row("Дата початку:", self.start_date_label))

        # Кнопки
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Зберегти")
        self.btn_cancel = QPushButton("Скасувати")
        self.btn_save.clicked.connect(self.validate)
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)

        layout.addStretch()
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _row(self, label_text, widget, button=None):
        layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setFixedWidth(120)
        layout.addWidget(label)
        layout.addWidget(widget)
        if button:
            layout.addWidget(button)
        return layout

    def choose_book(self):
        dialog = SelectBookDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.selected_book = dialog.get_selected()
            self.book_line.setText(self.selected_book['title'])

    def choose_reader(self):
        dialog = SelectReaderDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.selected_reader = dialog.get_selected()
            full_name = f"{self.selected_reader['last_name']} {self.selected_reader['first_name']}"
            self.reader_line.setText(full_name)

    def validate(self):
        if not self.selected_book or not self.selected_reader:
            QMessageBox.warning(self, "Помилка", "Будь ласка, оберіть і книгу, і читача.")
            return

        self.accept()

    def get_data(self):
        return {
            "book_id": self.selected_book["id"],
            "reader_id": self.selected_reader["id"],
            "borrow_date": QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss"),
        }
