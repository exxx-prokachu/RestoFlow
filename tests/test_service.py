import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from restoflow.database import Base
from restoflow.models import Category, OrderStatus
from restoflow.services import (billing_service, customer_service,
                                menu_service, order_service)


def test_order_lifecycle_and_stoplist(db):
    db.add(Category(id=1, name="Кухня", icon="🍽️"))
    db.commit()
    dish = menu_service.create_dish(db, category_id=1, name="Сырники", price=310)
    client = customer_service.create_client(
        db, full_name="Тест Тестов", phone="+70000000001")

    order = order_service.create_order(
        db, order_type="takeaway", table_number=None,
        client_id=client.id, items=[(dish.id, 2)])
    assert order.total_sum == 620
    assert order.status == OrderStatus.NEW.value

    order = order_service.advance_order(db, order.id, OrderStatus.COOKING)
    assert order.status == OrderStatus.COOKING.value

    with pytest.raises(ValueError):
        order_service.advance_order(db, order.id, OrderStatus.PAID)

    menu_service.toggle_stoplist(db, dish.id)
    with pytest.raises(ValueError):
        order_service.create_order(
            db, order_type="takeaway", table_number=None,
            client_id=client.id, items=[(dish.id, 1)])


def test_billing_flow(db):
    db.add(Category(id=1, name="Кухня", icon="🍽️"))
    db.commit()
    dish = menu_service.create_dish(db, category_id=1, name="Паста", price=500)
    client = customer_service.create_client(
        db, full_name="Платёж", phone="+70000000099")

    order = order_service.create_order(
        db, order_type="dine_in", table_number=3,
        client_id=client.id, items=[(dish.id, 1)])
    order_service.advance_order(db, order.id, OrderStatus.COOKING)
    order_service.advance_order(db, order.id, OrderStatus.READY)
    order_service.advance_order(db, order.id, OrderStatus.SERVED)
    paid = billing_service.pay_order(db, order.id, "card")
    assert paid.status == OrderStatus.PAID.value
    db.refresh(client)
    assert client.loyalty_points == 5
    assert client.visits_count == 1
    assert client.total_spent == 500


def test_phone_normalization(db):
    c1 = customer_service.create_client(
        db, full_name="A", phone="+7 (900) 111-22-33")
    c2 = customer_service.get_client_by_phone(db, "79001112233")
    assert c1.id == c2.id