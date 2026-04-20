# readme-template

Use ao escrever ou revisar o README.md final do projeto.

## Template

```markdown
# FIAP Secure Systems — Analisador de Diagramas de Arquitetura

## Descrição do problema
Empresas com sistemas distribuídos possuem dezenas de diagramas de arquitetura analisados manualmente, demandando tempo e especialistas. Esta solução automatiza a análise com IA, gerando relatórios técnicos com componentes, riscos e recomendações.

## Arquitetura proposta
[Inserir diagrama de arquitetura aqui]

Serviços:
- **api**: API Gateway REST (FastAPI) — recebe uploads, expõe status e relatórios
- **worker**: Serviço de processamento assíncrono (Celery) — análise via Claude AI
- **postgres**: Banco de dados
- **redis**: Broker de mensagens (fila Celery)

## Fluxo da solução
1. Cliente envia diagrama via `POST /analyses`
2. API salva o arquivo, cria registro com status `received` e publica job na fila
3. Worker consome o job, atualiza para `processing`, chama o Claude AI
4. Claude retorna JSON com componentes, riscos e recomendações
5. Worker persiste resultado e atualiza status para `analyzed`
6. Cliente consulta `GET /analyses/{id}/report` para obter o relatório

## Instruções de execução

### Pré-requisitos
- Docker e Docker Compose instalados
- Chave de API do Anthropic

### Passos
\`\`\`bash
cp .env.example .env
# Editar .env e adicionar ANTHROPIC_API_KEY
docker compose up --build
\`\`\`

API disponível em: http://localhost:8000
Documentação: http://localhost:8000/docs

## Endpoints
| Método | Path | Descrição |
|--------|------|-----------|
| POST | /analyses | Upload de diagrama |
| GET | /analyses/{id}/status | Consulta status |
| GET | /analyses/{id}/report | Obtém relatório |

## Segurança
[Preencher usando a skill security-checklist]

## Limitações conhecidas
- Sem rate limiting no MVP
- Arquivos máximo 10MB
- Tempo de análise: 5–30 segundos dependendo da complexidade
```
