from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QTableWidget,
                             QTableWidgetItem, QInputDialog, QVBoxLayout,
                             QWidget)

from restoflow.database import SessionLocal
from restoflow.services import feedback_service


class FeedbackTab(QWidget):
    HEADERS = ("ID", "Автор", "Оценка", "Отзыв", "Ответ", "Дата")

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        self.stats_label = QLabel("")
        reply_btn = QPushButton("💬 Ответить на выбранный")
        reply_btn.clicked.connect(self.reply_selected)
        refresh = QPushButton("⟳ Обновить")
        refresh.clicked.connect(self.refresh)
        top.addWidget(self.stats_label)
        top.addStretch()
        top.addWidget(reply_btn)
        top.addWidget(refresh)
        layout.addLayout(top)
        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(15000)
        self.refresh()

    def refresh(self):
        db = SessionLocal()
        try:
            rows = feedback_service.list_feedback_detailed(db, 100)
            stats = feedback_service.rating_stats(db)
        finally:
            db.close()
        self.stats_label.setText(
            f"⭐ Средняя оценка: {stats['average']} · отзывов: {stats['count']}")
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            stars = "★" * row["rating"] + "☆" * (5 - row["rating"])
            values = (str(row["id"]), row["author"], stars,
                      row["comment"] or "", row["reply"] or "",
                      row["created_at"].strftime("%d.%m.%Y %H:%M"))
            for c, value in enumerate(values):
                self.table.setItem(r, c, QTableWidgetItem(value))

    def reply_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        feedback_id = int(self.table.item(row, 0).text())
        text, ok = QInputDialog.getMultiLineText(self, "Ответ на отзыв", "Ваш ответ:")
        if ok and text.strip():
            db = SessionLocal()
            try:
                feedback_service.reply_feedback(db, feedback_id, text.strip())
            finally:
                db.close()
            self.refresh()