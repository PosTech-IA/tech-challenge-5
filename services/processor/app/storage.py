import io
import base64

from minio import Minio
from minio.error import S3Error

from app.config import settings

_client: Minio | None = None


def _get_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=False,
        )
    return _client


def download_file(file_ref: str) -> bytes:
    client = _get_client()
    try:
        response = client.get_object(settings.minio_bucket, file_ref)
        data = response.read()
        response.close()
        response.release_conn()
        return data
    except S3Error:
        raise


def encode_image(file_bytes: bytes) -> str:
    """Return base64-encoded string of bytes suitable for embedding in requests."""
    return base64.b64encode(file_bytes).decode("ascii")
