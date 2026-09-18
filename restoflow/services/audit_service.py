from sqlalchemy.orm import Session

from restoflow.models import AuditLog


def log_action(db: Session, action: str, entity: str,
               details: str, user_info: str | None = None,
               entity_id: int | None = None) -> None:
    db.add(AuditLog(action=action, entity=entity, details=details,
                    user_info=user_info, entity_id=entity_id))
    db.commit()


def list_logs(db: Session, limit: int = 100,
              action: str | None = None) -> list[AuditLog]:
    q = db.query(AuditLog)
    if action:
        q = q.filter(AuditLog.action == action)
    return q.order_by(AuditLog.created_at.desc()).limit(limit).all()