.PHONY: up down logs build test lint

up:
	docker compose up --build -d

down:
	docker compose down -v

logs:
	docker compose logs -f

build:
	docker compose build

test:
	cd services/gateway  && uv run pytest tests/ -v
	cd services/upload   && uv run pytest tests/ -v
	cd services/processor && uv run pytest tests/ -v
	cd services/reports  && uv run pytest tests/ -v

lint:
	uv run ruff check shared/src services/gateway/app services/upload/app services/processor/app services/reports/app
