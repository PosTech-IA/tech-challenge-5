import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.celery_app import enqueue_processing
from app.database import get_db
from app.models import Analysis
from app.storage import upload_file
from shared.src.shared.schemas import AnalysisSchema, AnalysisStatus

router = APIRouter()

ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "application/pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/upload", response_model=AnalysisSchema, status_code=status.HTTP_202_ACCEPTED)
async def upload_diagram(file: UploadFile, db: Session = Depends(get_db)) -> AnalysisSchema:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{file.content_type}' not supported. Use PNG, JPEG, or PDF.",
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum size is 10 MB.",
        )

    analysis_id = str(uuid.uuid4())
    file_ref = f"uploads/{analysis_id}/{file.filename}"

    upload_file(file_bytes, file.content_type, file_ref)

    analysis = Analysis(
        id=analysis_id,
        filename=file.filename,
        file_ref=file_ref,
        status=AnalysisStatus.RECEIVED,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    enqueue_processing(analysis_id, file_ref)

    return AnalysisSchema.model_validate(analysis)


@router.get("/status/{analysis_id}", response_model=AnalysisSchema)
def get_status(analysis_id: str, db: Session = Depends(get_db)) -> AnalysisSchema:
    analysis = db.get(Analysis, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found.")
    return AnalysisSchema.model_validate(analysis)
