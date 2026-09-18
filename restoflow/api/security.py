from datetime import datetime, timedelta

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from restoflow.api.config import ALGORITHM, SECRET_KEY, TOKEN_TTL_MINUTES
from restoflow.database import get_db
from restoflow.models import User, UserRole

bearer = HTTPBearer()


def create_token(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role_value(),
        "exp": datetime.utcnow() + timedelta(minutes=TOKEN_TTL_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(bearer),
        db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY,
                             algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Пользователь недоступен")
    return user


def require_roles(*roles: UserRole):
    allowed = {r.value for r in roles}

    def guard(user: User = Depends(get_current_user)) -> User:
        if user.role_value() not in allowed:
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        return user

    return guard


def optional_user(
        credentials: HTTPAuthorizationCredentials = Depends(
            HTTPBearer(auto_error=False)),
        db: Session = Depends(get_db)) -> User | None:
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY,
                             algorithms=[ALGORITHM])
        return db.get(User, int(payload["sub"]))
    except Exception:
        return None