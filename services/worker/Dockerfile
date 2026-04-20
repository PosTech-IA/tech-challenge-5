FROM python:3.12-slim

WORKDIR /app

RUN pip install uv --no-cache-dir

COPY pyproject.toml .
RUN uv sync --no-dev

COPY app/ app/

CMD ["uv", "run", "celery", "-A", "app.celery_app.celery", "worker", "--loglevel=info"]
