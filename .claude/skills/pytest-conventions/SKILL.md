# pytest-conventions

Use ao criar ou modificar testes em qualquer serviço.

## Estrutura de testes
```
tests/
├── unit/           # Testam uma função/classe isolada, sem I/O real
└── integration/    # Testam fluxos com banco ou fila reais (em memória ou container)
```

## Fixtures padrão (conftest.py)
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)

@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()
```

## Como mockar o Anthropic SDK (nunca chamar API real em CI)
```python
from unittest.mock import MagicMock, patch
import json

@patch("app.analyzer.anthropic.Anthropic")
def test_analyze_diagram(mock_cls):
    fake_response = json.dumps({
        "components": ["API Gateway", "PostgreSQL"],
        "risks": ["Sem rate limiting"],
        "recommendations": ["Adicionar circuit breaker"],
    })
    mock_client = MagicMock()
    mock_client.messages.create.return_value.content[0].text = fake_response
    mock_cls.return_value = mock_client

    result = analyze_diagram("/fake/diagram.png")
    assert result.components == ["API Gateway", "PostgreSQL"]
```

## Regras
- Nunca usar `ANTHROPIC_API_KEY` real em testes — sempre mockar
- Testes unitários não devem fazer I/O de disco nem rede
- Nome dos testes: `test_<o_que_faz>_<condição>` ex: `test_upload_rejects_pdf_over_10mb`
- Cobertura mínima esperada: 70% por serviço
