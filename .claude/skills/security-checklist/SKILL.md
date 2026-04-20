# security-checklist

Use ao escrever a seção obrigatória de Segurança do README ou ao revisar código.

## Seção obrigatória no README
O enunciado exige explicitamente uma seção **Segurança** cobrindo os itens abaixo.

### 1. Validação de upload
- Tipos MIME permitidos: `image/png`, `image/jpeg`, `image/jpg`, `application/pdf`
- Tamanho máximo: 10MB
- Validar magic bytes além do Content-Type (não confiar no cliente)
- Rejeitar arquivos com nome suspeito (path traversal: `../`, `%2F`, etc.)

### 2. Sanitização de entrada para o LLM
- Não incluir metadados do usuário no prompt enviado ao Claude
- System prompt com escopo fechado — o modelo só analisa diagramas
- `temperature=0` e `max_tokens` limitado para saída previsível

### 3. Escopo e controle do modelo de IA
- Modelo fixado: `claude-sonnet-4-6` (não deixar o cliente escolher)
- Saída validada por schema Pydantic antes de persistir
- Respostas fora do schema → retry controlado, depois status=ERROR (nunca expor raw response ao cliente)

### 4. Tratamento seguro de falhas da IA
- Timeout na chamada ao Anthropic SDK
- Máximo de retries definido (3x com backoff)
- Falha definitiva → status=ERROR com mensagem genérica ao cliente (sem stack trace)
- Logs internos com detalhes completos do erro

### 5. Comunicação entre serviços
- API key interna entre serviços se comunicação REST for adicionada
- Redis sem autenticação só em rede interna Docker (nunca expor porta externamente)
- PostgreSQL idem — nunca expor porta 5432 para fora do compose network

### 6. Riscos conhecidos e limitações
- **Prompt injection via diagrama**: imagem/PDF pode conter texto instrucional — mitigado pelo system prompt restritivo
- **Alucinação**: modelo pode inventar componentes — mitigado por instrução explícita no system prompt
- **Custo**: cada análise consome tokens — sem rate limiting no MVP
- **Latência**: análise pode levar alguns segundos — gerenciado pelo fluxo assíncrono
