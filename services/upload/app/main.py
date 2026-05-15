from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

import shared.database as db
from shared.storage import init_storage

from app.routes import router
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Initialize database and storage
    db.init_db(settings)
    init_storage(settings)

    db.Base.metadata.create_all(bind=db.engine)

    yield


app = FastAPI(title="Upload Service", lifespan=lifespan)
app.include_router(router)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": str(exc)})