import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from restoflow.database import SessionLocal, init_db
from restoflow.models import (Category, Client, Dish, Feedback, Order,
                              OrderItem, OrderStatus, Payment, UserRole)
from restoflow.services.auth_service import create_user

init_db()
db = SessionLocal()

if db.query(Category).count() == 0:
    cat_ids = {}
    for name, icon in [("Кухня", "🍽️"), ("Напитки", "☕"), ("Десерты", "🍰"),
                       ("Салаты", "🥗"), ("Выпечка", "🥐")]:
        c = Category(name=name, icon=icon)
        db.add(c); db.commit(); cat_ids[name] = c.id
    dishes = [
        ("Кухня", "Паста карбонара", 420, "320 г", "Спагетти, бекон, пармезан"),
        ("Кухня", "Сырники", 310, "250 г", "Со сметаной и ягодным джемом"),
        ("Кухня", "Том ям с креветками", 560, "350 мл", "Острый тайский суп"),
        ("Кухня", "Бургер классический", 480, "340 г", "Говядина, чеддер, соусы"),
        ("Кухня", "Пицца маргарита", 520, "400 г", "Томаты, моцарелла, базилик"),
        ("Напитки", "Раф лавандовый", 280, "350 мл", "Нежный сливочный кофе"),
        ("Напитки", "Капучино", 220, "300 мл", "Двойной эспрессо и молоко"),
        ("Напитки", "Матча латте", 290, "350 мл", "Японский чай на молоке"),
        ("Напитки", "Лимонад цитрус", 240, "400 мл", "Домашний, со льдом"),
        ("Десерты", "Чизкейк нью-йорк", 340, "150 г", "Классика на песочной основе"),
        ("Десерты", "Тирамису", 360, "160 г", "Маскарпоне, савоярди, кофе"),
        ("Десерты", "Медовик", 300, "170 г", "Домашний, семейный рецепт"),
        ("Салаты", "Цезарь с курицей", 390, "260 г", "Романо, пармезан, гренки"),
        ("Салаты", "Греческий", 350, "280 г", "Фета, оливки, свежие овощи"),
        ("Выпечка", "Круассан миндальный", 260, "110 г", "Свежая утренняя выпечка"),
        ("Выпечка", "Багет французский", 180, "250 г", "Хрустящая корочка"),
    ]
    for cat, name, price, weight, desc in dishes:
        db.add(Dish(category_id=cat_ids[cat], name=name, price=price,
                    weight=weight, description=desc))
    db.commit()

create_user(db, "admin", "Администратор", "admin123", UserRole.ADMIN)
create_user(db, "manager", "Мария Менеджер", "manager123", UserRole.MANAGER)
create_user(db, "cashier", "Иван Касса", "cash123", UserRole.CASHIER)
create_user(db, "cook", "Пётр Кухня", "cook123", UserRole.COOK)

if db.query(Client).count() == 0:
    for name, phone, pts, v, s in [
        ("Анна Смирнова", "+79161112233", 350, 12, 4820),
        ("Игорь Петров", "+79164445566", 150, 6, 2100),
        ("Мария Козлова", "+79167778899", 520, 18, 7350),
        ("Олег Соколов", "+79160001122", 80, 3, 1240),
    ]:
        c = Client(full_name=name, phone=phone, loyalty_points=pts,
                   visits_count=v, total_spent=s)
        c.set_password("client123")
        db.add(c)
    db.commit()

if db.query(Order).count() == 0:
    dishes = db.query(Dish).all()
    clients = db.query(Client).all()
    combos = [
        (clients[0], OrderStatus.PAID, [(0, 1), (5, 2)]),
        (clients[1], OrderStatus.SERVED, [(3, 1), (8, 1)]),
        (clients[2], OrderStatus.READY, [(9, 2)]),
        (clients[3], OrderStatus.COOKING, [(4, 1), (12, 1), (6, 2)]),
        (clients[0], OrderStatus.NEW, [(10, 1), (14, 2)]),
        (clients[1], OrderStatus.CANCELLED, [(2, 1)]),
        (clients[2], OrderStatus.PAID, [(7, 1), (11, 1)]),
        (clients[3], OrderStatus.NEW, [(1, 2)]),
    ]
    for client, status, items in combos:
        order = Order(client_id=client.id, order_type="takeaway",
                      status=status.value, discount_percent=0)
        for idx, qty in items:
            d = dishes[idx]
            order.items.append(OrderItem(dish_id=d.id, qty=qty, price=d.price))
        order.recalc_total()
        db.add(order)
    db.commit()
    for o in db.query(Order).filter(Order.status == OrderStatus.PAID.value).all():
        db.add(Payment(order_id=o.id, amount=o.total_sum, method="card"))
    for text, rating in [("Лучший раф в городе!", 5),
                         ("Вкусно, но долго ждали.", 4),
                         ("Замечательная атмосфера.", 5)]:
        db.add(Feedback(client_id=1, rating=rating, comment=text))
    db.commit()

print("✅ Seed завершён: 4 роли, 16 блюд, 4 клиента, 8 заказов, отзывы")
db.close()