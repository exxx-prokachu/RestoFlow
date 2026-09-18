from PyQt6.QtWidgets import (QDialog, QLabel, QLineEdit, QMessageBox,
                             QPushButton, QVBoxLayout)

from restoflow.database import SessionLocal
from restoflow.services.auth_service import authenticate


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.user = None
        self.setWindowTitle("RestoFlow Desk — вход")
        self.setFixedWidth(380)
        layout = QVBoxLayout(self)
        title = QLabel("☕ RestoFlow Desk")
        title.setProperty("cssClass", "title")
        self.login_edit = QLineEdit(placeholderText="Логин")
        self.password_edit = QLineEdit(placeholderText="Пароль")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.returnPressed.connect(self.try_login)
        button = QPushButton("Войти")
        button.clicked.connect(self.try_login)
        layout.addStretch()
        for widget in (title, self.login_edit, self.password_edit, button):
            layout.addWidget(widget)
        layout.addStretch()

    def try_login(self):
        db = SessionLocal()
        try:
            self.user = authenticate(db, self.login_edit.text().strip(),
                                     self.password_edit.text())
            if self.user:
                db.refresh(self.user)
        finally:
            db.close()
        if self.user:
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")