import io
from unittest.mock import patch

import app.database as db_module
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    db_module.engine = test_engine
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@patch("app.routes.enqueue_processing")
@patch("app.routes.upload_file")
def test_upload_png_success(mock_upload, mock_enqueue, client):
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    response = client.post(
        "/upload",
        files={"file": ("diagram.png", io.BytesIO(png_bytes), "image/png")},
    )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "received"
    assert data["filename"] == "diagram.png"
    assert "id" in data
    mock_upload.assert_called_once()
    mock_enqueue.assert_called_once()


@patch("app.routes.enqueue_processing")
@patch("app.routes.upload_file")
def test_upload_pdf_success(mock_upload, mock_enqueue, client):
    response = client.post(
        "/upload",
        files={"file": ("report.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
    )
    assert response.status_code == 202
    assert response.json()["status"] == "received"


def test_upload_invalid_type(client):
    response = client.post(
        "/upload",
        files={"file": ("notes.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert response.status_code == 415


@patch("app.routes.enqueue_processing")
@patch("app.routes.upload_file")
def test_upload_too_large(mock_upload, mock_enqueue, client):
    large_bytes = b"\x00" * (10 * 1024 * 1024 + 1)
    response = client.post(
        "/upload",
        files={"file": ("big.png", io.BytesIO(large_bytes), "image/png")},
    )
    assert response.status_code == 413


@patch("app.routes.enqueue_processing")
@patch("app.routes.upload_file")
def test_get_status_found(mock_upload, mock_enqueue, client):
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    upload_resp = client.post(
        "/upload",
        files={"file": ("diagram.png", io.BytesIO(png_bytes), "image/png")},
    )
    analysis_id = upload_resp.json()["id"]

    response = client.get(f"/status/{analysis_id}")
    assert response.status_code == 200
    assert response.json()["id"] == analysis_id


def test_get_status_not_found(client):
    response = client.get("/status/nonexistent-id")
    assert response.status_code == 404
