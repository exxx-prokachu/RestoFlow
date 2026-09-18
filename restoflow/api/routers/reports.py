from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from restoflow.api.schemas import KpiOut
from restoflow.api.security import require_roles
from restoflow.database import get_db
from restoflow.models import User, UserRole
from restoflow.services import report_service

router = APIRouter(prefix="/api/reports", tags=["reports"])
managers = require_roles(UserRole.ADMIN, UserRole.MANAGER)


@router.get("/dashboard", response_model=KpiOut)
def dashboard(db: Session = Depends(get_db), user: User = Depends(managers)):
    return report_service.dashboard_kpi(db)


@router.get("/top-dishes")
def top_dishes(limit: int = 5, db: Session = Depends(get_db),
               user: User = Depends(managers)):
    return [{"name": n, "qty": q}
            for n, q in report_service.top_dishes(db, limit)]


@router.get("/revenue")
def revenue(days: int = 7, db: Session = Depends(get_db),
            user: User = Depends(managers)):
    return report_service.revenue_by_day(db, days)


@router.get("/orders-by-status")
def orders_by_status(db: Session = Depends(get_db),
                     user: User = Depends(managers)):
    return report_service.orders_by_status(db)


@router.get("/payments")
def payments(db: Session = Depends(get_db),
             user: User = Depends(managers)):
    return report_service.payments_summary(db)