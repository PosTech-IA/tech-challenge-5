# docker-compose-stack

Use ao modificar o docker-compose.yml ou adicionar novos serviços.

## Serviços do stack
| Serviço    | Imagem              | Porta  | Função |
|------------|---------------------|--------|--------|
| `postgres` | postgres:16-alpine  | 5432   | Banco de dados |
| `redis`    | redis:7-alpine      | 6379   | Broker Celery |
| `api`      | build ./services/api | 8000  | API Gateway REST |
| `worker`   | build ./services/worker | —   | Processador async |

## Regras de healthcheck
Todos os serviços de infraestrutura (postgres, redis) devem ter healthcheck.
Os serviços da aplicação devem usar `depends_on` com `condition: service_healthy`.

## Variáveis de ambiente
- Nunca commitar `.env` — só `.env.example`
- Variáveis sensíveis (`ANTHROPIC_API_KEY`) apenas no `.env` local
- No CI/CD: injetar via secrets

## Makefile (targets padrão)
```makefile
.PHONY: up down logs test build

up:
	docker compose up --build -d

down:
	docker compose down -v

logs:
	docker compose logs -f

test:
	cd services/api && uv run pytest tests/ -v
	cd services/worker && uv run pytest tests/ -v

build:
	docker compose build
```

## Volume compartilhado de uploads
```yaml
volumes:
  uploads:        # compartilhado entre api e worker para acesso ao arquivo
  postgres_data:  # persistência do banco
```
Ambos `api` e `worker` montam `/uploads` para que o worker acesse o arquivo enviado pelo cliente.
