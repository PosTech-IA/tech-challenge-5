# structured-logging

Use ao configurar ou escrever logs em qualquer serviço. O edital exige logs estruturados.

## Setup (adicionar ao pyproject.toml de cada serviço)
```toml
"structlog>=24.0.0",
```

## Configuração padrão (chamar no startup de cada serviço)
```python
# app/logging_config.py
import logging
import structlog

def configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )
```

## Como usar em cada módulo
```python
import structlog
log = structlog.get_logger()

# Log simples
log.info("upload_received", filename="diagram.png", size_bytes=204800)

# Log com contexto de request (FastAPI middleware)
log.info("analysis_created", analysis_id="uuid", status="received")

# Log de erro
log.error("processing_failed", analysis_id="uuid", error=str(exc))
```

## Campos obrigatórios por evento
| Evento | Campos obrigatórios |
|--------|-------------------|
| upload recebido | `filename`, `size_bytes`, `analysis_id` |
| status alterado | `analysis_id`, `old_status`, `new_status` |
| chamada ao Claude | `analysis_id`, `model`, `file_type` |
| análise concluída | `analysis_id`, `components_count`, `risks_count` |
| erro | `analysis_id`, `error`, `retry_count` |

## No FastAPI (middleware de request logging)
```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    log.info("request_started", method=request.method, path=request.url.path)
    response = await call_next(request)
    log.info("request_completed", status_code=response.status_code)
    return response
```
