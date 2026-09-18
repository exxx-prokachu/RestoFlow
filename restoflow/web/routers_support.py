from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from restoflow.database import get_db
from restoflow.models import Client
from restoflow.services import notification_service, support_service
from restoflow.utils import validators as V

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def _client(request: Request, db: Session) -> Client | None:
    raw = request.cookies.get("client_id")
    return db.get(Client, int(raw)) if raw and raw.isdigit() else None


def _back(message: str, url: str):
    return RedirectResponse(f"{url}?message={quote(message)}", 303)


@router.get("/support", response_class=HTMLResponse)
def support_list(request: Request, message: str | None = None,
                 db: Session = Depends(get_db)):
    client = _client(request, db)
    if not client:
        return _back("Войдите в аккаунт", "/login")
    return templates.TemplateResponse(request, "support_list.html", {
        "client": client, "message": message,
        "requests": support_service.list_for_client(db, client.id),
        "unread": notification_service.unread_client_count(db, client.id)})


@router.post("/support/create")
def support_create(request: Request, subject: str = Form(...),
                   body: str = Form(...), db: Session = Depends(get_db)):
    client = _client(request, db)
    if not client:
        return _back("Войдите в аккаунт", "/login")
    try:
        req = support_service.create_request(
            db, client_id=client.id, subject=subject, body=body)
    except V.ValidationError as e:
        return _back(f"❌ {e}", "/support")
    return RedirectResponse(f"/support/{req.id}?message=✅ Обращение создано", 303)


@router.get("/support/{request_id}", response_class=HTMLResponse)
def support_detail(request: Request, request_id: int,
                   message: str | None = None, db: Session = Depends(get_db)):
    client = _client(request, db)
    if not client:
        return _back("Войдите в аккаунт", "/login")
    req = support_service.get_request(db, request_id)
    if not req or req.client_id != client.id:
        return _back("Обращение не найдено", "/support")
    return templates.TemplateResponse(request, "support_detail.html", {
        "client": client, "request_obj": req, "message": message,
        "unread": notification_service.unread_client_count(db, client.id)})


@router.post("/support/{request_id}/message")
def support_message(request: Request, request_id: int, body: str = Form(...),
                    db: Session = Depends(get_db)):
    client = _client(request, db)
    if not client:
        return _back("Войдите в аккаунт", "/login")
    try:
        support_service.add_client_message(db, request_id, client.id, body)
    except (ValueError, V.ValidationError) as e:
        return _back(f"❌ {e}", f"/support/{request_id}")
    return RedirectResponse(f"/support/{request_id}?message=✅ Сообщение отправлено", 303)


@router.post("/support/{request_id}/close")
def support_close(request: Request, request_id: int,
                  db: Session = Depends(get_db)):
    client = _client(request, db)
    if not client:
        return _back("Войдите в аккаунт", "/login")
    try:
        support_service.close_request(db, request_id, by_client=True)
    except ValueError as e:
        return _back(f"❌ {e}", f"/support/{request_id}")
    return RedirectResponse(f"/support/{request_id}?message=✅ Обращение закрыто", 303)


@router.post("/support/{request_id}/reopen")
def support_reopen(request: Request, request_id: int, body: str = Form(...),
                   db: Session = Depends(get_db)):
    client = _client(request, db)
    if not client:
        return _back("Войдите в аккаунт", "/login")
    try:
        support_service.reopen_request(db, request_id, client.id, body)
    except (ValueError, V.ValidationError) as e:
        return _back(f"❌ {e}", f"/support/{request_id}")
    return RedirectResponse(f"/support/{request_id}?message=✅ Обращение возобновлено", 303)