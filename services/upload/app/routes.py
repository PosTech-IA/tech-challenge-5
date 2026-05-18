import uuid
import os
import re
import unicodedata

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from shared.logging import get_logger

from app.celery_app import enqueue_processing
from shared.database import get_db
from shared.models import Analysis
from shared.storage import upload_file
from app.config import settings
from shared.schemas import AnalysisSchema, AnalysisStatus


router = APIRouter()
logger = get_logger(__name__)

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
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> AnalysisSchema:

    logger.info(f"Upload request received. File: {file.filename}, Content-Type: {file.content_type}")

    # 1. Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        logger.warning(f"Invalid file type: {file.content_type}")
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{file.content_type}' not supported. Use PNG, JPEG, or PDF.",
        )

    # 2. Read file
    logger.info("Reading file bytes...")
    file_bytes = await file.read()
    logger.info(f"File read complete. Size: {len(file_bytes)} bytes")

    if len(file_bytes) > MAX_FILE_SIZE:
        logger.warning(f"File too large: {len(file_bytes)} bytes (max: {MAX_FILE_SIZE})")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum size is 10 MB.",
        )

    # 3. Create analysis ID
    analysis_id = str(uuid.uuid4())
    filename = secure_filename(file.filename)
    file_ref = f"uploads/{analysis_id}/{filename}"
    logger.info(f"Created analysis ID: {analysis_id}, file_ref: {file_ref}")

    # 4. Upload file to storage
    try:
        logger.info(f"Uploading to MinIO: {file_ref}")
        upload_file(file_bytes, file.content_type, file_ref, settings)
        logger.info(f"MinIO upload successful")
    except Exception as e:
        logger.error(f"MinIO upload failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store file: {str(e)}",
        )

    # 5. Save DB record
    try:
        logger.info(f"Creating database record for analysis {analysis_id}")
        analysis = Analysis(
            id=analysis_id,
            filename=filename,
            file_ref=file_ref,
            status=AnalysisStatus.RECEIVED,
        )

        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        logger.info(f"Database record created successfully")
    except Exception as e:
        logger.error(f"Database operation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create analysis record: {str(e)}",
        )

    # 6. Send to Celery
    try:
        logger.info(f"Enqueueing Celery task for analysis {analysis_id}")
        enqueue_processing(analysis_id, file_ref)
        logger.info(f"Celery task enqueued successfully")
    except Exception as e:
        logger.error(f"Celery enqueue failed: {str(e)}", exc_info=True)
        # Don't fail the request - the file is already stored

    logger.info(f"Upload request completed successfully for {analysis_id}")
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