import os
from pathlib import Path

SECRET_KEY = os.getenv("RESTOFLOW_SECRET", "dev-secret-change-me")
ALGORITHM = "HS256"
TOKEN_TTL_MINUTES = 720
LOG_DIR = Path(__file__).resolve().parents[2] / "logs"