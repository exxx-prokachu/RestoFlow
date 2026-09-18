from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (QHBoxLayout, QLabel, QTableWidget,
                             QTableWidgetItem, QVBoxLayout, QWidget)

from restoflow.database import SessionLocal
from restoflow.services.report_service import dashboard_kpi, top_dishes

CAPTIONS = [("revenue_today", "Выручка сегодня", "💰"),
            ("revenue_month", "Выручка за месяц", "📅"),
            ("active_orders", "Активные заказы", "🧾"),
            ("avg_check", "Средний чек", "📈"),
            ("stoplist", "Стоп-лист", "🚫"),
            ("clients_total", "Клиентов", "👥")]


class KpiTile(QWidget):
    def __init__(self, caption: str, icon: str):
        super().__init__()
        layout = QVBoxLayout(self)
        icon_label = QLabel(icon)
        icon_label.setProperty("cssClass", "kpiIcon")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value = QLabel("—")
        self.value.setProperty("cssClass", "kpi")
        self.value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        caption_label = QLabel(caption)
        caption_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        layout.addWidget(self.value)
        layout.addWidget(caption_label)

    def set_value(self, text: str) -> None:
        self.value.setText(text)


class DashboardTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        row1 = QHBoxLayout()
        row2 = QHBoxLayout()
        self.tiles = {}
        for idx, (key, caption, icon) in enumerate(CAPTIONS):
            from restoflow.desk.animations import fade_in
            for i, tile in enumerate(self.tiles.values()):
                fade_in(tile, 400, i * 90)
            self.tiles[key] = KpiTile(caption, icon)
            (row1 if idx < 3 else row2).addWidget(self.tiles[key])
        layout.addLayout(row1)
        layout.addLayout(row2)
        self.top_table = QTableWidget(0, 2)
        self.top_table.setHorizontalHeaderLabels(["Топ блюд", "Продано"])
        self.top_table.setAlternatingRowColors(True)
        self.top_table.verticalHeader().setVisible(False)
        layout.addWidget(self.top_table)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(15000)
        self.refresh()

    def refresh(self):
        db = SessionLocal()
        try:
            kpi = dashboard_kpi(db)
            tops = top_dishes(db, 5)
        finally:
            db.close()
        self.tiles["revenue_today"].set_value(f"{kpi['revenue_today']} ₽")
        self.tiles["revenue_month"].set_value(f"{kpi['revenue_month']} ₽")
        self.tiles["active_orders"].set_value(str(kpi["active_orders"]))
        self.tiles["avg_check"].set_value(f"{kpi['avg_check']} ₽")
        self.tiles["stoplist"].set_value(str(kpi["stoplist"]))
        self.tiles["clients_total"].set_value(str(kpi["clients_total"]))
        self.top_table.setRowCount(len(tops))
        for row, (name, qty) in enumerate(tops):
            self.top_table.setItem(row, 0, QTableWidgetItem(name))
            self.top_table.setItem(row, 1, QTableWidgetItem(str(qty)))