import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QMessageBox, QCheckBox
)
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QHeaderView
from PyQt6.QtCore import QPropertyAnimation
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from windows.books.book_dialog import BookDialog
from user_session.current_user import CurrentUser

from config.config import API_URL
    
def safe_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

class BooksTab(QWidget):
    def __init__(self):
        super().__init__()
        self.page = 1
        self.page_size = 15
        self.total_pages = 1
        self.user= CurrentUser()

        self.api_url = API_URL + "/books"

        self.init_ui()
        
    def showEvent(self, event):
        super().showEvent(event)
        self.load_books()

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
        layout = QVBoxLayout(self)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Пошук за назвою або автором")
        self.btn_search = QPushButton("Пошук")
        self.btn_clear = QPushButton("Скинути")
        self.btn_search.clicked.connect(self.perform_search)
        self.btn_clear.clicked.connect(self.clear_search)

        self.available_only = QCheckBox("Лише наявні книги")
        self.available_only.setToolTip("Показати лише книги, які є в наявності")
        self.available_only.setStyleSheet("""
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
        self.available_only.stateChanged.connect(self.perform_search)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.btn_search)
        search_layout.addWidget(self.btn_clear)
        search_layout.addWidget(self.available_only)

        layout.addLayout(search_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Назва", "Автор", "Рік", "Видавець", "Місцезнаходження", "В наявності"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Додати книгу")
        edit_btn = QPushButton("Редагувати")
        delete_btn = QPushButton("Видалити")

        add_btn.clicked.connect(self.add_book)
        edit_btn.clicked.connect(self.edit_book)
        delete_btn.clicked.connect(self.delete_book)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)
        # Пагінація
        pagination_layout = QHBoxLayout()
        self.prev_btn = QPushButton("Попередня")
        self.next_btn = QPushButton("Наступна")
        self.page_label = QLabel(f"Сторінка {self.page} з {self.total_pages}")
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
        self.page = 1
        self.load_books()

    def clear_search(self):
        self.search_input.clear()
        self.page = 1
        self.load_books()

    def on_prev_page(self):
        if self.page > 1:
            self.page -= 1
            self.load_books()

    def on_next_page(self):
        if self.page < self.total_pages:
            self.page += 1
            self.load_books()

    
    def update_pagination(self, total_pages, page):
        self.total_pages = total_pages
        self.page = page
        self.page_label.setText(f"Сторінка {page} з {total_pages}")
        self.prev_btn.setEnabled(page > 1)
        self.next_btn.setEnabled(page < total_pages)

    def load_books(self):
        params = {
            "search": self.search_input.text(),
            "available_only": self.available_only.isChecked(),
            "page": self.page,
            "page_size": self.page_size
        }
        try:
            self.table.clearContents()
            self.table.setRowCount(0)
            self.table.setColumnCount(7)
            self.table.setHorizontalHeaderLabels([
                "ID", "Назва", "Автор", "Рік", "Видавець", "Місцезнаходження", "В наявності"
            ])
            self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
            self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

            response = requests.get(self.api_url, params=params, headers=self.user.get_auth_header())
            response.raise_for_status()
            data = response.json()

            books = data.get("books", [])
            self.total_pages = data.get("total_pages", 1)
            self.update_pagination(self.total_pages, self.page)

            self.table.setRowCount(len(books))
            for row, book in enumerate(books):
                index_number = (self.page - 1) * self.page_size + row + 1
                self.table.setVerticalHeaderItem(row, QTableWidgetItem(str(index_number)))

                self.table.setItem(row, 0, QTableWidgetItem(str(book["id"])))  # прихований ID
                self.table.setItem(row, 1, QTableWidgetItem(book["title"]))
                self.table.setItem(row, 2, QTableWidgetItem(book["author"]))
                self.table.setItem(row, 3, QTableWidgetItem(str(book["year"])))
                self.table.setItem(row, 4, QTableWidgetItem(book["publisher"] or ""))
                self.table.setItem(row, 5, QTableWidgetItem(book["location"] or ""))
                availability = "Так" if book["available"] else "Ні"
                item = QTableWidgetItem(availability)
                color = QColor("#c8e6c9") if book["available"] else QColor("#ffcdd2")
                item.setBackground(color)
                self.table.setItem(row, 6, item)


            self.table.setColumnHidden(0, True)
            #self.table.resizeColumnsToContents()
            self.table.resizeRowsToContents()
            self.table.verticalHeader().setDefaultSectionSize(35)
            self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
            self.fade_in_widget(self.table)
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити книги: {e}")

    def add_book(self):
        dialog = BookDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                response = requests.post(self.api_url, json=data, headers=self.user.get_auth_header())
                response.raise_for_status()
                QMessageBox.information(self, "Успіх", "Книгу додано.")
                self.load_books()
            except Exception as e:
                QMessageBox.warning(self, "Помилка", f"Не вдалося додати книгу:\n{e}")

    def edit_book(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Увага", "Виберіть книгу для редагування.")
            return
        row = selected_rows[0].row()
        book_id = int(self.table.item(row, 0).text())
        book = {
            "id": book_id,
            "title": self.table.item(row, 1).text(),
            "author": self.table.item(row, 2).text(),
            "year": safe_int(self.table.item(row, 3).text()),
            "publisher": self.table.item(row, 4).text(),
            "location": self.table.item(row, 5).text()
        }

        dialog = BookDialog(self, book=book)
        if dialog.exec():
            data = dialog.get_data()
            try:
                response = requests.put(f"{self.api_url}/{book_id}", json=data, headers=self.user.get_auth_header())
                response.raise_for_status()
                QMessageBox.information(self, "Успіх", "Книгу оновлено.")
                self.load_books()
            except Exception as e:
                QMessageBox.warning(self, "Помилка", f"Не вдалося оновити книгу:\n{e}")

    def delete_book(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Увага", "Оберіть книгу для видалення")
            return

        book_id = int(self.table.item(current_row, 0).text())
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Підтвердження видалення")
        msg_box.setText("Ви впевнені, що хочете видалити цю книгу?")
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
                response = requests.delete(f"{self.api_url}/{book_id}", headers=self.user.get_auth_header())
                if response.status_code == 200:
                    QMessageBox.information(self, "Успіх", "Книгу видалено.")
                    self.load_books()
                else:
                    # Якщо FastAPI повернув помилку, спробуй витягти текст
                    try:
                        error_detail = response.json().get("detail", "Невідома помилка")
                    except Exception:
                        error_detail = response.text  # fallback

                    QMessageBox.warning(self, "Помилка", f"Не вдалося видалити книгу:\n{error_detail}")

            except requests.exceptions.RequestException as e:
                QMessageBox.critical(self, "Помилка", f"Проблема з'єднання:\n{e}")