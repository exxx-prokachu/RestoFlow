import sys

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtGui import QIcon

from restoflow.database import init_db
from restoflow.desk.views.login_dialog import LoginDialog
from restoflow.desk.views.main_window import MainWindow
from restoflow.theme import QSS

window = QMainWindow()
window.setWindowIcon(QIcon('app_icon.png'))

def main():
    init_db()
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    login = LoginDialog()
    if login.exec() != LoginDialog.DialogCode.Accepted:
        sys.exit(0)
    window = MainWindow(login.user)
    window.show()
    from restoflow.desk.animations import fade_in_window
    fade_in_window(window)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()