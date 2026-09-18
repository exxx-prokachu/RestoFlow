from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from restoflow.api.schemas import CategoryOut, DishOut
from restoflow.api.security import require_roles
from restoflow.database import get_db
from restoflow.models import User, UserRole
from restoflow.services import menu_service

router = APIRouter(prefix="/api/menu", tags=["menu"])
staff = require_roles(UserRole.ADMIN, UserRole.MANAGER)


class DishIn(BaseModel):
    category_id: int
    name: str
    price: float
    weight: str | None = None
    description: str | None = None


class CategoryIn(BaseModel):
    name: str
    icon: str = "🍽️"


@router.get("/categories", response_model=list[CategoryOut])
def categories(db: Session = Depends(get_db)):
    return menu_service.list_categories(db)


@router.post("/categories", status_code=201, response_model=CategoryOut)
def create_category(body: CategoryIn, db: Session = Depends(get_db),
                    user: User = Depends(staff)):
    return menu_service.create_category(db, name=body.name, icon=body.icon)


@router.get("", response_model=list[DishOut])
def dishes(category_id: int | None = None, include_stopped: bool = False,
           search: str | None = None, db: Session = Depends(get_db)):
    return menu_service.list_dishes(db, category_id, include_stopped, search)


@router.post("", status_code=201, response_model=DishOut)
def create_dish(body: DishIn, db: Session = Depends(get_db),
                user: User = Depends(staff)):
    return menu_service.create_dish(db, **body.model_dump())


@router.patch("/{dish_id}", response_model=DishOut)
def update_dish(dish_id: int, body: DishIn, db: Session = Depends(get_db),
                user: User = Depends(staff)):
    dish = menu_service.update_dish(db, dish_id, **body.model_dump())
    if not dish:
        raise HTTPException(status_code=404, detail="Блюдо не найдено")
    return dish


@router.post("/{dish_id}/stoplist", response_model=DishOut)
def stoplist(dish_id: int, db: Session = Depends(get_db),
             user: User = Depends(staff)):
    dish = menu_service.toggle_stoplist(db, dish_id)
    if not dish:
        raise HTTPException(status_code=404, detail="Блюдо не найдено")
    return dish


@router.delete("/{dish_id}", status_code=204)
def delete_dish(dish_id: int, db: Session = Depends(get_db),
                user: User = Depends(staff)):
    if not menu_service.delete_dish(db, dish_id):
        raise HTTPException(status_code=404, detail="Блюдо не найдено")