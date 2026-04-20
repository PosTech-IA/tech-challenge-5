FROM python:3.12-slim
WORKDIR /app

RUN pip install uv --no-cache-dir

COPY pyproject.toml uv.lock ./
COPY shared/ shared/
COPY services/processor/ services/processor/

RUN uv sync --package processor --no-dev

WORKDIR /app/services/processor
CMD ["uv", "run", "--project", "/app", "celery", "-A", "app.celery_app.celery", "worker", "--loglevel=info"]
