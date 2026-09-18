import json
import re
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse

from restoflow.database import get_db, init_db
from restoflow.models import Client, Order
from restoflow.services import (customer_service, feedback_service,
                                menu_service, notification_service,
                                order_service)

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

STATUS_TITLES = {"new": "Принят", "cooking": "Готовится",
                 "ready": "Готов к выдаче", "served": "Подан",
                 "paid": "Оплачен", "cancelled": "Отменён"}
STATUS_FLOW = ["new", "cooking", "ready", "served", "paid"]
def _digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="RestoFlow Online", docs_url=None,
              redoc_url=None, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
from restoflow.web.routers_profile import router as profile_router
app.include_router(profile_router)
from restoflow.web.routers_support import router as support_router
app.include_router(support_router)
from restoflow.web.routers_reviews import router as reviews_router
app.include_router(reviews_router)
from restoflow.web.routers_payments import router as payments_router
app.include_router(payments_router)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("favicon.ico")

def get_current_client(request: Request, db: Session) -> Client | None:
    raw = request.cookies.get("client_id")
    if not raw or not raw.isdigit():
        return None
    return db.get(Client, int(raw))


def set_client_cookie(response, client: Client):
    response.set_cookie("client_id", str(client.id),
                        max_age=7 * 24 * 3600, httponly=True, samesite="lax")
    return response


def build_timeline(order: Order) -> list[dict]:
    if order.status == "cancelled":
        return [{"title": STATUS_TITLES["cancelled"], "state": "cancelled"}]
    if order.status not in STATUS_FLOW:
        return [{"title": order.status, "state": "current"}]
    idx = STATUS_FLOW.index(order.status)
    return [{"title": STATUS_TITLES[s],
             "state": "done" if i < idx else ("current" if i == idx else "pending")}
            for i, s in enumerate(STATUS_FLOW)]


@app.get("/", response_class=HTMLResponse)
def menu_page(request: Request, category_id: int | None = None,
              search: str | None = None, track_id: int | None = None,
              track_phone: str = "", db: Session = Depends(get_db)):
    client = get_current_client(request, db)
    tracked = None
    if track_id:
        order = db.get(Order, track_id)
        owner = db.get(Client, order.client_id) if order and order.client_id else None
        if order and owner and _digits(owner.phone) == _digits(track_phone):
            tracked = order
    active_orders = []
    if client:
        for o in order_service.list_orders(db, client_id=client.id, limit=10):
            if o.status in ("new", "cooking", "ready", "served"):
                active_orders.append({
                    "id": o.id, "status": o.status, "total": o.total_sum,
                    "payable": o.status in ("ready", "served")})
    return templates.TemplateResponse(request, "menu.html", {
        "dishes": menu_service.list_dishes(db, category_id, search=search),
        "categories": menu_service.list_categories(db),
        "active_category": category_id,
        "search": search or "",
        "cat_icons": {c.id: c.icon for c in menu_service.list_categories(db)},
        "client": client,
        "unread": notification_service.unread_client_count(db, client.id)
                  if client else 0,
        "active_orders": active_orders,
        "tracked": tracked,
        "track_id": track_id,
    })


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request, message: str | None = None,
                  db: Session = Depends(get_db)):
    return templates.TemplateResponse(request, "register.html", {
        "message": message, "client": get_current_client(request, db)})


@app.post("/register")
def register(full_name: str = Form(...), phone: str = Form(...),
             password: str = Form(...), db: Session = Depends(get_db)):
    if len(password) < 4:
        return RedirectResponse("/register?message=Пароль слишком короткий", 303)
    try:
        client = customer_service.register_client(
            db, full_name=full_name, phone=phone, password=password)
    except ValueError as e:
        return RedirectResponse(f"/register?message={quote(str(e))}", 303)
    return set_client_cookie(RedirectResponse("/", 303), client)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, message: str | None = None,
               db: Session = Depends(get_db)):
    return templates.TemplateResponse(request, "login.html", {
        "message": message, "client": get_current_client(request, db)})


@app.post("/login")
def login(phone: str = Form(...), password: str = Form(...),
          db: Session = Depends(get_db)):
    client = customer_service.authenticate_client(db, phone, password)
    if not client:
        return RedirectResponse("/login?message=Неверный телефон или пароль", 303)
    return set_client_cookie(RedirectResponse("/", 303), client)


@app.get("/logout")
def logout():
    response = RedirectResponse("/", 303)
    response.delete_cookie("client_id")
    return response


@app.post("/order/create")
def create_order(request: Request, order_type: str = Form("takeaway"),
                 table_number: int | None = Form(None),
                 address: str = Form(None), comment: str = Form(None),
                 items_json: str = Form(...), db: Session = Depends(get_db)):
    client = get_current_client(request, db)
    if not client:
        return RedirectResponse("/login?message=Войдите, чтобы оформить заказ", 303)
    try:
        items = [(int(i["id"]), int(i["qty"])) for i in json.loads(items_json)]
    except (ValueError, KeyError, TypeError):
        return RedirectResponse("/?message=Некорректные данные корзины", 303)
    if not items:
        return RedirectResponse("/?message=Корзина пуста", 303)
    try:
        order = order_service.create_order(
            db, order_type=order_type, table_number=table_number,
            client_id=client.id, comment=comment,
            address=address if order_type == "delivery" else None,
            items=items)
    except ValueError as e:
        return RedirectResponse(f"/?message={quote(str(e))}", 303)
    return RedirectResponse(f"/order/{order.id}", 303)


@app.get("/order/{order_id}", response_class=HTMLResponse)
def order_status_page(request: Request, order_id: int,
                      db: Session = Depends(get_db)):
    client = get_current_client(request, db)
    if not client:
        return RedirectResponse("/login?message=Войдите, чтобы смотреть заказы", 303)
    order = db.get(Order, order_id)
    if not order or order.client_id != client.id:
        return RedirectResponse("/my-orders?message=Заказ не найден", 303)
    return templates.TemplateResponse(request, "order_status.html", {
        "order": order, "client": client,
        "unread": notification_service.unread_client_count(db, client.id),
        "items": order.items,
        "steps": build_timeline(order)})


@app.get("/my-orders", response_class=HTMLResponse)
def my_orders(request: Request, message: str | None = None,
              db: Session = Depends(get_db)):
    client = get_current_client(request, db)
    if not client:
        return RedirectResponse("/login?message=Войдите, чтобы смотреть заказы", 303)
    orders = order_service.list_orders(db, client_id=client.id, limit=20)
    return templates.TemplateResponse(request, "my_orders.html", {
        "client": client, "unread": notification_service.unread_client_count(db, client.id),
        "orders": orders,
        "titles": STATUS_TITLES, "message": message})



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)