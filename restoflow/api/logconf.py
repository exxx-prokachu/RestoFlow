import logging
import uuid
from logging.handlers import RotatingFileHandler

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from restoflow.api.config import LOG_DIR


def get_logger(service: str) -> logging.Logger:
    logger = logging.getLogger(service)
    if not logger.handlers:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            LOG_DIR / f"{service}.log",
            maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8")
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.correlation_id = request.headers.get(
            "X-Correlation-ID", uuid.uuid4().hex[:12])
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = request.state.correlation_id
        return response


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        get_logger("gateway").info(
            "%s %s -> %s | cid=%s", request.method, request.url.path,
            response.status_code,
            getattr(request.state, "correlation_id", "-"))
        return response