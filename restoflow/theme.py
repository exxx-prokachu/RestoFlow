PALETTE = {
    "bg": "#FAF6F0", "surface": "#FFFFFF", "primary": "#4B2E2B",
    "secondary": "#8C5E45", "accent": "#D9A47A", "text": "#2B1D1A",
    "success": "#5F7A4A", "danger": "#B3402E", "warning": "#C97B2A",
}

QSS = """
QWidget {background: %(bg)s; color: %(text)s; font-family: 'Segoe UI'; font-size: 14px;}
QPushButton {background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 %(secondary)s, stop:1 %(primary)s);
             color: #FFF8E1; border-radius: 10px; padding: 9px 18px; font-weight: 600; min-height: 22px;}
QPushButton:hover {background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 %(accent)s, stop:1 %(secondary)s);}
QPushButton:pressed {background: %(primary)s;}
QPushButton:disabled {background: #C4B5A8; color: #8A7A6F;}
QPushButton[cssClass="danger"] {background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #D45843, stop:1 %(danger)s);}
QPushButton[cssClass="success"] {background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #7A9A5A, stop:1 %(success)s);}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit, QPlainTextEdit {
    background: %(surface)s; border: 1px solid %(accent)s; border-radius: 10px; padding: 7px 10px;}
QLineEdit:focus, QComboBox:focus {border: 2px solid %(secondary)s;}
QTableWidget {background: %(surface)s; gridline-color: #EADFD3; border-radius: 12px;
              alternate-background-color: %(bg)s;}
QTableWidget::item:selected {background: %(accent)s; color: %(primary)s;}
QHeaderView::section {background: %(primary)s; color: #FFF8E1; padding: 9px; border: none; font-weight: 600;}
QTabWidget::pane {border: 1px solid %(accent)s; border-radius: 12px; background: %(surface)s;}
QTabBar::tab {background: %(surface)s; padding: 11px 26px; margin-right: 4px;
              border-top-left-radius: 10px; border-top-right-radius: 10px;}
QTabBar::tab:selected {background: %(primary)s; color: #FFF8E1; font-weight: 700;}
QTabBar::tab:hover:!selected {background: %(accent)s;}
QScrollArea {border: none; background: transparent;}
QFrame#orderCard {background: %(surface)s; border: 1px solid #EADFD3; border-radius: 12px; padding: 10px;}
QFrame#orderCard:hover {border: 1px solid %(secondary)s;}
QFrame#kanbanColumn {background: #F3EBE1; border-radius: 14px; padding: 10px;}
QLabel#cardHead {font-weight: 700; color: %(primary)s; font-size: 15px;}
QLabel[cssClass="title"] {font-size: 24px; font-weight: 800; color: %(primary)s;}
QLabel[cssClass="kpi"] {background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 %(surface)s, stop:1 #F3E7DA);
                        border: 1px solid %(accent)s; border-radius: 14px;
                        padding: 16px; font-size: 22px; font-weight: 800; color: %(primary)s;}
QLabel[cssClass="kpiIcon"] {font-size: 28px;}
QLabel#col-new {color: #8a5a2b; font-size: 15px; font-weight: 800;}
QLabel#col-cooking {color: %(secondary)s; font-size: 15px; font-weight: 800;}
QLabel#col-ready {color: %(success)s; font-size: 15px; font-weight: 800;}
QLabel#col-served {color: %(primary)s; font-size: 15px; font-weight: 800;}
QMessageBox {background: %(surface)s;}
""" % PALETTE


def status_color(status: str) -> str:
    return {
        "new": PALETTE["accent"], "cooking": PALETTE["secondary"],
        "ready": PALETTE["success"], "served": PALETTE["primary"],
        "paid": PALETTE["success"], "cancelled": PALETTE["danger"],
    }.get(status, PALETTE["secondary"])