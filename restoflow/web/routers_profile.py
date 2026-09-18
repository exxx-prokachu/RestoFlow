from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from restoflow.database import get_db
from restoflow.models import Client
from restoflow.services import customer_service, notification_service
from restoflow.utils import validators as V
from restoflow.utils.mailer import send_email

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def _client(request: Request, db: Session) -> Client | None:
    raw = request.cookies.get("client_id")
    return db.get(Client, int(raw)) if raw and raw.isdigit() else None


def _back(message: str, url: str = "/profile"):
    return RedirectResponse(f"{url}?message={quote(message)}", 303)


@router.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request, message: str | None = None,
                 db: Session = Depends(get_db)):
    client = _client(request, db)
    if not client:
        return _back("Войдите в аккаунт", "/login")
    return templates.TemplateResponse(request, "profile.html", {
        "client": client, "message": message,
        "unread": notification_service.unread_client_count(db, client.id)})


@router.post("/profile/update")
def profile_update(request: Request, full_name: str = Form(...),
                   phone: str = Form(...), email: str = Form(None),
                   email_notifications: str = Form(None),
                   db: Session = Depends(get_db)):
    client = _client(request, db)
    if not client:
        return _back("Войдите в аккаунт", "/login")
    try:
        name = V.validate_full_name(full_name)
        digits = V.validate_phone(phone)
        mail = V.validate_email(email)
        other = customer_service.get_client_by_phone(db, phone)
        if other and other.id != client.id:
            raise V.ValidationError("Телефон занят другим аккаунтом")
        want_mail = email_notifications == "on"
        customer_service.update_client(
            db, client.id, full_name=name, phone="+" + digits, email=mail,
            email_notifications=want_mail)
        if mail and want_mail:
            send_email(mail, "RestoFlow: почта подключена",
                       "Статусы заказов будут дублироваться на этот адрес.")
        return _back("✅ Профиль обновлён")
    except V.ValidationError as e:
        return _back(f"❌ {e}")


@router.post("/profile/password")
def profile_password(request: Request, current: str = Form(...),
                     new: str = Form(...), confirm: str = Form(...),
                     db: Session = Depends(get_db)):
    client = _client(request, db)
    if not client:
        return _back("Войдите в аккаунт", "/login")
    if not client.check_password(current):
        return _back("❌ Текущий пароль неверен")
    if new != confirm:
        return _back("❌ Новый пароль и подтверждение не совпадают")
    try:
        V.validate_password(new)
    except V.ValidationError as e:
        return _back(f"❌ {e}")
    client.set_password(new)
    db.commit()
    if client.email and client.email_notifications:
        send_email(client.email, "RestoFlow: пароль изменён",
                   "Пароль аккаунта изменён. Если это не вы — смените пароль.")
    return _back("✅ Пароль изменён")


@router.post("/profile/theme")
def profile_theme(request: Request, theme: str = Form(...),
                  db: Session = Depends(get_db)):
    client = _client(request, db)
    if not client:
        return _back("Войдите в аккаунт", "/login")
    client.theme = theme if theme in ("light", "dark", "coffee") else "light"
    db.commit()
    return _back("✅ Тема применена")


@router.get("/notifications", response_class=HTMLResponse)
def notifications_page(request: Request, message: str | None = None,
                       db: Session = Depends(get_db)):
    client = _client(request, db)
    if not client:
        return _back("Войдите в аккаунт", "/login")
    return templates.TemplateResponse(request, "notifications.html", {
        "client": client, "message": message,
        "items": notification_service.list_for_client(db, client.id),
        "unread": notification_service.unread_client_count(db, client.id)})


@router.post("/notifications/{notification_id}/read")
def notification_read(request: Request, notification_id: int,
                      db: Session = Depends(get_db)):
    client = _client(request, db)
    if not client:
        return _back("Войдите в аккаунт", "/login")
    notification_service.mark_client_read(db, notification_id, client.id)
    return RedirectResponse("/notifications", 303)


@router.post("/notifications/read-all")
def notifications_read_all(request: Request, db: Session = Depends(get_db)):
    client = _client(request, db)
    if not client:
        return _back("Войдите в аккаунт", "/login")
    notification_service.mark_client_all_read(db, client.id)
    return RedirectResponse("/notifications", 303)