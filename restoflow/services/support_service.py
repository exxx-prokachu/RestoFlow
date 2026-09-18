from datetime import datetime, timezone

from sqlalchemy.orm import Session

from restoflow.models import (Client, SupportMessage, SupportRequest,
                              SupportStatus)
from restoflow.services import notification_service
from restoflow.services.audit_service import log_action
from restoflow.utils import validators as V


def create_request(db: Session, *, client_id: int, subject: str,
                   body: str) -> SupportRequest:
    title = (V.validate_text(subject, 160, "Тема") or "").strip()
    if len(title) < 5:
        raise V.ValidationError("Тема: минимум 5 символов")
    text = V.validate_text(body, 2000, "Сообщение") or ""
    if not text:
        raise V.ValidationError("Сообщение: не может быть пустым")
    client = db.get(Client, client_id)
    req = SupportRequest(client_id=client_id, subject=title,
                         status=SupportStatus.OPEN.value)
    db.add(req)
    db.commit()
    db.refresh(req)
    req.messages.append(SupportMessage(
        sender_type="client",
        sender_name=client.full_name if client else "Клиент",
        body=text))
    db.commit()
    notification_service.push_to_all_staff(
        db, title=f"🛟 Новое обращение #{req.id}", message=title, kind="support")
    log_action(db, "SUPPORT_CREATE", "SupportRequest",
               f"#{req.id}: {title}", None, req.id)
    return req


def list_for_client(db: Session, client_id: int,
                    limit: int = 50) -> list[SupportRequest]:
    return db.query(SupportRequest).filter(
        SupportRequest.client_id == client_id
    ).order_by(SupportRequest.updated_at.desc()).limit(limit).all()


def list_all(db: Session, status: str | None = None,
             limit: int = 100) -> list[SupportRequest]:
    q = db.query(SupportRequest)
    if status:
        q = q.filter(SupportRequest.status == status)
    return q.order_by(SupportRequest.updated_at.desc()).limit(limit).all()


def get_request(db: Session, request_id: int) -> SupportRequest | None:
    return db.get(SupportRequest, request_id)


def open_count(db: Session) -> int:
    return db.query(SupportRequest).filter(
        SupportRequest.status.in_([SupportStatus.OPEN.value,
                                   SupportStatus.IN_PROGRESS.value])).count()


def _touch(req: SupportRequest) -> None:
    req.updated_at = datetime.now(timezone.utc)


def add_client_message(db: Session, request_id: int, client_id: int,
                       body: str) -> SupportMessage:
    req = db.get(SupportRequest, request_id)
    if not req or req.client_id != client_id:
        raise ValueError("Обращение не найдено")
    if req.status == SupportStatus.CLOSED.value:
        raise ValueError("Обращение закрыто — сначала возобновите")
    text = V.validate_text(body, 2000, "Сообщение") or ""
    if not text:
        raise V.ValidationError("Сообщение: не может быть пустым")
    client = db.get(Client, client_id)
    msg = SupportMessage(sender_type="client",
                         sender_name=client.full_name if client else "Клиент",
                         body=text)
    req.messages.append(msg)
    if req.status == SupportStatus.OPEN.value:
        req.status = SupportStatus.IN_PROGRESS.value
    _touch(req)
    db.commit()
    notification_service.push_to_all_staff(
        db, title=f"📨 Ответ клиента в обращении #{request_id}",
        message=text[:100], kind="support")
    return msg


def add_staff_message(db: Session, request_id: int, staff_name: str,
                      body: str) -> SupportMessage:
    req = db.get(SupportRequest, request_id)
    if not req:
        raise ValueError("Обращение не найдено")
    if req.status == SupportStatus.CLOSED.value:
        raise ValueError("Обращение закрыто")
    text = V.validate_text(body, 2000, "Сообщение") or ""
    if not text:
        raise V.ValidationError("Сообщение: не может быть пустым")
    msg = SupportMessage(sender_type="staff",
                         sender_name=staff_name, body=text)
    req.messages.append(msg)
    if req.status == SupportStatus.OPEN.value:
        req.status = SupportStatus.IN_PROGRESS.value
    _touch(req)
    db.commit()
    notification_service.push_to_client(
        db, req.client_id,
        title=f"💬 Ответ поддержки в обращении #{request_id}",
        message=text[:100], kind="support")
    log_action(db, "SUPPORT_REPLY", "SupportRequest",
               f"#{request_id}", staff_name, request_id)
    return msg


def close_request(db: Session, request_id: int,
                  by_client: bool = False) -> SupportRequest:
    req = db.get(SupportRequest, request_id)
    if not req:
        raise ValueError("Обращение не найдено")
    if req.status == SupportStatus.CLOSED.value:
        raise ValueError("Обращение уже закрыто")
    req.status = SupportStatus.CLOSED.value
    req.closed_at = datetime.now(timezone.utc)
    _touch(req)
    db.commit()
    if by_client:
        notification_service.push_to_all_staff(
            db, title=f"🔒 Клиент закрыл обращение #{request_id}",
            message=None, kind="support")
    else:
        notification_service.push_to_client(
            db, req.client_id, title=f"🔒 Обращение #{request_id} закрыто",
            message="Спасибо за обращение!", kind="support")
    log_action(db, "SUPPORT_CLOSE", "SupportRequest",
               f"#{request_id}", None, request_id)
    return req


def reopen_request(db: Session, request_id: int, client_id: int,
                   body: str) -> SupportRequest:
    req = db.get(SupportRequest, request_id)
    if not req or req.client_id != client_id:
        raise ValueError("Обращение не найдено")
    if req.status != SupportStatus.CLOSED.value:
        raise ValueError("Обращение не закрыто")
    req.status = SupportStatus.IN_PROGRESS.value
    req.closed_at = None
    _touch(req)
    db.commit()
    add_client_message(db, request_id, client_id, body)
    return req