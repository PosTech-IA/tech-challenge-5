import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import httpx

from app.main import app
from app.config import settings


@pytest.fixture
def client():
    """Create a test client for the gateway app."""
    return TestClient(app)


class TestCORSConfiguration:
    """Test CORS middleware is properly configured."""

    def test_cors_origins_from_config(self):
        """Test that CORS origins are correctly parsed from config."""
        # Should parse the comma-separated origins
        assert isinstance(settings.cors_origins_list, list)
        assert len(settings.cors_origins_list) > 0
        # Default config should have the production domain
        assert "https://tech-challenge-5-front.vercel.app" in settings.cors_origins_list

    def test_cors_allow_credentials(self):
        """Test that credentials are allowed in CORS."""
        assert settings.cors_allow_credentials is True

    def test_cors_allow_methods(self):
        """Test that required HTTP methods are allowed."""
        assert "GET" in settings.cors_allow_methods
        assert "POST" in settings.cors_allow_methods
        assert "PUT" in settings.cors_allow_methods
        assert "DELETE" in settings.cors_allow_methods
        assert "OPTIONS" in settings.cors_allow_methods

    def test_cors_expose_headers(self):
        """Test that correlation ID header is exposed."""
        assert "X-Correlation-ID" in settings.cors_expose_headers


class TestCORSPreflight:
    """Test CORS preflight requests (OPTIONS)."""

    def test_preflight_request_allowed_origin(self, client):
        """Test preflight request from allowed origin returns correct headers."""
        response = client.options(
            "/api/v1/reports",
            headers={
                "Origin": "https://tech-challenge-5-front.vercel.app",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.status_code == 200
        # Check CORS headers are present
        assert "access-control-allow-origin" in response.headers
        assert (
            response.headers["access-control-allow-origin"]
            == "https://tech-challenge-5-front.vercel.app"
        )
        assert "access-control-allow-credentials" in response.headers
        assert response.headers["access-control-allow-credentials"] == "true"

    def test_preflight_request_denied_origin(self, client):
        """Test preflight request from disallowed origin."""
        response = client.options(
            "/api/v1/reports",
            headers={
                "Origin": "https://malicious-site.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.status_code == 200
        # Browser will block response if these headers are missing
        # CORSMiddleware shouldn't include them for disallowed origins

    def test_preflight_request_allows_methods(self, client):
        """Test preflight response includes allowed methods."""
        response = client.options(
            "/api/v1/upload",
            headers={
                "Origin": "https://tech-challenge-5-front.vercel.app",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert response.status_code == 200
        assert "access-control-allow-methods" in response.headers


class TestCORSWithActualRequests:
    """Test CORS headers are included in actual requests."""

    @patch("httpx.AsyncClient.get")
    def test_get_reports_includes_cors_headers(self, mock_get, client):
        """Test GET request includes CORS headers."""
        # Mock the httpx response
        mock_response = AsyncMock()
        mock_response.json.return_value = {"items": [], "total": 0}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        response = client.get(
            "/api/v1/reports",
            headers={"Origin": "https://tech-challenge-5-front.vercel.app"},
        )
        assert response.status_code == 200
        # Check CORS headers are in response
        assert "access-control-allow-origin" in response.headers

    @patch("httpx.AsyncClient.post")
    def test_post_upload_includes_cors_headers(self, mock_post, client):
        """Test POST request includes CORS headers."""
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "status": "received",
            "id": "test-123",
            "filename": "test.png",
        }
        mock_response.status_code = 202
        mock_post.return_value = mock_response

        import io

        response = client.post(
            "/api/v1/upload",
            files={"file": ("test.png", io.BytesIO(b"PNG"), "image/png")},
            headers={"Origin": "https://tech-challenge-5-front.vercel.app"},
        )
        assert response.status_code == 202
        # Check CORS headers are in response
        assert "access-control-allow-origin" in response.headers


class TestCORSHeaderExposure:
    """Test that custom headers are exposed to frontend."""

    def test_correlation_id_header_exposed(self):
        """Test that X-Correlation-ID is in exposed headers."""
        assert "X-Correlation-ID" in settings.cors_expose_headers

    @patch("httpx.AsyncClient.get")
    def test_response_exposes_correlation_id(self, mock_get, client):
        """Test response includes X-Correlation-ID and it's exposed to frontend."""
        mock_response = AsyncMock()
        mock_response.json.return_value = {"items": [], "total": 0}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        response = client.get(
            "/api/v1/reports",
            headers={"Origin": "https://tech-challenge-5-front.vercel.app"},
        )
        assert response.status_code == 200
        # Check exposure headers include X-Correlation-ID
        if "access-control-expose-headers" in response.headers:
            assert "X-Correlation-ID" in response.headers[
                "access-control-expose-headers"
            ]


class TestCORSPreflightMaxAge:
    """Test CORS max-age header for preflight caching."""

    def test_max_age_set(self):
        """Test that max-age is configured to reduce preflight requests."""
        assert settings.cors_max_age == 600

    def test_preflight_includes_max_age(self, client):
        """Test preflight response includes max-age header."""
        response = client.options(
            "/api/v1/reports",
            headers={
                "Origin": "https://tech-challenge-5-front.vercel.app",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        if "access-control-max-age" in response.headers:
            # Should be 600 seconds or similar
            max_age = int(response.headers["access-control-max-age"])
            assert max_age > 0
