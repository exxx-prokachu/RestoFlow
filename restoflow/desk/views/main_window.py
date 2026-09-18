from PyQt6.QtWidgets import QMainWindow, QTabWidget

from restoflow.desk.views.audit_panel import AuditTab
from restoflow.desk.views.clients_panel import ClientsTab
from restoflow.desk.views.dashboard import DashboardTab
from restoflow.desk.views.feedback_panel import FeedbackTab
from restoflow.desk.views.support_panel import SupportTab
from restoflow.desk.views.users_panel import UsersTab
from restoflow.desk.views.kanban_board import KanbanTab
from restoflow.desk.views.menu_editor import MenuEditorTab


class MainWindow(QMainWindow):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.setWindowTitle(f"RestoFlow Desk — {user.full_name} ({user.role_value()})")
        self.resize(1400, 850)
        tabs = QTabWidget()
        tabs.addTab(DashboardTab(), "📊 Дашборд")
        tabs.addTab(KanbanTab(), "🍳 Заказы")
        tabs.addTab(MenuEditorTab(), "📖 Меню")
        tabs.addTab(ClientsTab(), "👥 Клиенты")
        tabs.addTab(FeedbackTab(), "⭐ Отзывы")
        tabs.addTab(SupportTab(user), "🛟 Поддержка")
        if user.role_value() in ("admin", "manager"):
            tabs.addTab(UsersTab(user), "👥 Пользователи")
        if user.role_value() in ("admin", "manager"):
            tabs.addTab(AuditTab(), "📜 Аудит")
        self.setCentralWidget(tabs)