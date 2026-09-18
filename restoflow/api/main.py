from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from restoflow.api.logconf import (AccessLogMiddleware,
                                   CorrelationIdMiddleware, get_logger)
from restoflow.api.routers import (auth, customers, devlogs, feedback, menu,
                                   notifications, orders, reports)
from restoflow.database import SessionLocal, init_db
from restoflow.events import subscribe
from restoflow.services import notification_service

log = get_logger("gateway")


def _notify_order(order_id: int):
    db = SessionLocal()
    try:
        notification_service.push_to_all_staff(
            db, title=f"🆕 Новый заказ #{order_id}",
            message="Заказ передан на кухню", kind="order")
    finally:
        db.close()


def _notify_payment(order_id: int, amount: float, method: str):
    db = SessionLocal()
    try:
        notification_service.push_to_all_staff(
            db, title=f"💳 Заказ #{order_id} оплачен",
            message=f"Сумма: {amount} ₽ ({method})", kind="payment")
    finally:
        db.close()


def _notify_feedback(feedback_id: int):
    db = SessionLocal()
    try:
        notification_service.push_to_all_staff(
            db, title=f"⭐ Новый отзыв #{feedback_id}",
            message="Поступил новый отзыв от клиента", kind="feedback")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    tables = init_db()
    log.info("STARTUP | tables=%d", len(tables))
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="RestoFlow API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(AccessLogMiddleware)
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"],
        allow_methods=["*"], allow_headers=["*"])
    @app.get("/", include_in_schema=False)
    def root():
        from fastapi.responses import RedirectResponse
        return RedirectResponse("/docs")

    @app.get("/health", tags=["service"])
    def health():
        return {"status": "ok", "service": "RestoFlow API", "version": "1.0.0"}
    for r in (auth.router, menu.router, orders.router, customers.router,
              feedback.router, reports.router, notifications.router,
              devlogs.router):
        app.include_router(r)
    subscribe("order.created", _notify_order)
    subscribe("payment.completed", _notify_payment)
    subscribe("feedback.created", _notify_feedback)
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)