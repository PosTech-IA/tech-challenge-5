import json

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

import shared.database as db
import shared.storage as storage
from app.config import settings
from app.pdf_generator import generate_pdf_report
from shared.models import Analysis
from shared.schemas import AnalysisSchema, ListReportsResponse


# -----------------------------
# DB init
# -----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    db.init_db(settings)
    storage.init_storage(settings)
    db.Base.metadata.create_all(bind=db.engine)
    yield


app = FastAPI(title="Reports Service", lifespan=lifespan)


# -----------------------------
# Health check
# -----------------------------
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "reports"}


# -----------------------------
# List reports with filters and pagination
# -----------------------------
@app.get("/reports")
def list_reports(
    status: str | None = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db_session: Session = Depends(db.get_db),
):
    query = db_session.query(Analysis)

    if status:
        query = query.filter(Analysis.status == status)

    total = query.count()
    results = (
        query.order_by(Analysis.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    items = [AnalysisSchema.model_validate(r) for r in results]

    return ListReportsResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


# Get report (JSON API)
@app.get("/reports/{analysis_id}")
def get_report(
    analysis_id: str,
    db_session: Session = Depends(db.get_db),
):

    analysis = (
        db_session.query(Analysis)
        .filter(Analysis.id == analysis_id)
        .first()
    )

    if not analysis:
        raise HTTPException(status_code=404, detail="Not found")

    if analysis.status != "analyzed":
        raise HTTPException(status_code=409, detail="Still processing")

    return {
        "analysis_id": analysis.id,
        "filename": analysis.filename,
        "status": analysis.status,
        "content": analysis.result_data,
    }


# Download report as PDF (cached in MinIO)
@app.get("/reports/{analysis_id}/pdf")
def download_pdf_report(
    analysis_id: str,
    db_session: Session = Depends(db.get_db),
):
    """
    Download analysis report as PDF.
    Generates PDF on first request and caches in MinIO for subsequent requests.
    """
    # Fetch analysis from database
    analysis = (
        db_session.query(Analysis)
        .filter(Analysis.id == analysis_id)
        .first()
    )

    if not analysis:
        raise HTTPException(status_code=404, detail="Not found")

    if analysis.status != "analyzed":
        raise HTTPException(status_code=409, detail="Still processing")

    if not analysis.result_data:
        raise HTTPException(status_code=404, detail="No result data")

    # PDF cache key in MinIO
    pdf_cache_key = f"reports/{analysis_id}/report.pdf"

    # Check if PDF already exists in MinIO
    if storage.file_exists(pdf_cache_key, settings):
        # Return cached PDF from MinIO
        pdf_bytes = storage.download_file(pdf_cache_key, settings)
    else:
        # Generate PDF
        pdf_bytes = generate_pdf_report(
            filename=analysis.filename,
            created_at=analysis.created_at,
            result_data=analysis.result_data
        )

        # Cache PDF in MinIO
        try:
            storage.upload_file(
                file_bytes=pdf_bytes,
                content_type="application/pdf",
                file_ref=pdf_cache_key,
                config=settings
            )
        except Exception as e:
            # Log error but still return the PDF (generation succeeded)
            print(f"Warning: Failed to cache PDF in MinIO: {str(e)}")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="report.pdf"'
        },
    )


# -----------------------------
# DOWNLOAD generated file (from DB)
# -----------------------------
@app.get("/reports/{analysis_id}/download")
def download_report(
    analysis_id: str,
    db_session: Session = Depends(db.get_db),
):

    analysis = (
        db_session.query(Analysis)
        .filter(Analysis.id == analysis_id)
        .first()
    )

    if not analysis:
        raise HTTPException(status_code=404, detail="Not found")

    if analysis.status != "analyzed":
        raise HTTPException(status_code=409, detail="Still processing")

    if not analysis.result_data:
        raise HTTPException(status_code=404, detail="No result data")

    # garante dict
    try:
        data = json.loads(analysis.result_data) if isinstance(analysis.result_data, str) else analysis.result_data
    except Exception:
        data = {"raw": analysis.result_data}

    content = json.dumps(data, ensure_ascii=False, indent=2)

    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{analysis_id}-result.json"'
        },
    )