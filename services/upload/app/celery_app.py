from celery import Celery

from app.config import settings

celery = Celery(broker=settings.redis_url)


def enqueue_processing(analysis_id: str, file_ref: str) -> None:
    celery.send_task(
        "processor.tasks.process_diagram",
        args=[analysis_id, file_ref],
    )
