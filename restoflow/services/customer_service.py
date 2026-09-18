import re

from sqlalchemy.orm import Session

from restoflow.events import publish
from restoflow.models import Client
from restoflow.services.audit_service import log_action


def normalize_phone(phone: str) -> str:
    return re.sub(r"\D", "", phone or "")


def list_clients(db: Session, search: str | None = None) -> list[Client]:
    clients = db.query(Client).order_by(Client.full_name).all()
    if search:
        needle = search.strip().lower()
        if needle:
            clients = [c for c in clients
                       if needle in c.full_name.lower()
                       or needle in c.phone.lower()]
    return clients


def get_client(db: Session, client_id: int) -> Client | None:
    return db.get(Client, client_id)


def get_client_by_phone(db: Session, phone: str) -> Client | None:
    digits = normalize_phone(phone)
    if not digits:
        return None
    for client in db.query(Client).all():
        if normalize_phone(client.phone) == digits:
            return client
    return None


def create_client(db: Session, *, full_name: str, phone: str,
                  email: str | None = None) -> Client:
    existing = get_client_by_phone(db, phone)
    if existing:
        return existing
    client = Client(full_name=full_name.strip(), phone=phone.strip(), email=email)
    db.add(client)
    db.commit()
    db.refresh(client)
    publish("client.registered", client_id=client.id)
    return client


def register_client(db: Session, *, full_name: str, phone: str,
                    password: str) -> Client:
    from restoflow.utils import validators as V
    name = V.validate_full_name(full_name)
    digits = V.validate_phone(phone)
    V.validate_password(password)
    if get_client_by_phone(db, phone):
        raise V.ValidationError("Телефон уже зарегистрирован")
    client = Client(full_name=name, phone="+" + digits)
    client.set_password(password)
    db.add(client)
    db.commit()
    db.refresh(client)
    publish("client.registered", client_id=client.id)
    log_action(db, "CLIENT_REGISTER", "Client", client.phone, None, client.id)
    return client


def authenticate_client(db: Session, phone: str,
                        password: str) -> Client | None:
    client = get_client_by_phone(db, phone)
    if not client or client.is_active is False:
        return None
    if client.check_password(password):
        log_action(db, "CLIENT_LOGIN", "Client", client.phone, None, client.id)
        return client
    return None


def toggle_active(db: Session, client_id: int) -> Client | None:
    client = db.get(Client, client_id)
    if not client:
        return None
    client.is_active = client.is_active is False
    db.commit()
    log_action(db, "CLIENT_TOGGLE", "Client",
               f"ID={client_id} active={client.is_active is not False}",
               None, client_id)
    return client


def update_client(db: Session, client_id: int, **fields) -> Client | None:
    client = db.get(Client, client_id)
    if not client:
        return None
    for key, value in fields.items():
        if hasattr(client, key):
            setattr(client, key, value)
    db.commit()
    return client