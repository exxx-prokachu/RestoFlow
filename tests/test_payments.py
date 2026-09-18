import pytest

from restoflow.models import Category, OrderStatus
from restoflow.services import (billing_service, customer_service,
                                menu_service, order_service)
from restoflow.utils.validators import ValidationError, validate_card_number


@pytest.fixture()
def order_ready(db):
    db.add(Category(id=1, name="Кухня", icon="🍽️"))
    db.commit()
    dish = menu_service.create_dish(db, category_id=1, name="Пицца", price=500)
    client = customer_service.create_client(
        db, full_name="Плательщик Тест", phone="+70000000100")
    order = order_service.create_order(
        db, order_type="takeaway", client_id=client.id, items=[(dish.id, 1)])
    order_service.advance_order(db, order.id, OrderStatus.COOKING)
    order_service.advance_order(db, order.id, OrderStatus.READY)
    return order, client


def test_luhn_validation():
    assert validate_card_number("4111 1111 1111 1111") == "4111111111111111"
    with pytest.raises(ValidationError):
        validate_card_number("4111 1111 1111 1112")
    with pytest.raises(ValidationError):
        validate_card_number("1234")


def test_payment_flow_ready_to_paid(db, order_ready):
    order, client = order_ready
    paid = billing_service.process_test_payment(
        db, order.id, card_number="4111 1111 1111 1111",
        card_exp="12/30", cvc="123")
    assert paid.status == OrderStatus.PAID.value
    assert paid.payment is not None
    db.refresh(client)
    assert client.loyalty_points == 5
    assert client.visits_count == 1


def test_payment_rejects_bad_data(db, order_ready):
    order, _ = order_ready
    with pytest.raises(ValidationError):
        billing_service.process_test_payment(
            db, order.id, card_number="4111 1111 1111 1112",
            card_exp="12/30", cvc="123")
    with pytest.raises(ValidationError):
        billing_service.process_test_payment(
            db, order.id, card_number="4111 1111 1111 1111",
            card_exp="01/20", cvc="123")
    with pytest.raises(ValidationError):
        billing_service.process_test_payment(
            db, order.id, card_number="4111 1111 1111 1111",
            card_exp="12/30", cvc="12")