from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from shared.logging import setup_logging, get_logger, set_correlation_id

import shared.database as db
from shared.storage import init_storage

from app.routes import router
from app.config import settings

setup_logging('upload')
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Initialize database and storage
    logger.info("Initializing database and storage")
    try:
        db.init_db(settings)
        logger.info(f"Database URL: {settings.database_url[:50]}...")
        init_storage(settings)
        logger.info(f"MinIO endpoint: {settings.minio_endpoint}")

        db.Base.metadata.create_all(bind=db.engine)
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}", exc_info=True)
        raise

    logger.info("Upload service startup complete")
    yield
    logger.info("Upload service shutting down")


app = FastAPI(title="Upload Service", lifespan=lifespan)
app.include_router(router)


@app.middleware("http")
async def add_correlation_id_middleware(request: Request, call_next):
    """Extract or create correlation ID from request headers."""
    correlation_id = request.headers.get("X-Correlation-ID", "")
    if correlation_id:
        set_correlation_id(correlation_id)
        logger.info(f"Processing request with correlation ID: {correlation_id}")
    return await call_next(request)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "upload"}


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": str(exc)})