FROM python:3.12-slim
WORKDIR /app

RUN pip install uv --no-cache-dir

COPY pyproject.toml uv.lock ./
COPY shared/ shared/
COPY services/gateway/ services/gateway/

RUN uv sync --package gateway --no-dev

WORKDIR /app/services/gateway
EXPOSE 8080
CMD ["uv", "run", "--project", "/app", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
