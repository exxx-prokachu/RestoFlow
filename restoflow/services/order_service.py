from datetime import datetime, timezone

from sqlalchemy.orm import Session

from restoflow.events import publish
from restoflow.models import Dish, Order, OrderItem, OrderStatus, OrderType
from restoflow.services.audit_service import log_action
from restoflow.services import notification_service

TRANSITIONS = {
    OrderStatus.NEW: {OrderStatus.COOKING, OrderStatus.CANCELLED},
    OrderStatus.COOKING: {OrderStatus.READY, OrderStatus.CANCELLED},
    OrderStatus.READY: {OrderStatus.SERVED, OrderStatus.PAID},
    OrderStatus.SERVED: {OrderStatus.PAID},
    OrderStatus.PAID: set(),
    OrderStatus.CANCELLED: set(),
}

BOARD_COLUMNS = (OrderStatus.NEW, OrderStatus.COOKING,
                 OrderStatus.READY, OrderStatus.SERVED)

TYPE_LABELS = {"dine_in": "зал", "takeaway": "самовывоз", "delivery": "доставка"}


def create_order(db: Session, *, order_type: str = OrderType.DINE_IN.value,
                 table_number: int | None = None,
                 client_id: int | None = None,
                 comment: str | None = None,
                 address: str | None = None,
                 items: list[tuple[int, int]]) -> Order:
    if not items:
        raise ValueError("Корзина пуста")
    from restoflow.utils import validators as V
    comment = V.validate_text(comment, 300, "Комментарий")
    effective_table = V.validate_table(table_number) \
        if order_type == OrderType.DINE_IN.value else None
    effective_address = V.validate_address(address) \
        if order_type == OrderType.DELIVERY.value else None
    if order_type == OrderType.DELIVERY.value and not effective_address:
        raise ValueError("Укажите адрес доставки")
    order = Order(order_type=order_type, table_number=effective_table,
                  client_id=client_id, status=OrderStatus.NEW.value,
                  discount_percent=0, comment=comment,
                  address=effective_address)
    for dish_id, qty in items:
        dish = db.get(Dish, dish_id)
        if not dish or not dish.is_available:
            raise ValueError(f"Блюдо недоступно: id={dish_id}")
        order.items.append(OrderItem(dish_id=dish_id, qty=max(1, qty), price=dish.price))
    order.recalc_total()
    db.add(order)
    db.commit()
    db.refresh(order)
    publish("order.created", order_id=order.id)
    log_action(db, "ORDER_CREATE", "Order",
               f"Заказ #{order.id} на {order.total_sum} руб.", None, order.id)
    return order


def advance_order(db: Session, order_id: int,
                  next_status: OrderStatus) -> Order:
    order = db.get(Order, order_id)
    if order is None:
        raise ValueError("Заказ не найден")
    current = OrderStatus(order.status)
    if next_status not in TRANSITIONS[current]:
        raise ValueError(
            f"Недопустимый переход {current.value} → {next_status.value}")
    order.status = next_status.value
    if next_status == OrderStatus.PAID:
        order.closed_at = datetime.now(timezone.utc)
    db.commit()
    publish("order.status_changed", order_id=order_id,
            old=current.value, new=next_status.value)
    if order.client_id:
        notification_service.push_to_client(
            db, order.client_id,
            title=f"🔄 Заказ #{order.id}: статус «{next_status.value}»",
            message="Статус заказа обновлён. Подробности в «Мои заказы».",
            kind="order")
        if next_status == OrderStatus.SERVED:
            notification_service.push_to_client(
                db, order.client_id,
                title=f"💳 Заказ #{order.id} ожидает оплаты",
                message="Оплатите заказ онлайн или на кассе.",
                kind="payment")
    log_action(db, "ORDER_STATUS", "Order",
               f"#{order_id}: {current.value} → {next_status.value}",
               None, order_id)
    return order


def cancel_order(db: Session, order_id: int,
                 reason: str | None = None) -> Order:
    order = advance_order(db, order_id, OrderStatus.CANCELLED)
    if reason:
        order.comment = (order.comment or "") + f"\n[отмена: {reason}]"
        db.commit()
    return order


def get_order(db: Session, order_id: int) -> Order | None:
    return db.get(Order, order_id)


def list_orders(db: Session, status: str | None = None,
                client_id: int | None = None,
                limit: int = 100) -> list[Order]:
    q = db.query(Order)
    if status:
        q = q.filter(Order.status == status)
    if client_id:
        q = q.filter(Order.client_id == client_id)
    return q.order_by(Order.created_at.desc()).limit(limit).all()


def board_orders(db: Session) -> dict[str, list[dict]]:
    board = {s.value: [] for s in BOARD_COLUMNS}
    orders = db.query(Order).filter(
        Order.status.in_([s.value for s in BOARD_COLUMNS])
    ).order_by(Order.created_at).all()
    for o in orders:
        board[o.status].append({
            "id": o.id, "status": o.status, "total": o.total_sum,
            "table": o.table_number, "type": o.order_type,
            "items_count": len(o.items),
            "created": o.created_at.strftime("%H:%M"),
            "comment": o.comment or "",
            "address": o.address or "",
        })
    return board