from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from restoflow.database import get_db
from restoflow.models import Client
from restoflow.services import feedback_service, notification_service
from restoflow.utils import validators as V

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def _client(request: Request, db: Session) -> Client | None:
    raw = request.cookies.get("client_id")
    return db.get(Client, int(raw)) if raw and raw.isdigit() else None


@router.get("/reviews", response_class=HTMLResponse)
def reviews_page(request: Request, message: str | None = None,
                 db: Session = Depends(get_db)):
    client = _client(request, db)
    return templates.TemplateResponse(request, "reviews.html", {
        "client": client,
        "message": message,
        "reviews": feedback_service.list_feedback_detailed(db, 100),
        "stats": feedback_service.rating_stats(db),
        "unread": notification_service.unread_client_count(db, client.id)
                  if client else 0,
    })


@router.post("/reviews/create")
def reviews_create(request: Request, rating: int = Form(...),
                   comment: str = Form(None),
                   is_anonymous: str = Form(None),
                   db: Session = Depends(get_db)):
    client = _client(request, db)
    if not client:
        return RedirectResponse(
            "/login?message=Войдите, чтобы оставить отзыв", 303)
    try:
        feedback_service.create_feedback(
            db, client_id=client.id, rating=rating, comment=comment,
            is_anonymous=is_anonymous == "on")
    except V.ValidationError as e:
        return RedirectResponse(f"/reviews?message={quote(str(e))}", 303)
    return RedirectResponse("/reviews?message=✅ Спасибо за отзыв!", 303)