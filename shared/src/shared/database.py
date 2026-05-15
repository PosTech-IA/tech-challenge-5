from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from shared.config import BaseConfig


class Base(DeclarativeBase):
    pass


def init_db(config: BaseConfig):
    """Initialize database engine and session maker."""
    global engine, SessionLocal
    engine = create_engine(config.database_url)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return engine, SessionLocal


# Default initialization (can be overridden)
engine = None
SessionLocal = None


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session."""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
