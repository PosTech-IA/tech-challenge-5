FROM python:3.12-slim
WORKDIR /app

RUN pip install uv --no-cache-dir

COPY pyproject.toml uv.lock ./
COPY shared/ shared/
COPY services/reports/ services/reports/

RUN uv sync --package reports --no-dev

WORKDIR /app/services/reports
EXPOSE 8002
CMD ["uv", "run", "--project", "/app", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
