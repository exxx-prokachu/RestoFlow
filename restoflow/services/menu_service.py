from sqlalchemy.orm import Session

from restoflow.events import publish
from restoflow.models import Category, Dish
from restoflow.services.audit_service import log_action


def list_categories(db: Session) -> list[Category]:
    return db.query(Category).order_by(Category.sort_order, Category.name).all()


def list_dishes(db: Session, category_id: int | None = None,
                include_stopped: bool = False,
                search: str | None = None) -> list[Dish]:
    q = db.query(Dish)
    if category_id:
        q = q.filter(Dish.category_id == category_id)
    if not include_stopped:
        q = q.filter(Dish.is_available == True)
    dishes = q.order_by(Dish.name).all()
    if search:
        needle = search.strip().lower()
        if needle:
            dishes = [d for d in dishes if needle in d.name.lower()]
    return dishes


def get_dish(db: Session, dish_id: int) -> Dish | None:
    return db.get(Dish, dish_id)


def create_dish(db: Session, *, category_id: int, name: str, price: float,
                weight: str | None = None,
                description: str | None = None) -> Dish:
    dish = Dish(category_id=category_id, name=name, price=price,
                weight=weight, description=description)
    db.add(dish)
    db.commit()
    db.refresh(dish)
    publish("dish.created", dish_id=dish.id)
    log_action(db, "DISH_CREATE", "Dish", f"Создано: {name}", None, dish.id)
    return dish


def update_dish(db: Session, dish_id: int, **fields) -> Dish | None:
    dish = db.get(Dish, dish_id)
    if not dish:
        return None
    for key, value in fields.items():
        if hasattr(dish, key):
            setattr(dish, key, value)
    db.commit()
    log_action(db, "DISH_UPDATE", "Dish", f"ID={dish_id}", None, dish_id)
    return dish


def toggle_stoplist(db: Session, dish_id: int) -> Dish | None:
    dish = db.get(Dish, dish_id)
    if not dish:
        return None
    dish.is_available = not dish.is_available
    db.commit()
    if not dish.is_available:
        publish("dish.stopped", dish_id=dish.id)
    log_action(db, "DISH_STOPLIST", "Dish",
               f"{dish.name}: стоп={'да' if not dish.is_available else 'нет'}",
               None, dish.id)
    return dish


def delete_dish(db: Session, dish_id: int) -> bool:
    dish = db.get(Dish, dish_id)
    if not dish:
        return False
    db.delete(dish)
    db.commit()
    log_action(db, "DISH_DELETE", "Dish", f"ID={dish_id}", None, dish_id)
    return True


def create_category(db: Session, name: str, icon: str = "🍽️") -> Category:
    existing = db.query(Category).filter(Category.name == name).first()
    if existing:
        return existing
    cat = Category(name=name, icon=icon)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat