from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from restoflow.events import publish
from restoflow.models import Client, Feedback
from restoflow.services.audit_service import log_action
from restoflow.utils import validators as V


def create_feedback(db: Session, *, client_id: int | None, rating: int,
                    comment: str | None = None,
                    is_anonymous: bool = False) -> Feedback:
    V.validate_rating(rating)
    text = V.validate_text(comment, 1000, "Комментарий")
    fb = Feedback(client_id=client_id, rating=rating, comment=text,
                  is_anonymous=bool(is_anonymous))
    db.add(fb)
    db.commit()
    db.refresh(fb)
    publish("feedback.created", feedback_id=fb.id)
    log_action(db, "FEEDBACK_CREATE", "Feedback",
               f"Оценка {rating}" + (" (анонимно)" if fb.is_anonymous else ""),
               None, fb.id)
    return fb


def author_name(db: Session, fb: Feedback) -> str:
    if fb.is_anonymous:
        return "Аноним"
    if fb.client_id is None:
        return "Гость"
    client = db.get(Client, fb.client_id)
    return client.full_name if client else "Клиент"


def list_feedback_detailed(db: Session, limit: int = 100) -> list[dict]:
    rows = db.query(Feedback).order_by(
        Feedback.created_at.desc()).limit(limit).all()
    return [{
        "id": fb.id, "rating": fb.rating, "comment": fb.comment,
        "reply": fb.reply, "replied_at": fb.replied_at,
        "created_at": fb.created_at, "is_anonymous": fb.is_anonymous,
        "author": author_name(db, fb),
    } for fb in rows]


def list_feedback(db: Session, limit: int = 50) -> list[Feedback]:
    return db.query(Feedback).order_by(
        Feedback.created_at.desc()).limit(limit).all()


def reply_feedback(db: Session, feedback_id: int, reply: str) -> Feedback | None:
    fb = db.get(Feedback, feedback_id)
    if not fb:
        return None
    fb.reply = V.validate_text(reply, 1000, "Ответ")
    fb.replied_at = datetime.now(timezone.utc)
    db.commit()
    publish("feedback.replied", feedback_id=fb.id)
    log_action(db, "FEEDBACK_REPLY", "Feedback",
               f"ID={feedback_id}", None, feedback_id)
    return fb


def rating_stats(db: Session) -> dict:
    avg = db.query(func.avg(Feedback.rating)).scalar() or 0
    count = db.query(Feedback).count()
    dist = {star: 0 for star in range(1, 6)}
    for star, cnt in db.query(Feedback.rating, func.count(Feedback.id)
                              ).group_by(Feedback.rating).all():
        if star in dist:
            dist[star] = cnt
    return {"average": round(avg, 2), "count": count, "distribution": dist}