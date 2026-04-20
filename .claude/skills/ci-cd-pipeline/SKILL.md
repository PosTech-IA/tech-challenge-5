# ci-cd-pipeline

Use ao modificar o pipeline de CI/CD ou adicionar novos jobs.

## Estrutura do pipeline (GitHub Actions)
```
on: push/PR para main
│
├── test-api      (lint ruff + pytest)
├── test-worker   (lint ruff + pytest)
│
└── build         (docker compose build) — só roda se ambos os testes passarem
```

## Regras
- PR não pode ser mergeado sem todos os jobs passando
- Nunca commitar `ANTHROPIC_API_KEY` — injetar via `secrets.ANTHROPIC_API_KEY`
- Cache de dependências UV entre runs para velocidade

## Template de job
```yaml
jobs:
  test-api:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - name: Lint and test
        working-directory: services/api
        run: |
          uv sync --group dev
          uv run ruff check app/ tests/
          uv run pytest tests/ -v
```

## Adicionar novo serviço ao pipeline
Duplicar o job com o nome do novo serviço e ajustar `working-directory`.
Adicionar como dependência no job `build`.

## Deploy (opcional para hackathon)
Deploy local via `docker compose up --build` é suficiente para demonstração.
Para cloud: adicionar job `deploy` que faz SSH + `docker compose pull && up`.
