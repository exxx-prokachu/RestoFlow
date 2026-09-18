from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from restoflow.api.schemas import NotificationOut
from restoflow.api.security import get_current_user
from restoflow.database import get_db
from restoflow.models import User
from restoflow.services import notification_service

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
def list_notifications(user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    return notification_service.list_for_user(db, user)


@router.get("/unread-count")
def unread_count(user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    return {"count": notification_service.unread_count(db, user)}


@router.post("/{notification_id}/read")
def mark_read(notification_id: int, user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    if not notification_service.mark_read(db, notification_id):
        raise HTTPException(status_code=404, detail="Уведомление не найдено")
    return {"success": True}


@router.post("/read-all")
def mark_all_read(user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    return {"count": notification_service.mark_all_read(db, user)}