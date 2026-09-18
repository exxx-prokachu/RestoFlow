from collections import defaultdict
from typing import Callable, Any

_handlers: dict[str, list[Callable[..., Any]]] = defaultdict(list)
_history: list[dict] = []


def subscribe(event: str, handler: Callable[..., Any]) -> None:
    _handlers[event].append(handler)


def publish(event: str, **payload: Any) -> None:
    _history.append({"event": event, "payload": payload})
    for handler in _handlers.get(event, []):
        try:
            handler(**payload)
        except Exception:
            pass


def last_events(limit: int = 100) -> list[dict]:
    return _history[-limit:]