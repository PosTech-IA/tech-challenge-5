# clean-architecture-python

Use ao criar novos casos de uso, endpoints ou entidades.

## Estrutura de pastas por serviço
```
app/
├── domain/
│   ├── entities/       # Modelos de negócio puros (sem ORM, sem HTTP)
│   └── interfaces/     # Abstrações (repositórios, serviços externos)
├── application/
│   └── use_cases/      # Um arquivo por caso de uso
├── infrastructure/
│   ├── db/             # Modelos ORM, repositórios concretos
│   └── messaging/      # Celery, Redis
└── presentation/
    └── routes/         # Controllers FastAPI (só orquestram, sem lógica)
```

## Regra de dependência
`domain` não importa nada de fora. `application` só importa `domain`. `infrastructure` e `presentation` importam `application` e `domain`.

## Template de caso de uso
```python
# application/use_cases/create_analysis.py
from app.domain.interfaces.analysis_repository import AnalysisRepository
from app.domain.interfaces.queue import Queue
from app.domain.entities.analysis import Analysis

class CreateAnalysisUseCase:
    def __init__(self, repository: AnalysisRepository, queue: Queue) -> None:
        self._repository = repository
        self._queue = queue

    def execute(self, filename: str, file_path: str) -> Analysis:
        analysis = Analysis.create(filename=filename, file_path=file_path)
        self._repository.save(analysis)
        self._queue.enqueue(analysis.id)
        return analysis
```

## Template de interface (domain)
```python
# domain/interfaces/analysis_repository.py
from abc import ABC, abstractmethod
from app.domain.entities.analysis import Analysis

class AnalysisRepository(ABC):
    @abstractmethod
    def save(self, analysis: Analysis) -> None: ...

    @abstractmethod
    def find_by_id(self, analysis_id: str) -> Analysis | None: ...

    @abstractmethod
    def update_status(self, analysis_id: str, status: str, **kwargs) -> None: ...
```
