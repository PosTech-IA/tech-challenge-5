"""Test that gateway properly forwards multipart file uploads."""
import io
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from fastapi.testclient import TestClient
import httpx


@pytest.fixture
def client():
    """Create a test client for the gateway."""
    from app.main import app
    return TestClient(app)


@pytest.mark.asyncio
async def test_multipart_forwarding():
    """Test that gateway parses and forwards multipart requests correctly."""
    from app.main import app

    # Mock the upload service response
    mock_response = {
        "id": "test-id",
        "filename": "test.png",
        "file_ref": "uploads/test-id/test.png",
        "status": "received",
        "created_at": "2026-05-18T00:00:00Z"
    }

    with patch('httpx.AsyncClient.post') as mock_post:
        # Setup mock to return the expected response
        mock_resp = AsyncMock()
        mock_resp.json.return_value = mock_response
        mock_post.return_value = mock_resp

        # Make request with test file
        test_file_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/v1/upload",
                files={"file": ("test.png", io.BytesIO(test_file_content), "image/png")},
                headers={"X-Correlation-ID": "test-123"}
            )

        # Verify the response
        assert response.status_code == 200
        assert response.json() == mock_response

        # Verify that httpx.AsyncClient.post was called with files parameter
        mock_post.assert_called_once()
        call_args = mock_post.call_args

        # Check that files parameter was used
        assert 'files' in call_args.kwargs
        assert call_args.kwargs['files'] == {"file": ("test.png", test_file_content, "image/png")}


def test_multipart_forwarding_sync(client):
    """Test multipart forwarding with synchronous test client."""
    from unittest.mock import patch, MagicMock

    mock_response = {
        "id": "test-id",
        "filename": "test.png",
        "file_ref": "uploads/test-id/test.png",
        "status": "received",
        "created_at": "2026-05-18T00:00:00Z"
    }

    test_file_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

    with patch('httpx.AsyncClient') as mock_client_class:
        # Setup mock async client
        mock_client = AsyncMock()
        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response
        mock_response_obj.status_code = 200

        # Make the post method async
        async def async_post(*args, **kwargs):
            return mock_response_obj

        mock_client.post = async_post
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client

        response = client.post(
            "/api/v1/upload",
            files={"file": ("test.png", io.BytesIO(test_file_content), "image/png")},
            headers={"X-Correlation-ID": "test-123"}
        )

        # Should get the mocked response
        assert response.status_code == 200


def test_no_file_error(client):
    """Test that request without file is properly handled."""
    response = client.post(
        "/api/v1/upload",
        headers={"X-Correlation-ID": "test-123"}
    )

    # Should get 500 error when no file provided
    assert response.status_code == 500
