import uuid
import os
import re
import unicodedata

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.celery_app import enqueue_processing
from shared.database import get_db
from shared.models import Analysis
from shared.storage import upload_file
from app.config import settings
from shared.schemas import AnalysisSchema, AnalysisStatus


router = APIRouter()

ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "application/pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# -----------------------------
# Secure filename (no dependencies)
# -----------------------------
def secure_filename(filename: str) -> str:
    filename = unicodedata.normalize("NFKD", filename)
    filename = filename.encode("ascii", "ignore").decode("ascii")
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
    return filename


# -----------------------------
# Upload endpoint
# -----------------------------
@router.post(
    "/upload",
    response_model=AnalysisSchema,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_diagram(
    file: UploadFile,
    db: Session = Depends(get_db),
) -> AnalysisSchema:

    # 1. Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{file.content_type}' not supported. Use PNG, JPEG, or PDF.",
        )

    # 2. Read file
    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum size is 10 MB.",
        )

    # 3. Create analysis ID
    analysis_id = str(uuid.uuid4())

    filename = secure_filename(file.filename)
    file_ref = f"uploads/{analysis_id}/{filename}"

    # 4. Upload file to storage
    upload_file(file_bytes, file.content_type, file_ref, settings)

    # 5. Save DB record
    analysis = Analysis(
        id=analysis_id,
        filename=filename,
        file_ref=file_ref,
        status=AnalysisStatus.RECEIVED,
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    # 6. Send to Celery
    enqueue_processing(analysis_id, file_ref)

    return AnalysisSchema.model_validate(analysis)


# -----------------------------
# Status endpoint
# -----------------------------
@router.get(
    "/analysis/{analysis_id}",
    response_model=AnalysisSchema,
)
def get_status(
    analysis_id: str,
    db: Session = Depends(get_db),
) -> AnalysisSchema:

    analysis = (
        db.query(Analysis)
        .filter(Analysis.id == analysis_id)
        .first()
    )

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found.",
        )

    return AnalysisSchema.model_validate(analysis)