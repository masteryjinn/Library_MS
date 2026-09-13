from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QMessageBox
)
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QHeaderView
from PyQt6.QtCore import QPropertyAnimation
from PyQt6.QtCore import Qt
import requests
from windows.readers.reader_dialog import ReaderDialog
from user_session.current_user import CurrentUser
from config.config import API_URL

class ReadersTab(QWidget):
    def __init__(self):
        super().__init__()
        self.user = CurrentUser()
        self.current_page = 1
        self.items_per_page = 15
        self.total_pages = 1
        self.api_url = API_URL + "/readers"
        self.init_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_readers()

    def init_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                color: #2c3e50;
                font-size: 14px;
            }

            QLineEdit {
                background-color: #f5f5f5;
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                color: #2c3e50;
            }

            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #2980b9;
            }

            QPushButton:disabled {
                background-color: #bdc3c7;
            }

            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f9f9f9;
                gridline-color: #dcdcdc;
                color: #2c3e50;
            }
            QTableWidget::item:selected {
                background-color: #d6eaf8;
                color: #1c2833;
            }
            QHeaderView::section {
                background-color: #ecf0f1;
                color: #2c3e50;
                font-weight: bold;
                padding: 6px;
                border: 1px solid #dcdcdc;
            }

            QLabel {
                font-weight: bold;
            }
        """)
        layout = QVBoxLayout()

        # Панель пошуку
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Пошук за ім'ям чи прізвищем...")
        self.btn_search = QPushButton("Пошук")
        self.btn_clear = QPushButton("Скинути")

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.btn_search)
        search_layout.addWidget(self.btn_clear)

        self.btn_search.clicked.connect(self.perform_search)
        self.btn_clear.clicked.connect(self.clear_search)

        # Таблиця читачів
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(['ID', 'Ім’я', 'Прізвище', 'Email', 'Телефон', 'Адреса', 'Кількість книг'])
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)


        layout.addLayout(search_layout)
        layout.addWidget(self.table)

        # Кнопки дій
        button_layout = QHBoxLayout()
        self.add_btn = QPushButton("Додати")
        self.edit_btn = QPushButton("Редагувати")
        self.delete_btn = QPushButton("Видалити")

        self.add_btn.clicked.connect(self.add_reader)
        self.edit_btn.clicked.connect(self.edit_reader)
        self.delete_btn.clicked.connect(self.delete_reader)

        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        layout.addLayout(button_layout)

        # Пагінація
        pagination_layout = QHBoxLayout()
        self.prev_btn = QPushButton("Попередня")
        self.next_btn = QPushButton("Наступна")
        self.page_label = QLabel(f"Сторінка {self.current_page} з {self.total_pages}")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.prev_btn.clicked.connect(self.on_prev_page)
        self.next_btn.clicked.connect(self.on_next_page)

        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_btn)

        layout.addLayout(pagination_layout)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        self.setLayout(layout)

    def fade_in_widget(self, widget):
        effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(effect)
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(500)  # 0.5 секунди анімації
        animation.setStartValue(0)
        animation.setEndValue(1)
        animation.start()
        # Збережемо анімацію, щоб вона не зникла (важливо)
        widget._animation = animation

    def perform_search(self):
        self.current_page = 1
        self.load_readers()

    def clear_search(self):
        self.search_input.clear()
        self.current_page = 1
        self.load_readers()

    def on_prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_readers()

    def on_next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_readers()

    def update_pagination(self, total_pages, current_page):
        self.total_pages = total_pages
        self.current_page = current_page
        self.page_label.setText(f"Сторінка {current_page} з {total_pages}")
        self.prev_btn.setEnabled(current_page > 1)
        self.next_btn.setEnabled(current_page < total_pages)

    def load_readers(self):
        try:
            self.table.clearContents()
            self.table.setRowCount(0)
            self.table.setColumnCount(7)
            self.table.setHorizontalHeaderLabels(['ID', 'Ім’я', 'Прізвище', 'Email', 'Телефон', 'Адреса', 'Кількість книг'])
            self.table.setSortingEnabled(True)
            self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
            self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

            params = {
                "page": self.current_page,
                "limit": self.items_per_page,
                "search": self.search_input.text(),
            }

            response = requests.get(self.api_url, params=params, headers=self.user.get_auth_header())

            if response.status_code != 200:
                QMessageBox.warning(self, "Помилка", "Не вдалося отримати список читачів")
                return
            
            data = response.json()
            readers = data.get("data", [])
            total_pages = data.get("total_pages", 1)
            current_page = data.get("current_page", 1)

            self.update_pagination(total_pages, current_page)

            self.table.setRowCount(len(readers))
            for row, reader in enumerate(readers):
                index_number = (self.current_page - 1) * self.items_per_page + row + 1
                self.table.setVerticalHeaderItem(row, QTableWidgetItem(str(index_number)))
                self.table.setItem(row, 0, QTableWidgetItem(str(reader["id"])))
                self.table.setItem(row, 1, QTableWidgetItem(reader["first_name"]))
                self.table.setItem(row, 2, QTableWidgetItem(reader["last_name"]))
                self.table.setItem(row, 3, QTableWidgetItem(reader.get("email", "")))
                self.table.setItem(row, 4, QTableWidgetItem(reader.get("phone", ""))) 
                self.table.setItem(row, 5, QTableWidgetItem(reader.get("address", ""))) 
                self.table.setItem(row, 6, QTableWidgetItem(str(reader.get("book_count", 0))))

            self.table.setColumnHidden(0, True)
            #self.table.resizeColumnsToContents()
            self.table.resizeRowsToContents()
            self.table.verticalHeader().setDefaultSectionSize(35)
            self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
            self.fade_in_widget(self.table)
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити дані: {e}")

    def add_reader(self):
        dlg = ReaderDialog(self.api_url, parent=self)
        if dlg.exec():
            self.load_readers()

    def edit_reader(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Увага", "Оберіть читача для редагування")
            return

        reader_id = int(self.table.item(current_row, 0).text())
        reader_data = {
            "id": reader_id,
            "first_name": self.table.item(current_row, 1).text(),
            "last_name": self.table.item(current_row, 2).text(),
            "email": self.table.item(current_row, 3).text(),
            "phone": self.table.item(current_row, 4).text(),
            "address": self.table.item(current_row, 5).text(),
        }

        dlg = ReaderDialog(self.api_url, reader=reader_data, parent=self)
        if dlg.exec():
            self.load_readers()


    def delete_reader(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Увага", "Оберіть читача для видалення")
            return

        reader_id = int(self.table.item(current_row, 0).text())
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Підтвердження видалення")
        msg_box.setText("Ви впевнені, що хочете видалити цього читача?")
        msg_box.setIcon(QMessageBox.Icon.Question)

        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #ffffff;
            }
            QLabel {
                color: #2c3e50;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton {
                background-color: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                padding: 6px 12px;
                font-size: 14px;
                font-weight: bold;
                min-width: 80px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #d0d3d4;
            }
        """)

        yes_button = msg_box.addButton("Так", QMessageBox.ButtonRole.YesRole)
        no_button = msg_box.addButton("Ні", QMessageBox.ButtonRole.NoRole)

        msg_box.exec()
        if msg_box.clickedButton() == yes_button:
            try:
                response = requests.delete(f"{self.api_url}/{reader_id}", headers=self.user.get_auth_header())
                if response.status_code == 200:
                    QMessageBox.information(self, "Успіх", "Читача видалено.")
                    self.load_readers()
                else:
                    # Якщо FastAPI повернув помилку, спробуй витягти текст
                    try:
                        error_detail = response.json().get("detail", "Невідома помилка")
                    except Exception:
                        error_detail = response.text  # fallback

                    QMessageBox.warning(self, "Помилка", f"Не вдалося видалити читача:\n{error_detail}")

            except requests.exceptions.RequestException as e:
                QMessageBox.critical(self, "Помилка", f"Проблема з'єднання:\n{e}")
