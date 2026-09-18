from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QMessageBox,
                             QPushButton, QScrollArea, QVBoxLayout, QWidget)

from restoflow.database import SessionLocal
from restoflow.models import OrderStatus
from restoflow.services import billing_service
from restoflow.services.order_service import advance_order, board_orders
from restoflow.theme import status_color

NEXT = {OrderStatus.NEW: ("В готовку", OrderStatus.COOKING),
        OrderStatus.COOKING: ("Готов", OrderStatus.READY),
        OrderStatus.READY: ("Подать", OrderStatus.SERVED),
        OrderStatus.SERVED: ("Оплата", OrderStatus.PAID)}
TITLES = {OrderStatus.NEW: "Новые", OrderStatus.COOKING: "Готовится",
          OrderStatus.READY: "Готово", OrderStatus.SERVED: "Подано"}
TYPES = {"dine_in": "зал", "takeaway": "самовывоз", "delivery": "доставка"}


class OrderCard(QFrame):
    advanced = pyqtSignal()

    def __init__(self, data: dict):
        super().__init__()
        self.setObjectName("orderCard")
        self.order_id = data["id"]
        self.status = OrderStatus(data["status"])
        layout = QVBoxLayout(self)
        if data["table"]:
            place = f"стол {data['table']}"
        elif data.get("address"):
            place = f"доставка: {data['address'][:28]}"
        else:
            place = TYPES.get(data["type"], data["type"])
        head = QLabel(f"#{data['id']} · {place} · {data['created']}")
        head.setObjectName("cardHead")
        layout.addWidget(head)
        layout.addWidget(QLabel(f"{data['items_count']} поз. · {data['total']} ₽"))
        label, next_status = NEXT[self.status]
        button = QPushButton(f"→ {label}")
        button.clicked.connect(lambda: self.advance(next_status))
        layout.addWidget(button)
        self.setStyleSheet(self.styleSheet() +
                           f"border-left: 6px solid {status_color(self.status.value)};")

    def advance(self, next_status: OrderStatus):
        db = SessionLocal()
        try:
            if next_status == OrderStatus.PAID:
                billing_service.pay_order(db, self.order_id)
            else:
                advance_order(db, self.order_id, next_status)
        except ValueError as e:
            QMessageBox.warning(self, "Статус", str(e))
        finally:
            db.close()
        self.advanced.emit()


class KanbanTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        self.columns = {}
        for status in (OrderStatus.NEW, OrderStatus.COOKING,
                       OrderStatus.READY, OrderStatus.SERVED):
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            inner = QWidget()
            inner.setObjectName("kanbanColumn")
            column = QVBoxLayout(inner)
            header = QLabel(f"{TITLES[status]} · 0")
            header.setObjectName(f"col-{status.value}")
            cards = QVBoxLayout()
            cards.addStretch()
            column.addWidget(header)
            column.addLayout(cards)
            column.addStretch()
            scroll.setWidget(inner)
            self.columns[status.value] = (header, cards)
            layout.addWidget(scroll)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(10000)
        self.refresh()

    def refresh(self):
        db = SessionLocal()
        try:
            board = board_orders(db)
        finally:
            db.close()
        for status, (header, cards) in self.columns.items():
            while cards.count() > 1:
                item = cards.takeAt(0)
                if item.widget():
                    from restoflow.desk.animations import clear_fade
                    clear_fade(item.widget())
                    item.widget().deleteLater()
            orders = board.get(status, [])
            header.setText(f"{TITLES[OrderStatus(status)]} · {len(orders)}")
            for data in orders:
                card = OrderCard(data)
                card.advanced.connect(self.refresh)
                cards.insertWidget(cards.count() - 1, card)
                from restoflow.desk.animations import fade_in
                fade_in(card, 300, orders.index(data) * 60)