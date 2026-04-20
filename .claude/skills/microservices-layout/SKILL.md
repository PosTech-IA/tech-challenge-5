# microservices-layout

Use ao definir novos endpoints, mensagens de fila ou contratos entre serviços.

## Serviços e responsabilidades
| Serviço | Porta | Responsabilidade |
|---------|-------|-----------------|
| `api`   | 8000  | Receber upload, expor status e relatório via REST |
| `worker`| —     | Consumir fila, executar análise IA, persistir resultado |

## Comunicação
```
Cliente → POST /analyses         → api
api     → publica job na fila    → Redis (Celery)
worker  ← consome job da fila    ← Redis (Celery)
worker  → atualiza banco         → PostgreSQL
Cliente → GET /analyses/{id}/status  → api → PostgreSQL
Cliente → GET /analyses/{id}/report  → api → PostgreSQL
```

## Contratos REST (api)

### POST /analyses
- Request: multipart/form-data, campo `file` (PNG/JPEG/PDF, máx 10MB)
- Response 202: `{ "id": "uuid", "status": "received", "created_at": "...", "updated_at": "..." }`
- Response 400: tipo ou tamanho inválido

### GET /analyses/{id}/status
- Response 200: `{ "id": "uuid", "status": "received|processing|analyzed|error", "created_at": "...", "updated_at": "..." }`
- Response 404: não encontrado

### GET /analyses/{id}/report
- Response 200: `{ "id": "uuid", "status": "analyzed", "components": [...], "risks": [...], "recommendations": [...] }`
- Response 202: ainda processando
- Response 404: não encontrado

## Schema da mensagem de fila (Celery)
```json
{ "analysis_id": "uuid-v4" }
```
Task name: `worker.tasks.process_diagram`

## Regra de banco
Cada serviço conecta ao seu próprio banco (ou schema). O `api` cria e lê registros de `analyses`. O `worker` atualiza status e resultado de `analyses`. Não há chamadas REST entre api e worker — a comunicação é exclusivamente via fila.
