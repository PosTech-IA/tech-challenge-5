from celery import Celery
from app.config import settings

celery = Celery(broker=settings.redis_url)

# Ensure database tables exist before tasks run
# This creates all tables defined in app.models using SQLAlchemy
try:
    from app.database import engine, Base
    Base.metadata.create_all(bind=engine)
except Exception as e:
    import logging
    logging.warning(f"Could not initialize database tables: {e}")

# Import tasks module so the tasks are registered when the worker starts
# This ensures Celery discovers the @celery.task decorators in app.main
import app.main  # noqa: F401

__all__ = ["celery"]
