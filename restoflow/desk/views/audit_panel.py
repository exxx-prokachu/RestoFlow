from PyQt6.QtWidgets import (QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QVBoxLayout, QWidget)

from restoflow.database import SessionLocal
from restoflow.services import audit_service


class AuditTab(QWidget):
    HEADERS = ("Время", "Действие", "Сущность", "Детали", "Пользователь")

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        refresh = QPushButton("Обновить")
        refresh.clicked.connect(self.refresh)
        top.addStretch()
        top.addWidget(refresh)
        layout.addLayout(top)
        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)
        self.refresh()

    def refresh(self):
        db = SessionLocal()
        try:
            logs = audit_service.list_logs(db, limit=200)
        finally:
            db.close()
        self.table.setRowCount(len(logs))
        for row, log in enumerate(logs):
            values = (log.created_at.strftime("%d.%m %H:%M:%S"),
                      log.action, log.entity or "",
                      log.details or "", log.user_info or "")
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(value))