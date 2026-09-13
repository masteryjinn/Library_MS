import requests
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QPushButton, QMessageBox, QHeaderView
)

from config.config import API_URL
from user_session.current_user import CurrentUser


class SelectBookDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Обрати книгу")
        self.setMinimumSize(600, 450)

        self.selected = None

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Пошук за назвою, автором або видавництвом...")
        self.search_input.textChanged.connect(self.update_table)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Назва", "Автор", "Видавництво"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.doubleClicked.connect(self.accept_selection)

        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        btn = QPushButton("Обрати")
        btn.clicked.connect(self.accept_selection)

        layout = QVBoxLayout()
        layout.addWidget(self.search_input)
        layout.addWidget(self.table)
        layout.addWidget(btn)

        self.setLayout(layout)

        self.books = self.fetch_available_books()
        self.update_table()

    def fetch_available_books(self):
        try:
            response = requests.get(
                f"{API_URL}/books/available", 
                headers=CurrentUser().get_auth_header()
            )
            response.raise_for_status()
            
            # Ендпоінт /books/available повертає список книг напряму [{}, {}]
            data = response.json()
            
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "books" in data:
                # На випадок, якщо бекенд колись буде змінено на {"books": [...]}
                return data["books"]
            else:
                QMessageBox.critical(self, "Помилка", "Невірний формат даних від сервера.")
                return []
                
        except requests.RequestException as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити дані: {e}")
            return []

    def update_table(self):
        search = self.search_input.text().lower().strip()
        filtered_books = []

        for book in self.books:
            title = str(book.get("title", ""))
            author = str(book.get("author", ""))
            publisher = str(book.get("publisher", ""))
            
            if search in title.lower() or search in author.lower() or search in publisher.lower():
                filtered_books.append(book)

        self.table.setRowCount(len(filtered_books))

        for row, book in enumerate(filtered_books):
            title_item = QTableWidgetItem(str(book.get("title", "")))
            author_item = QTableWidgetItem(str(book.get("author", "")))
            publisher_item = QTableWidgetItem(str(book.get("publisher", "")))

            for item in [title_item, author_item, publisher_item]:
                item.setFont(QFont("Arial", 11))

            self.table.setItem(row, 0, title_item)
            self.table.setItem(row, 1, author_item)
            self.table.setItem(row, 2, publisher_item)

            # Зберігаємо об'єкт книги у DataRole першої комірки рядка
            title_item.setData(Qt.ItemDataRole.UserRole, book)

    def accept_selection(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            title_item = self.table.item(row, 0)
            if title_item:
                self.selected = title_item.data(Qt.ItemDataRole.UserRole)
                self.accept()
                return
        
        QMessageBox.warning(self, "Увага", "Будь ласка, оберіть книгу зі списку.")

    def get_selected(self):
        return self.selected