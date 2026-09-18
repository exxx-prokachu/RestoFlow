from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from restoflow.models import (Client, Dish, Order, OrderItem, OrderStatus,
                              Payment)


def dashboard_kpi(db: Session) -> dict:
    today = date.today()
    paid = Order.status == OrderStatus.PAID.value
    revenue_today = db.query(func.sum(Order.total_sum)).filter(
        paid, func.date(Order.created_at) == today).scalar() or 0
    revenue_month = db.query(func.sum(Order.total_sum)).filter(
        paid, func.strftime("%Y-%m", Order.created_at) == today.strftime("%Y-%m")
    ).scalar() or 0
    active = db.query(Order).filter(Order.status.in_(
        [OrderStatus.NEW.value, OrderStatus.COOKING.value,
         OrderStatus.READY.value, OrderStatus.SERVED.value])).count()
    avg_check = db.query(func.avg(Order.total_sum)).filter(paid).scalar() or 0
    stoplist = db.query(Dish).filter(Dish.is_available == False).count()
    clients = db.query(Client).count()
    return {
        "revenue_today": round(revenue_today, 2),
        "revenue_month": round(revenue_month, 2),
        "active_orders": active,
        "avg_check": round(avg_check, 2),
        "stoplist": stoplist,
        "clients_total": clients,
    }


def top_dishes(db: Session, limit: int = 5) -> list[tuple[str, int]]:
    rows = db.query(
        Dish.name, func.coalesce(func.sum(OrderItem.qty), 0).label("qty")
    ).outerjoin(OrderItem, OrderItem.dish_id == Dish.id
    ).group_by(Dish.id).order_by(func.sum(OrderItem.qty).desc()
    ).limit(limit).all()
    return [(name, int(qty)) for name, qty in rows]


def revenue_by_day(db: Session, days: int = 7) -> list[dict]:
    paid = Order.status == OrderStatus.PAID.value
    rows = db.query(
        func.date(Order.created_at).label("day"),
        func.sum(Order.total_sum).label("sum"),
        func.count(Order.id).label("cnt"),
    ).filter(paid).group_by(func.date(Order.created_at)
    ).order_by(func.date(Order.created_at).desc()).limit(days).all()
    return [{"day": str(r.day), "sum": float(r.sum or 0), "cnt": int(r.cnt)}
            for r in rows]


def orders_by_status(db: Session) -> dict:
    rows = db.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    return {s: c for s, c in rows}


def payments_summary(db: Session) -> dict:
    rows = db.query(Payment.method, func.sum(Payment.amount),
                    func.count(Payment.id)).group_by(Payment.method).all()
    return {m: {"sum": float(s or 0), "count": int(c)} for m, s, c in rows}