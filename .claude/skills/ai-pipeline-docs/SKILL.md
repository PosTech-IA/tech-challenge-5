# ai-pipeline-docs

Use ao escrever a documentação de IA exigida pelo edital (parte IADT) no README ou em documento separado.

## O que o edital exige (obrigatório)
- Pipeline claro de IA
- Justificativa da abordagem escolhida
- Demonstração prática da análise
- Discussão de limitações do modelo

## Template de seção "Pipeline de IA" para o README

### Abordagem escolhida
**LLM multimodal com prompt engineering e guardrails**

Usamos o Claude (`claude-sonnet-4-6`) com capacidade de visão para analisar diagramas diretamente como imagem ou PDF, sem etapa de OCR separada. A saída é estruturada via prompt engineering com schema JSON estrito, validada por Pydantic antes de persistir.

### Pipeline
```
Arquivo recebido (PNG/JPEG/PDF)
       │
       ▼
Validação de entrada
(tipo MIME, magic bytes, tamanho ≤ 10MB)
       │
       ▼
Codificação base64
       │
       ▼
Chamada Claude API (claude-sonnet-4-6)
  - System prompt com schema JSON obrigatório
  - temperature=0 para saída determinística
  - max_tokens=2048
       │
       ▼
Validação da saída (Pydantic)
  ├─ Válida → persistir resultado → status=ANALYZED
  └─ Inválida → retry com prompt de correção (1x)
                    └─ falha → status=ERROR
```

### Justificativa
| Critério | Decisão |
|----------|---------|
| Sem dataset próprio | LLM pré-treinado elimina necessidade de treinar modelo de visão |
| Diagramas variados | Claude generaliza bem para diferentes notações (C4, UML, informal) |
| Saída estruturada | Prompt engineering com JSON schema é mais confiável que parsing livre |
| Guardrails | Pydantic valida schema + system prompt restringe escopo |

### Limitações conhecidas
- **Alucinação**: o modelo pode identificar componentes não presentes — mitigado pela instrução explícita no system prompt
- **Diagramas complexos**: imagens de baixa resolução ou muito densas reduzem a qualidade da análise
- **Custo por análise**: cada chamada consome tokens — sem rate limiting no MVP
- **Latência**: 5–30s por análise dependendo do tamanho do arquivo
- **Prompt injection**: texto instrucional dentro do diagrama pode tentar desviar o comportamento — mitigado pelo system prompt restritivo com papel fixo de arquiteto
- **Idioma**: o modelo responde no idioma do texto do diagrama; sem texto, responde em português (configurado no prompt)
