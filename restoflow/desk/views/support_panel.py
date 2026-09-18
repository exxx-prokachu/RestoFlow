from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (QHBoxLayout, QMessageBox, QPlainTextEdit,
                             QPushButton, QSplitter, QTableWidget,
                             QTableWidgetItem, QTextEdit, QVBoxLayout,
                             QWidget)

from restoflow.database import SessionLocal
from restoflow.services import support_service

STATUS_TITLES = {"open": "Открыто", "in_progress": "В работе", "closed": "Закрыто"}


class SupportTab(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.current_id = None
        layout = QHBoxLayout(self)
        splitter = QSplitter()
        left = QWidget()
        left_layout = QVBoxLayout(left)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["#", "Клиент", "Тема", "Статус"])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self.load_thread)
        left_layout.addWidget(self.table)
        right = QWidget()
        right_layout = QVBoxLayout(right)
        self.thread_view = QTextEdit()
        self.thread_view.setReadOnly(True)
        self.reply_edit = QPlainTextEdit()
        self.reply_edit.setPlaceholderText("Ответ клиенту…")
        buttons = QHBoxLayout()
        reply_btn = QPushButton("✉ Ответить")
        reply_btn.clicked.connect(self.reply)
        close_btn = QPushButton("🔒 Закрыть")
        close_btn.clicked.connect(self.close_request)
        refresh_btn = QPushButton("⟳ Обновить")
        refresh_btn.clicked.connect(self.refresh)
        for b in (reply_btn, close_btn, refresh_btn):
            buttons.addWidget(b)
        right_layout.addWidget(self.thread_view)
        right_layout.addWidget(self.reply_edit)
        right_layout.addLayout(buttons)
        splitter.addWidget(left)
        splitter.addWidget(right)
        layout.addWidget(splitter)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(10000)
        self.refresh()

    def refresh(self):
        db = SessionLocal()
        try:
            rows = [{"id": r.id,
                     "client": r.client.full_name if r.client else "—",
                     "subject": r.subject, "status": r.status}
                    for r in support_service.list_all(db, limit=100)]
        finally:
            db.close()
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(row["client"]))
            self.table.setItem(r, 2, QTableWidgetItem(row["subject"]))
            self.table.setItem(r, 3,
                QTableWidgetItem(STATUS_TITLES.get(row["status"], row["status"])))

    def load_thread(self):
        row = self.table.currentRow()
        if row < 0:
            return
        self.current_id = int(self.table.item(row, 0).text())
        db = SessionLocal()
        try:
            req = support_service.get_request(db, self.current_id)
            if not req:
                return
            html = [f"<h3>#{req.id} · {req.subject}</h3>"]
            for m in req.messages:
                align = "right" if m.sender_type == "staff" else "left"
                html.append(
                    f"<div style='text-align:{align};margin:6px 0;'>"
                    f"<span style='background:#F3EBE1;border-radius:10px;"
                    f"padding:6px 10px;display:inline-block;'>"
                    f"<b>{m.sender_name}</b>: {m.body}</span></div>")
        finally:
            db.close()
        self.thread_view.setHtml("".join(html))

    def reply(self):
        if not self.current_id:
            return
        text = self.reply_edit.toPlainText().strip()
        if not text:
            return
        db = SessionLocal()
        try:
            support_service.add_staff_message(
                db, self.current_id, self.user.full_name, text)
        except ValueError as e:
            QMessageBox.warning(self, "Поддержка", str(e))
        finally:
            db.close()
        self.reply_edit.clear()
        self.refresh()
        self.load_thread()

    def close_request(self):
        if not self.current_id:
            return
        db = SessionLocal()
        try:
            support_service.close_request(db, self.current_id)
        except ValueError as e:
            QMessageBox.warning(self, "Поддержка", str(e))
        finally:
            db.close()
        self.refresh()
        self.load_thread()