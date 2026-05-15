from pathlib import Path
from unittest.mock import patch

import pytest
import shared.src.shared.database as db_module
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from shared.src.shared.database import Base, get_db
from app.main import app

FIXTURES_DIR = Path(__file__).parent / "fixtures"

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
    # substitui o engine do módulo pelo SQLite antes do lifespan rodar
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
def test_upload_png_fixture(mock_upload, mock_enqueue, client):
    file_path = FIXTURES_DIR / "diagram.png"
    with file_path.open("rb") as f:
        response = client.post(
            "/upload",
            files={"file": (file_path.name, f, "image/png")},
        )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "received"
    assert data["filename"] == "diagram.png"
    assert "id" in data


@patch("app.routes.enqueue_processing")
@patch("app.routes.upload_file")
def test_upload_jpeg_fixture(mock_upload, mock_enqueue, client):
    file_path = FIXTURES_DIR / "diagram.jpg"
    with file_path.open("rb") as f:
        response = client.post(
            "/upload",
            files={"file": (file_path.name, f, "image/jpeg")},
        )
    assert response.status_code == 202
    assert response.json()["status"] == "received"


@patch("app.routes.enqueue_processing")
@patch("app.routes.upload_file")
def test_upload_pdf_fixture(mock_upload, mock_enqueue, client):
    file_path = FIXTURES_DIR / "diagram.pdf"
    with file_path.open("rb") as f:
        response = client.post(
            "/upload",
            files={"file": (file_path.name, f, "application/pdf")},
        )
    assert response.status_code == 202
    assert response.json()["status"] == "received"


@patch("app.routes.enqueue_processing")
@patch("app.routes.upload_file")
def test_upload_and_check_status(mock_upload, mock_enqueue, client):
    """Faz upload de um arquivo real e verifica o status em seguida."""
    file_path = FIXTURES_DIR / "diagram.png"
    with file_path.open("rb") as f:
        upload_resp = client.post(
            "/upload",
            files={"file": (file_path.name, f, "image/png")},
        )
    assert upload_resp.status_code == 202
    analysis_id = upload_resp.json()["id"]

    status_resp = client.get(f"/status/{analysis_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["id"] == analysis_id
    assert status_resp.json()["status"] == "received"
    assert status_resp.json()["filename"] == "diagram.png"
