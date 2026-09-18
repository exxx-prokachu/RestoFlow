from sqlalchemy.orm import Session

from restoflow.models import Notification, User, UserRole


def push(db: Session, *, title: str, message: str | None,
         kind: str = "info", user_id: int | None = None) -> Notification:
    n = Notification(title=title, message=message, kind=kind, user_id=user_id)
    db.add(n)
    db.commit()
    db.refresh(n)
    return n


def push_to_all_staff(db: Session, *, title: str, message: str | None,
                     kind: str = "info") -> None:
    push(db, title=title, message=message, kind=kind, user_id=None)


def list_for_user(db: Session, user: User,
                  limit: int = 50) -> list[Notification]:
    role = user.role_value()
    q = db.query(Notification).order_by(Notification.created_at.desc())
    if role not in (UserRole.ADMIN.value, UserRole.MANAGER.value):
        q = q.filter(Notification.user_id == user.id)
    return q.limit(limit).all()


def unread_count(db: Session, user: User) -> int:
    role = user.role_value()
    q = db.query(Notification).filter(Notification.is_read == False)
    if role in (UserRole.ADMIN.value, UserRole.MANAGER.value):
        q = q.filter((Notification.user_id == None) |
                     (Notification.user_id == user.id))
    else:
        q = q.filter(Notification.user_id == user.id)
    return q.count()


def mark_read(db: Session, notification_id: int) -> Notification | None:
    n = db.get(Notification, notification_id)
    if n:
        n.is_read = True
        db.commit()
    return n


def mark_all_read(db: Session, user: User) -> int:
    role = user.role_value()
    q = db.query(Notification).filter(Notification.is_read == False)
    if role in (UserRole.ADMIN.value, UserRole.MANAGER.value):
        q = q.filter((Notification.user_id == None) |
                     (Notification.user_id == user.id))
    else:
        q = q.filter(Notification.user_id == user.id)
    count = q.update({"is_read": True})
    db.commit()
    return count

def push_to_client(db: Session, client_id: int, *, title: str,
                   message: str | None, kind: str = "info") -> Notification:
    n = Notification(title=title, message=message, kind=kind, client_id=client_id)
    db.add(n)
    db.commit()
    db.refresh(n)
    return n


def list_for_client(db: Session, client_id: int, limit: int = 50) -> list[Notification]:
    return db.query(Notification).filter(
        Notification.client_id == client_id
    ).order_by(Notification.created_at.desc()).limit(limit).all()


def unread_client_count(db: Session, client_id: int) -> int:
    return db.query(Notification).filter(
        Notification.client_id == client_id,
        Notification.is_read == False).count()


def mark_client_read(db: Session, notification_id: int,
                     client_id: int) -> Notification | None:
    n = db.get(Notification, notification_id)
    if n and n.client_id == client_id:
        n.is_read = True
        db.commit()
        return n
    return None


def mark_client_all_read(db: Session, client_id: int) -> int:
    count = db.query(Notification).filter(
        Notification.client_id == client_id,
        Notification.is_read == False).update({"is_read": True})
    db.commit()
    return count