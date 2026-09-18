from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from restoflow.api.logconf import get_logger
from restoflow.api.security import create_token, get_current_user
from restoflow.database import get_db
from restoflow.models import User
from restoflow.services.auth_service import authenticate

router = APIRouter(prefix="/api/auth", tags=["auth"])
log = get_logger("auth")


class LoginRequest(BaseModel):
    username: str
    password: str


class MeOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate(db, body.username, body.password)
    if not user:
        log.warning("LOGIN_FAIL | user=%s", body.username)
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    log.info("LOGIN | user=%s role=%s", user.username, user.role_value())
    return {"access_token": create_token(user), "token_type": "bearer"}


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "username": user.username,
            "full_name": user.full_name, "role": user.role_value()}