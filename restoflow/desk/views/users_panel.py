from PyQt6.QtWidgets import (QComboBox, QDialog, QFormLayout, QHBoxLayout,
                             QInputDialog, QLineEdit, QMessageBox,
                             QPushButton, QSplitter, QTableWidget,
                             QTableWidgetItem, QVBoxLayout, QWidget)

from restoflow.database import SessionLocal
from restoflow.models import UserRole
from restoflow.services import auth_service, customer_service


class StaffDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Новый сотрудник")
        form = QFormLayout(self)
        self.username_edit = QLineEdit()
        self.name_edit = QLineEdit()
        self.role_box = QComboBox()
        for role in UserRole:
            self.role_box.addItem(role.value, role)
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Логин", self.username_edit)
        form.addRow("ФИО", self.name_edit)
        form.addRow("Роль", self.role_box)
        form.addRow("Пароль", self.password_edit)
        button = QPushButton("Сохранить")
        button.clicked.connect(self.accept)
        form.addRow(button)

    def payload(self) -> dict:
        return {"username": self.username_edit.text().strip(),
                "full_name": self.name_edit.text().strip(),
                "role": self.role_box.currentData(),
                "password": self.password_edit.text()}


class ClientDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Новый клиент")
        form = QFormLayout(self)
        self.name_edit = QLineEdit()
        self.phone_edit = QLineEdit(placeholderText="+7 900 000-00-00")
        self.email_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("ФИО", self.name_edit)
        form.addRow("Телефон", self.phone_edit)
        form.addRow("Email", self.email_edit)
        form.addRow("Пароль для сайта", self.password_edit)
        button = QPushButton("Сохранить")
        button.clicked.connect(self.accept)
        form.addRow(button)


class UsersTab(QWidget):
    def __init__(self, user):
        super().__init__()
        self.current_user = user
        layout = QHBoxLayout(self)
        splitter = QSplitter()

        staff_box = QWidget()
        staff_layout = QVBoxLayout(staff_box)
        staff_panel = QHBoxLayout()
        add_staff = QPushButton("＋ Сотрудник")
        add_staff.clicked.connect(self.add_staff)
        pwd_btn = QPushButton("🔑 Пароль")
        pwd_btn.clicked.connect(self.change_password)
        block_btn = QPushButton("🚫 Блокировка")
        block_btn.clicked.connect(self.toggle_staff)
        refresh_btn = QPushButton("⟳ Обновить")
        refresh_btn.clicked.connect(self.refresh)
        for b in (add_staff, pwd_btn, block_btn, refresh_btn):
            staff_panel.addWidget(b)
        staff_layout.addLayout(staff_panel)
        self.staff_table = QTableWidget(0, 5)
        self.staff_table.setHorizontalHeaderLabels(
            ["ID", "Логин", "ФИО", "Роль", "Статус"])
        self.staff_table.verticalHeader().setVisible(False)
        self.staff_table.setAlternatingRowColors(True)
        staff_layout.addWidget(self.staff_table)

        clients_box = QWidget()
        clients_layout = QVBoxLayout(clients_box)
        clients_panel = QHBoxLayout()
        add_client = QPushButton("＋ Клиент")
        add_client.clicked.connect(self.add_client)
        block_client = QPushButton("🚫 Блокировка")
        block_client.clicked.connect(self.toggle_client)
        refresh_clients = QPushButton("⟳ Обновить")
        refresh_clients.clicked.connect(self.refresh)
        for b in (add_client, block_client, refresh_clients):
            clients_panel.addWidget(b)
        clients_layout.addLayout(clients_panel)
        self.clients_table = QTableWidget(0, 5)
        self.clients_table.setHorizontalHeaderLabels(
            ["ID", "ФИО", "Телефон", "Email", "Статус"])
        self.clients_table.verticalHeader().setVisible(False)
        self.clients_table.setAlternatingRowColors(True)
        clients_layout.addWidget(self.clients_table)

        splitter.addWidget(staff_box)
        splitter.addWidget(clients_box)
        layout.addWidget(splitter)
        self.refresh()

    def refresh(self):
        db = SessionLocal()
        try:
            users = [(u.id, u.username, u.full_name, u.role_value(),
                      "активен" if u.is_active else "заблокирован")
                     for u in auth_service.list_users(db)]
            clients = [(c.id, c.full_name, c.phone, c.email or "—",
                        "активен" if c.is_active is not False else "заблокирован")
                       for c in customer_service.list_clients(db)]
        finally:
            db.close()
        self.staff_table.setRowCount(len(users))
        for r, values in enumerate(users):
            for c, value in enumerate(values):
                self.staff_table.setItem(r, c, QTableWidgetItem(str(value)))
        self.clients_table.setRowCount(len(clients))
        for r, values in enumerate(clients):
            for c, value in enumerate(values):
                self.clients_table.setItem(r, c, QTableWidgetItem(str(value)))

    def selected_staff_id(self) -> int | None:
        row = self.staff_table.currentRow()
        return None if row < 0 else int(self.staff_table.item(row, 0).text())

    def selected_client_id(self) -> int | None:
        row = self.clients_table.currentRow()
        return None if row < 0 else int(self.clients_table.item(row, 0).text())

    def add_staff(self):
        dialog = StaffDialog()
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        db = SessionLocal()
        try:
            auth_service.create_user(db, **dialog.payload())
        except ValueError as e:
            QMessageBox.warning(self, "Пользователи", str(e))
        finally:
            db.close()
        self.refresh()

    def change_password(self):
        user_id = self.selected_staff_id()
        if not user_id:
            return
        text, ok = QInputDialog.getText(
            self, "Новый пароль", "Пароль:",
            QLineEdit.EchoMode.Password)
        if not ok or not text:
            return
        db = SessionLocal()
        try:
            auth_service.change_password(db, user_id, text)
            QMessageBox.information(self, "Пользователи", "✅ Пароль изменён")
        except ValueError as e:
            QMessageBox.warning(self, "Пользователи", str(e))
        finally:
            db.close()

    def toggle_staff(self):
        user_id = self.selected_staff_id()
        if not user_id:
            return
        db = SessionLocal()
        try:
            auth_service.toggle_user(db, user_id)
        except ValueError as e:
            QMessageBox.warning(self, "Пользователи", str(e))
        finally:
            db.close()
        self.refresh()

    def add_client(self):
        dialog = ClientDialog()
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        db = SessionLocal()
        try:
            client = customer_service.register_client(
                db, full_name=dialog.name_edit.text(),
                phone=dialog.phone_edit.text(),
                password=dialog.password_edit.text() or "Client1234")
            email = dialog.email_edit.text().strip()
            if email:
                customer_service.update_client(db, client.id, email=email)
        except ValueError as e:
            QMessageBox.warning(self, "Клиенты", str(e))
        finally:
            db.close()
        self.refresh()

    def toggle_client(self):
        client_id = self.selected_client_id()
        if not client_id:
            return
        db = SessionLocal()
        try:
            customer_service.toggle_active(db, client_id)
        finally:
            db.close()
        self.refresh()