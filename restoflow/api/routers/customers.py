from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from restoflow.api.schemas import ClientOut
from restoflow.api.security import require_roles
from restoflow.database import get_db
from restoflow.models import User, UserRole
from restoflow.services import customer_service

router = APIRouter(prefix="/api/customers", tags=["customers"])
staff = require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.CASHIER)


class ClientIn(BaseModel):
    full_name: str
    phone: str
    email: str | None = None


@router.get("", response_model=list[ClientOut])
def list_clients(search: str | None = None, db: Session = Depends(get_db),
                 user: User = Depends(staff)):
    return customer_service.list_clients(db, search=search)


@router.post("", status_code=201, response_model=ClientOut)
def create_client(body: ClientIn, db: Session = Depends(get_db),
                  user: User = Depends(staff)):
    return customer_service.create_client(db, **body.model_dump())


@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: int, db: Session = Depends(get_db),
               user: User = Depends(staff)):
    client = customer_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return client


@router.get("/by-phone/{phone}", response_model=ClientOut)
def by_phone(phone: str, db: Session = Depends(get_db),
             user: User = Depends(staff)):
    client = customer_service.get_client_by_phone(db, phone)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return client