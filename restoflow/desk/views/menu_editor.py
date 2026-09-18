from PyQt6.QtWidgets import (QComboBox, QDialog, QDoubleSpinBox, QFormLayout,
                             QHBoxLayout, QLabel, QLineEdit, QMessageBox,
                             QPlainTextEdit, QPushButton, QTableWidget,
                             QTableWidgetItem, QVBoxLayout, QWidget)

from restoflow.database import SessionLocal
from restoflow.services.menu_service import (create_dish, list_categories,
                                             list_dishes, toggle_stoplist,
                                             update_dish)


class DishDialog(QDialog):
    def __init__(self, categories, dish=None):
        super().__init__()
        self.setWindowTitle("Блюдо")
        self.categories = categories
        form = QFormLayout(self)
        self.name_edit = QLineEdit(dish.name if dish else "")
        self.category_box = QComboBox()
        for category in categories:
            self.category_box.addItem(category.name, category.id)
        if dish:
            for i in range(self.category_box.count()):
                if self.category_box.itemData(i) == dish.category_id:
                    self.category_box.setCurrentIndex(i)
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(1, 100000)
        self.price_spin.setValue(dish.price if dish else 100)
        self.weight_edit = QLineEdit(dish.weight if dish else "")
        self.desc_edit = QPlainTextEdit(dish.description if dish else "")
        form.addRow("Название", self.name_edit)
        form.addRow("Категория", self.category_box)
        form.addRow("Цена, ₽", self.price_spin)
        form.addRow("Выход", self.weight_edit)
        form.addRow("Описание", self.desc_edit)
        button = QPushButton("Сохранить")
        button.clicked.connect(self.accept)
        form.addRow(button)

    def payload(self) -> dict:
        return {"name": self.name_edit.text().strip(),
                "category_id": self.category_box.currentData(),
                "price": self.price_spin.value(),
                "weight": self.weight_edit.text().strip() or None,
                "description": self.desc_edit.toPlainText().strip() or None}


class MenuEditorTab(QWidget):
    HEADERS = ("ID", "Блюдо", "Категория", "Цена", "Выход", "Статус")

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        panel = QHBoxLayout()
        add_button = QPushButton("＋ Блюдо")
        edit_button = QPushButton("Изменить")
        stop_button = QPushButton("Стоп-лист")
        refresh_button = QPushButton("Обновить")
        for button, handler in ((add_button, self.add_dish),
                                (edit_button, self.edit_dish),
                                (stop_button, self.stop_dish),
                                (refresh_button, self.refresh)):
            button.clicked.connect(handler)
            panel.addWidget(button)
        layout.addLayout(panel)
        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        self.refresh()

    def selected_dish_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        return int(self.table.item(row, 0).text())

    def add_dish(self):
        db = SessionLocal()
        try:
            dialog = DishDialog(list_categories(db))
            if dialog.exec() == QDialog.DialogCode.Accepted:
                create_dish(db, **dialog.payload())
        finally:
            db.close()
        self.refresh()

    def edit_dish(self):
        dish_id = self.selected_dish_id()
        if dish_id is None:
            return
        db = SessionLocal()
        try:
            from restoflow.models import Dish
            dish = db.get(Dish, dish_id)
            if not dish:
                return
            dialog = DishDialog(list_categories(db), dish)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                update_dish(db, dish_id, **dialog.payload())
        finally:
            db.close()
        self.refresh()

    def stop_dish(self):
        dish_id = self.selected_dish_id()
        if dish_id is None:
            return
        db = SessionLocal()
        try:
            toggle_stoplist(db, dish_id)
        finally:
            db.close()
        self.refresh()

    def refresh(self):
        db = SessionLocal()
        try:
            dishes = list_dishes(db, include_stopped=True)
            categories = {c.id: c.name for c in list_categories(db)}
        finally:
            db.close()
        self.table.setRowCount(len(dishes))
        for row, dish in enumerate(dishes):
            values = (str(dish.id), dish.name,
                      categories.get(dish.category_id, "—"),
                      f"{dish.price} ₽", dish.weight or "—",
                      "в продаже" if dish.is_available else "стоп-лист")
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col == 5 and value == "стоп-лист":
                    from PyQt6.QtGui import QColor
                    item.setForeground(QColor("#B3402E"))
                self.table.setItem(row, col, item)