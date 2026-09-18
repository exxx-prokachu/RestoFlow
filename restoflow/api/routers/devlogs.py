import re

from fastapi import APIRouter, Depends, HTTPException

from restoflow.api.config import LOG_DIR
from restoflow.api.security import require_roles
from restoflow.models import User, UserRole

router = APIRouter(tags=["dev"])


@router.get("/api/admin/dev-logs")
def dev_logs(service: str = "gateway", tail: int = 200,
             user: User = Depends(require_roles(UserRole.ADMIN))):
    if not re.fullmatch(r"[a-z_]+", service):
        raise HTTPException(status_code=400, detail="Некорректное имя сервиса")
    path = LOG_DIR / f"{service}.log"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Лог-файл не найден")
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines()[-tail:]:
        parts = [p.strip() for p in line.split(" | ", 2)]
        if len(parts) == 3:
            entries.append({"time": parts[0], "level": parts[1],
                            "message": parts[2]})
        else:
            entries.append({"time": "", "level": "INFO", "message": line})
    return entries


@router.get("/api/admin/audit")
def audit(limit: int = 100, action: str | None = None,
          user: User = Depends(require_roles(UserRole.ADMIN))):
    from restoflow.database import SessionLocal
    from restoflow.services import audit_service
    db = SessionLocal()
    try:
        return [{"id": l.id, "action": l.action, "entity": l.entity,
                 "details": l.details, "user_info": l.user_info,
                 "created_at": l.created_at.isoformat()}
                for l in audit_service.list_logs(db, limit=limit, action=action)]
    finally:
        db.close()