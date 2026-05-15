from shared.celery import create_celery_app
from app.config import settings

celery = create_celery_app(settings)


def enqueue_processing(analysis_id: str, file_ref: str) -> None:
    celery.send_task(
        "processor.tasks.process_diagram",
        args=[analysis_id, file_ref],
    )

