from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from restoflow.api.schemas import OrderOut
from restoflow.api.security import require_roles
from restoflow.database import get_db
from restoflow.models import Order, OrderStatus, User, UserRole
from restoflow.services import billing_service, order_service

router = APIRouter(prefix="/api/orders", tags=["orders"])
staff = require_roles(UserRole.ADMIN, UserRole.MANAGER,
                      UserRole.CASHIER, UserRole.COOK)
managers = require_roles(UserRole.ADMIN, UserRole.MANAGER)
cashiers = require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.CASHIER)


class OrderItemIn(BaseModel):
    dish_id: int
    qty: int = 1


class OrderIn(BaseModel):
    order_type: str = "dine_in"
    table_number: int | None = None
    client_id: int | None = None
    comment: str | None = None
    items: list[OrderItemIn]


class StatusIn(BaseModel):
    status: OrderStatus


class PaymentIn(BaseModel):
    method: str = "card"
    loyalty_points_used: int = 0


class DiscountIn(BaseModel):
    percent: int


@router.post("", status_code=201, response_model=OrderOut)
def create_order(body: OrderIn, db: Session = Depends(get_db),
                 user: User = Depends(staff)):
    try:
        return order_service.create_order(
            db, order_type=body.order_type, table_number=body.table_number,
            client_id=body.client_id, comment=body.comment,
            items=[(i.dish_id, i.qty) for i in body.items])
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/board", response_model=dict[str, list[OrderOut]])
def board(db: Session = Depends(get_db), user: User = Depends(staff)):
    return order_service.board_orders(db)


@router.get("", response_model=list[OrderOut])
def list_orders(status: str | None = None, client_id: int | None = None,
                limit: int = 100, db: Session = Depends(get_db),
                user: User = Depends(staff)):
    return order_service.list_orders(db, status=status,
                                     client_id=client_id, limit=limit)


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db),
              user: User = Depends(staff)):
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return order


@router.post("/{order_id}/status", response_model=OrderOut)
def set_status(order_id: int, body: StatusIn, db: Session = Depends(get_db),
               user: User = Depends(staff)):
    try:
        return order_service.advance_order(db, order_id, body.status)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/{order_id}/cancel", response_model=OrderOut)
def cancel(order_id: int, reason: str | None = None,
           db: Session = Depends(get_db),
           user: User = Depends(managers)):
    try:
        return order_service.cancel_order(db, order_id, reason=reason)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/{order_id}/pay", response_model=OrderOut)
def pay(order_id: int, body: PaymentIn, db: Session = Depends(get_db),
        user: User = Depends(cashiers)):
    try:
        return billing_service.pay_order(db, order_id, body.method,
                                         body.loyalty_points_used)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/{order_id}/discount", response_model=OrderOut)
def discount(order_id: int, body: DiscountIn, db: Session = Depends(get_db),
             user: User = Depends(managers)):
    try:
        return billing_service.apply_discount(db, order_id, body.percent)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))