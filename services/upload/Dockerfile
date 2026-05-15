FROM python:3.12-slim
WORKDIR /app

RUN pip install uv --no-cache-dir

COPY pyproject.toml uv.lock ./
COPY shared/ shared/
COPY services/upload/ services/upload/

RUN uv sync --package upload --no-dev
ENV PYTHONPATH=/app/shared/src
WORKDIR /app/services/upload
EXPOSE 8001
CMD ["uv", "run", "--project", "/app", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
