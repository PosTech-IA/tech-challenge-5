from celery import Celery
from shared.config import BaseConfig


def create_celery_app(config: BaseConfig) -> Celery:
    """Factory function to create a Celery app with shared config."""
    return Celery(broker=config.redis_url)
