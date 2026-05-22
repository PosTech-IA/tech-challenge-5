import json

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

import shared.database as db
from app.config import settings
from shared.models import Analysis
from shared.schemas import AnalysisSchema, ListReportsResponse


# -----------------------------
# DB init
# -----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    db.init_db(settings)
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