from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from PyQt6.QtGui import QPainter
from PyQt6.QtCore import QPropertyAnimation
from PyQt6.QtWidgets import QGraphicsOpacityEffect
import requests
from datetime import datetime, timedelta
from user_session.current_user import CurrentUser

from config.config import API_URL

class AnalyticsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.api_url = API_URL + "/analytics"
        self.user =  CurrentUser()
        self.init_ui()

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

        filter_layout = QHBoxLayout()
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Останні 7 днів", "Останні 30 днів", "Останні 90 днів", "Весь період"])
        self.period_combo.currentIndexChanged.connect(self.load_data)

        self.btn_refresh = QPushButton("Оновити")
        self.btn_refresh.clicked.connect(self.load_data)

        filter_layout.addWidget(QLabel("Період:"))
        filter_layout.addWidget(self.period_combo)
        filter_layout.addWidget(self.btn_refresh)
        filter_layout.addStretch()

        title_chart = QLabel("📊 Графік видач книг")
        title_chart.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 10px;")

        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        title_table = QLabel("📋 Загальна статистика")
        title_table.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 20px;")

        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(3)
        self.stats_table.setHorizontalHeaderLabels(["Показник", "Значення", "Деталі"])
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        self.stats_table.verticalHeader().setVisible(False)
        self.stats_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.stats_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.stats_table.setStyleSheet("""
            QTableWidget {
                background-color: #fcfcfc;
                border: 1px solid #ddd;
            }
            QTableWidget::item {
                padding: 6px;
            }
        """)

        layout.addLayout(filter_layout)
        layout.addWidget(title_chart)
        layout.addWidget(self.chart_view, stretch=2)
        layout.addWidget(title_table)
        layout.addWidget(self.stats_table, stretch=1)
        layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(layout)

    def load_data(self):
        try:
            self.btn_refresh.setText("Завантаження...")
            self.btn_refresh.setEnabled(False)

            period = self.period_combo.currentText()
            params = self._get_period_params(period)

            response = requests.get(f"{self.api_url}/stats", params=params, headers=self.user.get_auth_header())
            if response.status_code != 200:
                raise Exception("Помилка отримання даних")

            data = response.json()
            self._update_chart(data.get("borrowings_by_day", []))
            self._update_stats_table(data.get("general_stats", {}))

        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити дані: {e}")
        finally:
            self.btn_refresh.setText("Оновити")
            self.btn_refresh.setEnabled(True)

    def _get_period_params(self, period):
        today = datetime.now().date()
        if period == "Останні 7 днів":
            start_date = today - timedelta(days=7)
        elif period == "Останні 30 днів":
            start_date = today - timedelta(days=30)
        elif period == "Останні 90 днів":
            start_date = today - timedelta(days=90)
        else:
            start_date = None
        return {"start_date": start_date.isoformat()} if start_date else {}

    def _update_chart(self, borrowings_data):
        chart = QChart()
        chart.setTitle("Кількість видач книг за період")

        series = QBarSeries()
        bar_set = QBarSet("Видачі")

        dates = []
        for item in borrowings_data:
            dates.append(datetime.strptime(item["date"], "%Y-%m-%d").strftime("%d.%m"))
            bar_set.append(item["count"])

        series.append(bar_set)
        chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(dates)
        axis_x.setLabelsAngle(-45)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setTitleText("Кількість")
        max_value = max([item["count"] for item in borrowings_data], default=10)
        axis_y.setRange(0, max_value + 1)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        self.chart_view.setChart(chart)
        self.fade_in_widget(self.chart_view)

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

    def _update_stats_table(self, stats):
        self.stats_table.setRowCount(0)
        if not stats:
            return

        rows = [
            ["Активні читачі", stats.get("active_readers", 0), "Читачі з хоча б однією видачею"],
            ["Прострочені книги", stats.get("overdue_books", 0), "Книги, не повернуті вчасно"],
            ["Найпопулярніша книга", stats.get("top_book", "-"), "За кількістю видач"],
        ]

        self.stats_table.setRowCount(len(rows))
        for row, (name, value, details) in enumerate(rows):
            self.stats_table.setItem(row, 0, QTableWidgetItem(name))
            self.stats_table.setItem(row, 1, QTableWidgetItem(str(value)))
            self.stats_table.setItem(row, 2, QTableWidgetItem(details))

        self.stats_table.resizeRowsToContents()
        self.stats_table.verticalHeader().setDefaultSectionSize(35)
        self.stats_table.horizontalHeader().setDefaultSectionSize(150)
        self.stats_table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fade_in_widget(self.stats_table)