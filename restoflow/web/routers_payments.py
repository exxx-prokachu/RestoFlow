from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from restoflow.database import get_db
from restoflow.models import Client, Order
from restoflow.services import billing_service, notification_service
from restoflow.utils import validators as V

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def _client(request: Request, db: Session) -> Client | None:
    raw = request.cookies.get("client_id")
    return db.get(Client, int(raw)) if raw and raw.isdigit() else None


@router.get("/pay/{order_id}", response_class=HTMLResponse)
def pay_page(request: Request, order_id: int, message: str | None = None,
             db: Session = Depends(get_db)):
    client = _client(request, db)
    if not client:
        return RedirectResponse("/login?message=Войдите, чтобы оплатить заказ", 303)
    order = db.get(Order, order_id)
    if not order or order.client_id != client.id:
        return RedirectResponse("/my-orders?message=Заказ не найден", 303)
    return templates.TemplateResponse(request, "pay.html", {
        "client": client, "order": order, "message": message,
        "payable": billing_service.can_pay(order),
        "unread": notification_service.unread_client_count(db, client.id)})


@router.post("/pay/{order_id}")
def pay_process(request: Request, order_id: int, card_number: str = Form(...),
                card_exp: str = Form(...), cvc: str = Form(...),
                db: Session = Depends(get_db)):
    client = _client(request, db)
    if not client:
        return RedirectResponse("/login", 303)
    order = db.get(Order, order_id)
    if not order or order.client_id != client.id:
        return RedirectResponse("/my-orders?message=Заказ не найден", 303)
    try:
        billing_service.process_test_payment(
            db, order_id, card_number=card_number,
            card_exp=card_exp, cvc=cvc)
    except (ValueError, V.ValidationError) as e:
        return RedirectResponse(f"/pay/{order_id}?message={quote(str(e))}", 303)
    return RedirectResponse(f"/order/{order_id}?message=✅ Заказ оплачен", 303)