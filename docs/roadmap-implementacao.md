# Roadmap de Implementação — Tech Challenge 5

## Etapa 1 — Upload Service `✅ Concluída`

Serviço responsável por receber arquivos (PNG, JPEG, PDF) via HTTP, armazená-los no MinIO, registrar o status no banco `upload_db` e enfileirar a tarefa de processamento no Celery/Redis.

**Arquivos criados:** `config.py`, `database.py`, `models.py`, `storage.py`, `celery_app.py`, `routes.py`, `main.py`
**Endpoints:** `POST /upload`, `GET /status/{id}`
**Testes:** 10 testes passando (unitários com mocks + físicos com fixtures)
**Doc:** `docs/etapa-1-upload-service.md`

---

## Etapa 2 — Processor Service `⬜ Pendente`

Worker Celery responsável por consumir tarefas da fila, baixar o arquivo do MinIO, extrair o conteúdo (texto de PDFs via pypdf, imagens via Pillow/base64), chamar a API Claude (`claude-sonnet-4-6`) para análise e publicar o resultado na fila do Reports.

**Arquivos a criar:** `celery_app.py`, `storage.py`, `extractor.py`, `ai.py`, `worker.py`
**Fluxo:** consome `processor.tasks.process_diagram` → analisa → publica `reports.tasks.store_report`
**Atualiza:** status no `upload_db` para `processing` / `analyzed` / `error`

---

## Etapa 3 — Reports Service `⬜ Pendente`

Serviço responsável por consumir os resultados do Processor via Celery, persistir os relatórios no banco `reports_db` e expô-los via API REST.

**Arquivos a criar:** `config.py`, `database.py`, `models.py`, `celery_app.py`, `routes.py`, `main.py`
**Endpoints:** `GET /reports/{analysis_id}`
**Fluxo:** consome `reports.tasks.store_report` → persiste no banco → disponibiliza via GET

---

## Etapa 4 — Gateway Service `⬜ Pendente`

Único ponto de entrada público da API. Valida JWT, aplica rate limiting (10 req/min via SlowAPI) e faz proxy das requisições para Upload e Reports via HTTPX.

**Arquivos a criar:** `config.py`, `auth.py`, `routes.py`, `main.py`
**Endpoints expostos:** `POST /upload`, `GET /status/{id}`, `GET /reports/{id}`
**Porta:** 8000 (única porta exposta ao cliente)

---

## Etapa 5 — Testes de Integração `⬜ Pendente`

Testes end-to-end cobrindo o fluxo completo: upload → processamento → relatório. Valida a comunicação entre todos os serviços com a stack Docker Compose rodando.

**Escopo:** subir a stack com `make up`, fazer upload de fixture real, aguardar processamento, consultar relatório gerado.

---

## Etapa 6 — README e Documentação Final `⬜ Pendente`

Documentação completa exigida pelo hackathon no `README.md`, incluindo a seção obrigatória de Segurança.

**Conteúdo obrigatório:**
- Descrição do problema
- Arquitetura proposta com diagrama
- Fluxo da solução
- Instruções de execução (`make up`, variáveis de ambiente)
- **Seção Segurança** — validação de entradas, guardrails da IA, comunicação entre serviços, riscos e limitações

---

## Resumo

| Etapa | Serviço | Status |
|---|---|---|
| 1 | Upload Service | ✅ Concluída |
| 2 | Processor Service | ⬜ Pendente |
| 3 | Reports Service | ⬜ Pendente |
| 4 | Gateway Service | ⬜ Pendente |
| 5 | Testes de Integração | ⬜ Pendente |
| 6 | README + Docs Finais | ⬜ Pendente |
