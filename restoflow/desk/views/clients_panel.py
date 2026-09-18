from PyQt6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QPushButton,
                             QTableWidget, QTableWidgetItem, QVBoxLayout,
                             QWidget, QLineEdit)

from restoflow.database import SessionLocal
from restoflow.services import customer_service, order_service

STATUS_TITLES = {"new": "Новый", "cooking": "Готовится", "ready": "Готов",
                 "served": "Подан", "paid": "Оплачен",
                 "cancelled": "Отменён"}


class ClientDetailDialog(QDialog):
    def __init__(self, client_id: int):
        super().__init__()
        self.setWindowTitle("Карточка клиента")
        self.resize(760, 500)
        layout = QVBoxLayout(self)
        db = SessionLocal()
        try:
            client = customer_service.get_client(db, client_id)
            if not client:
                layout.addWidget(QLabel("Клиент не найден"))
                return
            info = QLabel(
                f"<b>{client.full_name}</b><br>Телефон: {client.phone}<br>"
                f"Email: {client.email or '—'}<br>"
                f"Баллы: {client.loyalty_points} · Визиты: {client.visits_count} · "
                f"Потрачено: {client.total_spent} ₽")
            layout.addWidget(info)
            orders = order_service.list_orders(db, client_id=client_id, limit=50)
            table = QTableWidget(len(orders), 5)
            table.setHorizontalHeaderLabels(
                ["#", "Дата", "Статус", "Сумма", "Позиций"])
            table.setAlternatingRowColors(True)
            table.verticalHeader().setVisible(False)
            for row, o in enumerate(orders):
                values = (str(o.id), o.created_at.strftime("%d.%m.%Y %H:%M"),
                          STATUS_TITLES.get(o.status, o.status),
                          f"{o.total_sum} ₽", str(len(o.items)))
                for col, value in enumerate(values):
                    table.setItem(row, col, QTableWidgetItem(value))
            layout.addWidget(table)
        finally:
            db.close()
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class ClientsTab(QWidget):
    HEADERS = ("ID", "ФИО", "Телефон", "Баллы", "Визиты", "Потрачено")

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        self.search_edit = QLineEdit(
            placeholderText="Поиск по имени или телефону…")
        self.search_edit.returnPressed.connect(self.refresh)
        search_button = QPushButton("Найти")
        search_button.clicked.connect(self.refresh)
        card_button = QPushButton("👤 Карточка клиента")
        card_button.clicked.connect(self.open_card)
        top.addWidget(self.search_edit)
        top.addWidget(search_button)
        top.addWidget(card_button)
        layout.addLayout(top)
        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.itemDoubleClicked.connect(lambda: self.open_card())
        layout.addWidget(self.table)
        self.refresh()

    def selected_client_id(self) -> int | None:
        row = self.table.currentRow()
        return None if row < 0 else int(self.table.item(row, 0).text())

    def open_card(self):
        client_id = self.selected_client_id()
        if client_id:
            ClientDetailDialog(client_id).exec()

    def refresh(self):
        db = SessionLocal()
        try:
            clients = customer_service.list_clients(
                db, search=self.search_edit.text().strip() or None)
            rows = [(c.id, c.full_name, c.phone, c.loyalty_points,
                     c.visits_count, c.total_spent) for c in clients]
        finally:
            db.close()
        self.table.setRowCount(len(rows))
        for row, values in enumerate(rows):
            for col, value in enumerate(values):
                text = f"{value:.0f} ₽" if col == 5 else str(value)
                self.table.setItem(row, col, QTableWidgetItem(text))