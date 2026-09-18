from datetime import datetime, timezone

from sqlalchemy.orm import Session

from restoflow.models import User, UserRole
from restoflow.services.audit_service import log_action


def authenticate(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(
        User.username == username, User.is_active == True).first()
    if user and user.check_password(password):
        user.last_login_at = datetime.now(timezone.utc)
        db.commit()
        log_action(db, "LOGIN", "User", f"Вход: {username}", username, user.id)
        return user
    log_action(db, "LOGIN_FAIL", "User", f"Неудачный вход: {username}", username)
    return None


def create_user(db: Session, username: str, full_name: str,
                password: str, role: UserRole = UserRole.CASHIER) -> User:
    from restoflow.utils import validators as V
    login = V.validate_username(username)
    name = V.validate_full_name(full_name)
    V.validate_password(password)
    existing = db.query(User).filter(User.username == login).first()
    if existing:
        return existing
    user = User(username=login, full_name=name, role=role.value)
    user.set_password(password)
    db.add(user)
    db.commit()
    db.refresh(user)
    log_action(db, "USER_CREATE", "User", f"Создан: {login}", None, user.id)
    return user


def list_users(db: Session, include_inactive: bool = True) -> list[User]:
    q = db.query(User)
    if not include_inactive:
        q = q.filter(User.is_active == True)
    return q.order_by(User.created_at.desc()).all()


def toggle_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user:
        raise ValueError("Пользователь не найден")
    if user.username == "admin":
        raise ValueError("Нельзя заблокировать главного администратора")
    user.is_active = not user.is_active
    db.commit()
    log_action(db, "USER_TOGGLE", "User",
               f"ID={user_id} active={user.is_active}", None, user_id)
    return user


def change_password(db: Session, user_id: int, new_password: str) -> User:
    from restoflow.utils import validators as V
    V.validate_password(new_password)
    user = db.get(User, user_id)
    if not user:
        raise ValueError("Пользователь не найден")
    user.set_password(new_password)
    db.commit()
    log_action(db, "USER_PASSWORD", "User", f"ID={user_id}", None, user_id)
    return user


def update_user(db: Session, user_id: int, *, full_name: str | None = None,
                role: str | None = None, new_password: str | None = None) -> User | None:
    user = db.get(User, user_id)
    if not user:
        return None
    if full_name is not None:
        user.full_name = full_name
    if role is not None:
        user.role = role
    if new_password:
        user.set_password(new_password)
    db.commit()
    log_action(db, "USER_UPDATE", "User", f"ID={user_id}", None, user_id)
    return user