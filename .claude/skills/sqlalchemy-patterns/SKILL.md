# sqlalchemy-patterns

Use ao criar modelos, sessões ou queries em qualquer serviço.

## Engine e sessão (infrastructure/db/session.py)
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## Template de model
```python
# infrastructure/db/models.py
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.session import Base
import enum

class AnalysisStatus(str, enum.Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    ERROR = "error"

class AnalysisModel(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[AnalysisStatus] = mapped_column(SAEnum(AnalysisStatus), default=AnalysisStatus.RECEIVED)
    components: Mapped[list | None] = mapped_column(JSON, nullable=True)
    risks: Mapped[list | None] = mapped_column(JSON, nullable=True)
    recommendations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

## Criar tabelas no startup
```python
# Chamar no lifespan do FastAPI ou no início do worker
Base.metadata.create_all(bind=engine)
```

## Queries comuns
```python
# Buscar por ID
analysis = db.query(AnalysisModel).filter(AnalysisModel.id == analysis_id).first()

# Atualizar status
analysis.status = AnalysisStatus.PROCESSING
analysis.updated_at = datetime.utcnow()
db.commit()

# Salvar novo registro
db.add(analysis)
db.commit()
db.refresh(analysis)
```

## Config de banco por serviço
- `api`: `DATABASE_URL=postgresql://app:app@postgres/analyzer`
- `worker`: mesma URL — os dois acessam o mesmo banco mas cada um cuida do seu domínio
- Em testes: usar `sqlite:///:memory:` via override de fixture
