# hackathon-context

Use whenever working on the FIAP Secure Systems hackathon project.

## Problema
Analisar diagramas de arquitetura (imagem ou PDF) automaticamente com IA, gerando relatório técnico com componentes, riscos e recomendações.

## Fluxo obrigatório (5 passos)
1. Upload de diagrama (PNG, JPEG ou PDF)
2. Processamento do diagrama
3. Análise automatizada por IA
4. Geração de relatório técnico
5. Consulta do status do processamento

## Estados válidos de processamento
- `received` — diagrama recebido, aguardando processamento
- `processing` — worker processando
- `analyzed` — análise concluída com sucesso
- `error` — falha no processamento

## Stack fixada
- Python 3.12+, UV
- FastAPI + Uvicorn (API)
- Celery + Redis (fila assíncrona)
- SQLAlchemy + PostgreSQL (persistência)
- Anthropic SDK — claude-sonnet-4-6 (análise IA)
- Pillow + pypdf (processamento de arquivos)
- Pytest + Ruff (qualidade)
- Docker + Docker Compose

## Checklist de entregáveis
- [ ] Código-fonte no repositório Git
- [ ] Dockerfile por serviço
- [ ] docker-compose.yml funcional
- [ ] Pipeline CI/CD (build + testes + deploy)
- [ ] README com: problema, arquitetura, fluxo, instruções
- [ ] Diagrama de arquitetura
- [ ] Seção obrigatória de Segurança no README
- [ ] Vídeo de demonstração (até 15 minutos)

## Requisitos técnicos obrigatórios
- Arquitetura de microsserviços
- REST + ao menos um fluxo assíncrono (fila)
- Clean Architecture ou Hexagonal
- Cada serviço: responsabilidade clara, banco próprio, testes
- Logs estruturados e tratamento de erros
