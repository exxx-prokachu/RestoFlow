import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

_mail = logging.getLogger("mail_outbox")
if not _mail.handlers:
    _handler = RotatingFileHandler(LOG_DIR / "mail_outbox.log",
                                   maxBytes=5 * 1024 * 1024, backupCount=3,
                                   encoding="utf-8")
    _handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
    _mail.addHandler(_handler)
    _mail.setLevel(logging.INFO)


def send_email(to: str, subject: str, body: str) -> bool:
    if not to:
        return False
    _mail.info(f"TO={to} | SUBJECT={subject} | BODY={body[:200]}")
    return True