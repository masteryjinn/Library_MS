from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QStackedWidget,
    QListWidgetItem, QToolButton, QPushButton, QSizePolicy, QMessageBox
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QSize
from .reader_tab import ReadersTab
from .books_tab import BooksTab
from .borrowing_tab import BorrowingsTab
from .analytics_tab import AnalyticsTab

from user_session.current_user import CurrentUser

TOOLTIP_MAP = {
    "📚 Книги": "Управління каталогом книг бібліотеки",
    "👤 Читачі": "Список читачів і їх інформація",
    "📅 Позичання": "Облік позичання та повернення книг",
    "📈 Аналітика": "Статистика користування бібліотекою"
}

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Головне вікно")
        self.showFullScreen()

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === ЛІВА ПАНЕЛЬ (МЕНЮ) ===
        self.menu_list = QListWidget()
        self.menu_list.setFixedWidth(250)
        self.menu_list.setStyleSheet("""
            QListWidget {
                background-color: #ecf0f1;
                border-right: 2px solid #bdc3c7;
                font-size: 18px;
                font-weight: 600;
            }
            QListWidget::item {
                padding: 18px;
                margin: 5px;
                border-radius: 8px;
                color: #2c3e50;
            }
            QListWidget::item:hover {
                background-color: #d0ece7;
            }
            QListWidget::item:selected {
                background-color: #2ecc71;
                color: white;
                font-weight: bold;
            }
        """)

        self.stack = QStackedWidget()
        self.add_tab("📚 Книги", BooksTab())
        if CurrentUser().get_role() == "librarian":
            self.add_tab("👤 Читачі", ReadersTab())
            self.add_tab("📅 Позичання", BorrowingsTab())
            self.add_tab("📈 Аналітика", AnalyticsTab())

        # === ВЕРХНЯ ПАНЕЛЬ ===
        header = QHBoxLayout()
        self.toggle_menu_button = QToolButton(self)
        self.toggle_menu_button.setIcon(QIcon("frontend/icons/menu_close.png"))
        self.toggle_menu_button.setIconSize(QSize(30, 30))
        self.toggle_menu_button.setStyleSheet("background-color: transparent; border: none;")
        self.toggle_menu_button.clicked.connect(self.toggle_menu)

        app_name_label = QLabel("Бібліотечна система")
        app_name_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        app_name_label.setStyleSheet("color: white; padding-left: 10px;")

        header.addWidget(self.toggle_menu_button)
        header.addWidget(app_name_label)
        header.addStretch()

        # ВІДОБРАЖЕННЯ ІМ'Я КОРИСТУВАЧА
        name = CurrentUser().get_name()
        user_label = QLabel(f"👤 {name}")
        user_label.setFont(QFont("Arial", 14))
        user_label.setStyleSheet("color: white; padding-left: 10px;")
        header.addWidget(user_label)

        # КНОПКА ВИЙТИ
        exit_button = QPushButton("Вийти")
        exit_button.setFixedSize(130, 45)
        exit_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        exit_button.clicked.connect(self.confirm_exit)
        header.addWidget(exit_button)

        top_panel = QWidget()
        top_panel.setLayout(header)
        top_panel.setStyleSheet("background-color: #2980b9; padding: 12px;")

        # === КОНТЕЙНЕР ЗМІСТУ ===
        content_layout = QVBoxLayout()
        content_layout.addWidget(top_panel)
        content_layout.addWidget(self.stack)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.setStretch(0, 1)
        content_layout.setStretch(1, 10)

        stack_container = QWidget()
        stack_container.setLayout(content_layout)
        stack_container.setStyleSheet("background-color: #fdfefe;")

        main_layout.addWidget(self.menu_list)
        main_layout.addWidget(stack_container)

        self.setLayout(main_layout)

        self.stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.menu_list.currentRowChanged.connect(self.stack.setCurrentIndex)

    def toggle_menu(self):
        if self.menu_list.isVisible():
            self.menu_list.setVisible(False)
            self.toggle_menu_button.setIcon(QIcon("frontend/icons/menu_open.png"))
        else:
            self.menu_list.setVisible(True)
            self.toggle_menu_button.setIcon(QIcon("frontend/icons/menu_close.png"))

    def confirm_exit(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Підтвердження виходу")
        msg_box.setText("Ви впевнені, що хочете вийти з програми?")
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
            self.close()

    def add_tab(self, name, widget):
        item = QListWidgetItem(name)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setToolTip(TOOLTIP_MAP.get(name, name))
        self.menu_list.addItem(item)
        self.stack.addWidget(widget)
