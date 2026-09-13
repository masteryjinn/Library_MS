from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QPushButton, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from user_session.current_user import CurrentUser
from config.config import API_URL

class SelectReaderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Обрати читача")
        self.setMinimumSize(600, 450)

        self.selected = None

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Пошук за ПІБ або телефоном...")
        self.search_input.textChanged.connect(self.update_table)

        # Таблиця замість списку
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Прізвище", "Ім’я", "Телефон"])
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

        self.readers = self.fetch_eligible_readers()
        self.update_table()

    def fetch_eligible_readers(self):
        import requests
        try:
            response = requests.get(f"{API_URL}/readers/eligible", headers=CurrentUser().get_auth_header())
            response.raise_for_status()
            data = response.json()
            return data.get("readers", [])
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити читачів: {e}")
            return []

    def update_table(self):
        search = self.search_input.text().lower()
        filtered_readers = []

        for reader in self.readers:
            full_name = f"{reader['last_name']} {reader['first_name']}"
            phone = reader.get("phone", "")
            if search in full_name.lower() or search in phone.lower():
                filtered_readers.append(reader)

        self.table.setRowCount(len(filtered_readers))

        for row, reader in enumerate(filtered_readers):
            last_name_item = QTableWidgetItem(reader["last_name"])
            first_name_item = QTableWidgetItem(reader["first_name"])
            phone_item = QTableWidgetItem(reader.get("phone", "—"))

            for item in [last_name_item, first_name_item, phone_item]:
                item.setFont(QFont("Arial", 11))

            self.table.setItem(row, 0, last_name_item)
            self.table.setItem(row, 1, first_name_item)
            self.table.setItem(row, 2, phone_item)

            # Зберігаємо читача як data в один з item'ів
            last_name_item.setData(Qt.ItemDataRole.UserRole, reader)

    def accept_selection(self):
        selected_items = self.table.selectedItems()
        if selected_items:
            reader = selected_items[0].data(Qt.ItemDataRole.UserRole)
            self.selected = reader
            self.accept()
        else:
            QMessageBox.warning(self, "Увага", "Будь ласка, оберіть читача.")

    def get_selected(self):
        return self.selected
