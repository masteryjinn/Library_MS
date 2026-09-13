import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QMessageBox, QCheckBox, QDialog
)
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QHeaderView
from PyQt6.QtCore import QPropertyAnimation, Qt, QDateTime
from PyQt6.QtGui import QColor
from windows.borrowings.borrowing_dialog import LoanDialog
from windows.password.password_dialog import PasswordDialog
from utils.datatime import format_date
from user_session.current_user import CurrentUser
from config.config import API_URL


def safe_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


class BorrowingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.page = 1
        self.page_size = 15
        self.total_pages = 1

        self.api_url = API_URL + "/borrowings"
        self.user = CurrentUser()

        self.init_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_borrowings()

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
        self.search_input.setPlaceholderText("Пошук за іменем або назвою книги")
        self.btn_search = QPushButton("Пошук")
        self.btn_clear = QPushButton("Скинути")
        self.btn_search.clicked.connect(self.perform_search)
        self.btn_clear.clicked.connect(self.clear_search)

        self.active_only = QCheckBox("Лише активні")
        self.active_only.setToolTip("Показати лише активні позичання (без дати повернення)")
        self.active_only.setStyleSheet("""
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
        self.active_only.stateChanged.connect(self.perform_search)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.btn_search)
        search_layout.addWidget(self.btn_clear)
        search_layout.addWidget(self.active_only)

        layout.addLayout(search_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Читач", "Книга", "Дата позички", "Дата повернення", "Стан"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Додати позичання")
        edit_btn = QPushButton("Зафіксувати повернення")
        delete_btn = QPushButton("Видалити")

        add_btn.clicked.connect(self.add_borrowing)
        edit_btn.clicked.connect(self.edit_borrowing)
        delete_btn.clicked.connect(self.delete_borrowing)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)

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
        animation.setDuration(500)
        animation.setStartValue(0)
        animation.setEndValue(1)
        animation.start()
        widget._animation = animation

    def perform_search(self):
        self.page = 1
        self.load_borrowings()

    def clear_search(self):
        self.search_input.clear()
        self.page = 1
        self.load_borrowings()

    def on_prev_page(self):
        if self.page > 1:
            self.page -= 1
            self.load_borrowings()

    def on_next_page(self):
        if self.page < self.total_pages:
            self.page += 1
            self.load_borrowings()

    def update_pagination(self, total_pages, current_page):
        self.total_pages = total_pages
        self.page = current_page
        self.page_label.setText(f"Сторінка {current_page} з {total_pages}")
        self.prev_btn.setEnabled(current_page > 1)
        self.next_btn.setEnabled(current_page < total_pages)

    def load_borrowings(self):
        params = {
            "search": self.search_input.text(),
            "active_only": self.active_only.isChecked(),
            "page": self.page,
            "page_size": self.page_size
        }
        try:
            self.table.clearContents()
            self.table.setRowCount(0)
            self.table.setColumnCount(6)
            self.table.setHorizontalHeaderLabels([
                "ID", "Читач", "Книга", "Дата позички", "Дата повернення", "Стан"
            ])
            self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
            self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            response = requests.get(self.api_url, params=params, headers=self.user.get_auth_header())
            response.raise_for_status()
            data = response.json()

            borrowings = data.get("borrowings", [])
            self.total_pages = data.get("total_pages", 1)
            self.update_pagination(self.total_pages, self.page)

            self.table.setRowCount(len(borrowings))
            for row, b in enumerate(borrowings):
                index_number = (self.page - 1) * self.page_size + row + 1
                self.table.setVerticalHeaderItem(row, QTableWidgetItem(str(index_number)))

                self.table.setItem(row, 0, QTableWidgetItem(str(b["id"])))
                self.table.setItem(row, 1, QTableWidgetItem(b["reader_name"]))
                self.table.setItem(row, 2, QTableWidgetItem(b["book_title"]))
                self.table.setItem(row, 3, QTableWidgetItem(format_date(b["borrow_date"])))
                self.table.setItem(row, 4, QTableWidgetItem(format_date(b["return_date"])))
                state_item = QTableWidgetItem("Активне" if not b["return_date"] else "Повернено")
                state_item.setBackground(QColor("#c8e6c9") if b["return_date"] else QColor("#ffecb3"))
                self.table.setItem(row, 5, state_item)

            self.table.setColumnHidden(0, True)
            self.table.resizeRowsToContents()
            self.table.verticalHeader().setDefaultSectionSize(35)
            self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
            self.fade_in_widget(self.table)
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити позичання: {e}")

    def add_borrowing(self):
        dialog = LoanDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                response = requests.post(self.api_url, json=data, headers=self.user.get_auth_header())
                response.raise_for_status()
                QMessageBox.information(self, "Успіх", "Позичання додано.")
                self.load_borrowings()
            except Exception as e:
                QMessageBox.warning(self, "Помилка", f"Не вдалося додати позичання:\n{e}")

    def edit_borrowing(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Увага", "Виберіть позичання для зафіксування повернення.")
            return

        row = selected_rows[0].row()
        borrowing_id = int(self.table.item(row, 0).text())
        reader_name = self.table.item(row, 1).text()
        book_title = self.table.item(row, 2).text()
        return_date = self.table.item(row, 4).text()

        if return_date:
            QMessageBox.information(self, "Інформація", "Це позичання вже повернене.")
            return
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Підтвердження")
        msg_box.setText(f"Зафіксувати повернення книги '{book_title}' читачем {reader_name}?")
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
            # Поточна дата і час
            return_datetime = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")

            try:
                response = requests.put(
                    f"{self.api_url}/return/{borrowing_id}",
                    json={"return_date": return_datetime},
                    headers=self.user.get_auth_header()
                )
                response.raise_for_status()
                QMessageBox.information(self, "Успіх", "Повернення зафіксовано.")
                self.load_borrowings()
            except Exception as e:
                QMessageBox.warning(self, "Помилка", f"Не вдалося зафіксувати повернення:\n{e}")

    def delete_borrowing(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Увага", "Оберіть запис для видалення")
            return

        borrowing_id = int(self.table.item(current_row, 0).text())

        # Виклик діалогу для введення пароля
        pwd_dialog = PasswordDialog(self)
        if pwd_dialog.exec() == QDialog.DialogCode.Accepted:
            entered_password = pwd_dialog.password

            # Тут можна відправити пароль на бекенд для перевірки
            try:
                # Приклад запиту для перевірки пароля
                auth_response = requests.post(
                    f"{self.api_url}/check-password",
                    json={"password": entered_password},
                    headers=self.user.get_auth_header()
                )
                if auth_response.status_code != 200:
                    QMessageBox.warning(self, "Помилка", "Неправильний пароль.")
                    return

                # Якщо пароль правильний — підтверджуємо видалення
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Підтвердження видалення")
                msg_box.setText("Ви впевнені, що хочете видалити цей запис?")
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
                        res = requests.delete(f"{self.api_url}/{borrowing_id}", headers=self.user.get_auth_header())
                        if res.status_code == 200:
                            QMessageBox.information(self, "Успіх", "Запис видалено")
                            self.load_borrowings()
                        else:
                            QMessageBox.warning(self, "Помилка", "Не вдалося видалити запис")
                    except Exception as e:
                        QMessageBox.critical(self, "Помилка", f"Не вдалося видалити: {e}")

            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Сталася помилка при перевірці пароля: {e}")