from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CategoryOut(ORMModel):
    id: int
    name: str
    icon: str


class DishOut(ORMModel):
    id: int
    category_id: int
    name: str
    price: float
    weight: str | None
    description: str | None
    is_available: bool


class OrderItemOut(ORMModel):
    id: int
    dish_id: int
    qty: int
    price: float


class OrderOut(ORMModel):
    id: int
    client_id: int | None
    table_number: int | None
    order_type: str
    status: str
    total_sum: float
    discount_percent: int
    created_at: datetime
    items: list[OrderItemOut] = []
    comment: str | None = None


class ClientOut(ORMModel):
    id: int
    full_name: str
    phone: str
    email: str | None
    loyalty_points: int
    visits_count: int
    total_spent: float


class FeedbackOut(ORMModel):
    id: int
    client_id: int | None
    rating: int
    comment: str | None
    reply: str | None
    created_at: datetime


class NotificationOut(ORMModel):
    id: int
    title: str
    message: str | None
    kind: str
    is_read: bool
    created_at: datetime


class KpiOut(BaseModel):
    revenue_today: float
    revenue_month: float
    active_orders: int
    avg_check: float
    stoplist: int
    clients_total: int


class AuditLogOut(ORMModel):
    id: int
    action: str
    entity: str | None
    details: str | None
    user_info: str | None
    created_at: datetime