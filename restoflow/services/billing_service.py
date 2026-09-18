from sqlalchemy.orm import Session

from restoflow.events import publish
from restoflow.models import Client, Order, OrderStatus, Payment, PaymentMethod
from restoflow.services.audit_service import log_action
from restoflow.services.order_service import advance_order
from restoflow.services import notification_service
from restoflow.utils.mailer import send_email

def pay_order(db: Session, order_id: int,
              method: str = PaymentMethod.CARD.value,
              loyalty_points_used: int = 0) -> Order:
    order = advance_order(db, order_id, OrderStatus.PAID)
    final_amount = max(0.0, order.total_sum - loyalty_points_used)
    db.add(Payment(order_id=order.id, amount=final_amount, method=method))
    if order.client_id:
        client = db.get(Client, order.client_id)
        if client:
            client.loyalty_points += int(final_amount // 100)
            client.visits_count += 1
            client.total_spent = (client.total_spent or 0) + final_amount
            notification_service.push_to_client(
                db, client.id, title=f"💳 Заказ #{order.id} оплачен",
                message=f"Сумма {final_amount} ₽. Баллов начислено: "
                        f"{int(final_amount // 100)}", kind="payment")
            if client.email and client.email_notifications:
                send_email(client.email, f"RestoFlow: заказ #{order.id} оплачен",
                           f"Сумма {final_amount} ₽. Спасибо!")
    db.commit()
    publish("payment.completed", order_id=order.id,
            amount=final_amount, method=method)
    log_action(db, "PAYMENT", "Order",
               f"#{order.id} оплачен ({method}, {final_amount} руб.)",
               None, order.id)
    return order


def apply_discount(db: Session, order_id: int, percent: int) -> Order:
    order = db.get(Order, order_id)
    if not order:
        raise ValueError("Заказ не найден")
    order.discount_percent = max(0, min(100, percent))
    order.recalc_total()
    db.commit()
    log_action(db, "DISCOUNT", "Order",
               f"#{order.id}: скидка {percent}%", None, order_id)
    return order

def recalc_client_stats(db: Session, client_id: int) -> None:
    client = db.get(Client, client_id)
    if not client:
        return
    paid = db.query(Order).filter(
        Order.client_id == client_id,
        Order.status == OrderStatus.PAID.value).all()
    total, points = 0.0, 0
    for o in paid:
        amount = o.payment.amount if o.payment else o.total_sum
        total += amount
        points += int(amount // 100)
    client.visits_count = len(paid)
    client.total_spent = round(total, 2)
    client.loyalty_points = points
    db.commit()


def recalc_all_client_stats(db: Session) -> int:
    ids = [c.id for c in db.query(Client).all()]
    for cid in ids:
        recalc_client_stats(db, cid)
    return len(ids)

PAYABLE_STATUSES = (OrderStatus.READY.value, OrderStatus.SERVED.value)


def can_pay(order: Order) -> bool:
    return order is not None and order.status in PAYABLE_STATUSES


def process_test_payment(db: Session, order_id: int, *, card_number: str,
                         card_exp: str, cvc: str,
                         method: str = PaymentMethod.CARD.value) -> Order:
    from restoflow.utils import validators as V
    V.validate_card_number(card_number)
    V.validate_card_exp(card_exp)
    V.validate_cvc(cvc)
    order = db.get(Order, order_id)
    if not order:
        raise ValueError("Заказ не найден")
    if not can_pay(order):
        raise ValueError("Оплата доступна только для статусов «Готов» и «Подан»")
    log_action(db, "TEST_PAYMENT", "Order",
               f"#{order_id} карта ****{V.validate_card_number(card_number)[-4:]}",
               None, order_id)
    return pay_order(db, order_id, method)