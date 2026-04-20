# celery-worker-patterns

Use ao criar ou modificar tasks Celery no serviço worker.

## Template de task padrão
```python
import logging
from celery import Task
from app.celery_app import celery
from app.database import SessionLocal
from app.models import Analysis, AnalysisStatus

logger = logging.getLogger(__name__)

@celery.task(
    name="worker.tasks.process_diagram",
    bind=True,
    max_retries=3,
    acks_late=True,          # só confirma após execução bem-sucedida
    default_retry_delay=60,  # segundos entre retries
)
def process_diagram(self, analysis_id: str) -> None:
    log = logger.bind(analysis_id=analysis_id) if hasattr(logger, "bind") else logger
    db = SessionLocal()
    analysis = None
    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            log.warning("analysis_not_found")
            return

        analysis.status = AnalysisStatus.PROCESSING
        db.commit()
        log.info("processing_started")

        result = analyze_diagram(analysis.file_path)  # chama o analyzer

        analysis.components = result.components
        analysis.risks = result.risks
        analysis.recommendations = result.recommendations
        analysis.status = AnalysisStatus.ANALYZED
        db.commit()
        log.info("processing_completed")

    except Exception as exc:
        log.error("processing_failed", error=str(exc))
        if analysis:
            analysis.status = AnalysisStatus.ERROR
            analysis.error_message = str(exc)
            db.commit()
        raise self.retry(exc=exc)
    finally:
        db.close()
```

## Transições de status
```
RECEIVED → (worker inicia) → PROCESSING → (IA retorna) → ANALYZED
                                        → (erro/retries esgotados) → ERROR
```

## Logging estruturado
Usar campos fixos em todos os logs da task: `analysis_id`, `status`, `event`.
Se usar `structlog`: `log = structlog.get_logger().bind(analysis_id=analysis_id)`.
Se usar `logging` padrão: incluir `analysis_id` no prefixo ou como extra.

## Celery app mínimo
```python
# app/celery_app.py
from celery import Celery
from app.config import settings

celery = Celery(
    "worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"],
)
celery.conf.task_serializer = "json"
celery.conf.result_serializer = "json"
celery.conf.accept_content = ["json"]
```
