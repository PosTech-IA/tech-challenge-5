# anthropic-diagram-analysis

Use ao implementar ou modificar a análise de diagramas com o Claude.

## Modelo
`claude-sonnet-4-6` — suporta visão (imagem) e documentos (PDF).

## System prompt (versão atual)
```
You are an expert software architect. Analyze the provided architecture diagram.
Return ONLY a valid JSON object with exactly these fields:
- "components": list of strings — only components visually identifiable in the diagram (services, databases, queues, load balancers, CDNs, etc.)
- "risks": list of strings — potential architectural risks or issues observed
- "recommendations": list of strings — basic architectural recommendations

Rules:
- Do not invent components not present in the diagram
- Each list must have at least 1 item
- Do not include any text outside the JSON object
- Respond in the same language as any text found in the diagram (default: Portuguese)
```

## Schema de resposta esperado
```python
class AnalysisResult(BaseModel):
    components: list[str]      # mínimo 1 item
    risks: list[str]           # mínimo 1 item
    recommendations: list[str] # mínimo 1 item
```

## Chamada para imagem (PNG/JPEG)
```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=2048,
    temperature=0,   # saída determinística
    system=SYSTEM_PROMPT,
    messages=[{
        "role": "user",
        "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64}},
            {"type": "text", "text": "Analyze this architecture diagram."},
        ],
    }],
)
```

## Chamada para PDF
```python
{"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": b64}}
```

## Guardrails de entrada
- Tipos permitidos: `image/png`, `image/jpeg`, `image/jpg`, `application/pdf`
- Tamanho máximo: 10MB
- Validar com magic bytes (não confiar só no Content-Type do cliente)

## Guardrails de saída
```python
raw = response.content[0].text.strip()
try:
    parsed = json.loads(raw)
    result = AnalysisResult(**parsed)
except (json.JSONDecodeError, ValidationError):
    # Tentar uma vez com prompt de correção antes de lançar erro
    raise ValueError("LLM returned invalid response")
```

## Mitigação de alucinação
- `temperature=0` garante saída mais determinística
- System prompt proíbe inventar componentes não visíveis
- Validação Pydantic rejeita respostas que não seguem o schema
- Se JSON inválido: retry com prompt explícito de correção, depois status=ERROR
