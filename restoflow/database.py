from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_engine(
    "sqlite:///cafe.db",
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from restoflow import models  # noqa: F401
    from restoflow.migrate import ensure_schema
    Base.metadata.create_all(bind=engine)
    ensure_schema(engine)
    return list(Base.metadata.tables.keys())