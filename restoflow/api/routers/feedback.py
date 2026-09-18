from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from restoflow.api.schemas import FeedbackOut
from restoflow.api.security import require_roles
from restoflow.database import get_db
from restoflow.models import User, UserRole
from restoflow.services import feedback_service

router = APIRouter(prefix="/api/feedback", tags=["feedback"])
managers = require_roles(UserRole.ADMIN, UserRole.MANAGER)


class FeedbackIn(BaseModel):
    client_id: int | None = None
    rating: int
    comment: str | None = None


class ReplyIn(BaseModel):
    reply: str


@router.post("", status_code=201, response_model=FeedbackOut)
def create_feedback(body: FeedbackIn, db: Session = Depends(get_db)):
    return feedback_service.create_feedback(db, **body.model_dump())


@router.get("", response_model=list[FeedbackOut])
def list_feedback(limit: int = 50, db: Session = Depends(get_db)):
    return feedback_service.list_feedback(db, limit=limit)


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    return feedback_service.rating_stats(db)


@router.post("/{feedback_id}/reply", response_model=FeedbackOut)
def reply(feedback_id: int, body: ReplyIn, db: Session = Depends(get_db),
          user: User = Depends(managers)):
    fb = feedback_service.reply_feedback(db, feedback_id, body.reply)
    if not fb:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    return fb