import hashlib
import secrets
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey,
                        Integer, String, Text)
from sqlalchemy.orm import relationship

from restoflow.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class UserRole(str, PyEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    CASHIER = "cashier"
    COOK = "cook"


class OrderStatus(str, PyEnum):
    NEW = "new"
    COOKING = "cooking"
    READY = "ready"
    SERVED = "served"
    PAID = "paid"
    CANCELLED = "cancelled"


class OrderType(str, PyEnum):
    DINE_IN = "dine_in"
    TAKEAWAY = "takeaway"
    DELIVERY = "delivery"


class PaymentMethod(str, PyEnum):
    CARD = "card"
    CASH = "cash"
    LOYALTY = "loyalty"


class FeedbackRating(str, PyEnum):
    ONE = "1"
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(120), nullable=False)
    password_hash = Column(String(128), nullable=False)
    salt = Column(String(32), nullable=False)
    role = Column(String(20), default=UserRole.CASHIER.value, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    last_login_at = Column(DateTime)

    def set_password(self, password: str) -> None:
        self.salt = secrets.token_hex(8)
        self.password_hash = hashlib.sha256(
            (password + self.salt).encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        if not self.salt:
            return False
        return hashlib.sha256(
            (password + self.salt).encode()).hexdigest() == self.password_hash

    def role_value(self) -> str:
        return self.role if isinstance(self.role, str) else self.role.value


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True, nullable=False)
    icon = Column(String(10), default="🍽️")
    sort_order = Column(Integer, default=0)
    dishes = relationship("Dish", back_populates="category")


class Dish(Base):
    __tablename__ = "dishes"
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    name = Column(String(120), nullable=False, index=True)
    description = Column(Text)
    price = Column(Float, nullable=False)
    weight = Column(String(30))
    image_path = Column(String(255))
    is_available = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    category = relationship("Category", back_populates="dishes")


class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True)
    full_name = Column(String(120), nullable=False)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(120))
    loyalty_points = Column(Integer, default=0, nullable=False)
    visits_count = Column(Integer, default=0, nullable=False)
    total_spent = Column(Float, default=0.0, nullable=False)
    theme = Column(String(20), default="light", nullable=False)
    email_notifications = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    password_hash = Column(String(128))
    salt = Column(String(32))

    def set_password(self, password: str) -> None:
        self.salt = secrets.token_hex(8)
        self.password_hash = hashlib.sha256(
            (password + self.salt).encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        if not self.salt:
            return False
        return hashlib.sha256(
            (password + self.salt).encode()).hexdigest() == self.password_hash


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    table_number = Column(Integer)
    order_type = Column(String(20), default=OrderType.DINE_IN.value, nullable=False)
    status = Column(String(20), default=OrderStatus.NEW.value, nullable=False, index=True)
    total_sum = Column(Float, default=0.0, nullable=False)
    discount_percent = Column(Integer, default=0, nullable=False)
    comment = Column(Text)
    address = Column(String(255))
    created_at = Column(DateTime, default=utcnow, nullable=False)
    closed_at = Column(DateTime)
    client = relationship("Client")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="order", uselist=False)

    def recalc_total(self) -> None:
        gross = sum(i.price * i.qty for i in self.items)
        discount = self.discount_percent or 0
        self.total_sum = round(gross * (1 - discount / 100), 2)


class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    dish_id = Column(Integer, ForeignKey("dishes.id"), nullable=False)
    qty = Column(Integer, default=1, nullable=False)
    price = Column(Float, nullable=False)
    order = relationship("Order", back_populates="items")
    dish = relationship("Dish")


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, unique=True)
    amount = Column(Float, nullable=False)
    method = Column(String(20), default=PaymentMethod.CARD.value, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    order = relationship("Order", back_populates="payment")


class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    rating = Column(Integer, default=5, nullable=False)
    comment = Column(Text)
    reply = Column(Text)
    replied_at = Column(DateTime)
    is_anonymous = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    title = Column(String(160), nullable=False)
    message = Column(Text)
    kind = Column(String(40), default="info", nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    client_id = Column(Integer, index=True)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    action = Column(String(80), nullable=False, index=True)
    entity = Column(String(60))
    entity_id = Column(Integer)
    details = Column(Text)
    user_info = Column(String(120))
    created_at = Column(DateTime, default=utcnow, nullable=False, index=True)

class SupportStatus(str, PyEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


class SupportRequest(Base):
    __tablename__ = "support_requests"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    subject = Column(String(160), nullable=False)
    status = Column(String(20), default=SupportStatus.OPEN.value, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, nullable=False)
    closed_at = Column(DateTime)
    client = relationship("Client")
    messages = relationship("SupportMessage", back_populates="request",
                            cascade="all, delete-orphan",
                            order_by="SupportMessage.created_at")


class SupportMessage(Base):
    __tablename__ = "support_messages"
    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey("support_requests.id"), nullable=False)
    sender_type = Column(String(10), nullable=False)
    sender_name = Column(String(120), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    request = relationship("SupportRequest", back_populates="messages")