import io
import base64

from minio import Minio
from minio.error import S3Error

from shared.config import BaseConfig

_client: Minio | None = None


def init_storage(config: BaseConfig) -> None:
    """Initialize Minio client with config."""
    global _client
    _client = Minio(
        config.minio_endpoint,
        access_key=config.minio_access_key,
        secret_key=config.minio_secret_key,
        secure=False,
    )


def _get_client() -> Minio:
    """Get or initialize Minio client."""
    global _client
    if _client is None:
        raise RuntimeError("Storage not initialized. Call init_storage() first.")
    return _client


def _ensure_bucket(config: BaseConfig) -> None:
    """Ensure bucket exists in Minio."""
    client = _get_client()
    try:
        if not client.bucket_exists(config.minio_bucket):
            client.make_bucket(config.minio_bucket)
    except S3Error:
        pass


def upload_file(file_bytes: bytes, content_type: str, file_ref: str, config: BaseConfig) -> None:
    """Upload file to Minio."""
    _ensure_bucket(config)
    client = _get_client()
    client.put_object(
        config.minio_bucket,
        file_ref,
        io.BytesIO(file_bytes),
        length=len(file_bytes),
        content_type=content_type,
    )


def download_file(file_ref: str, config: BaseConfig) -> bytes:
    """Download file from Minio."""
    client = _get_client()
    try:
        response = client.get_object(config.minio_bucket, file_ref)
        data = response.read()
        response.close()
        response.release_conn()
        return data
    except S3Error as e:
        raise


def encode_image(file_bytes: bytes) -> str:
    """Return base64-encoded string of bytes suitable for embedding in requests."""
    return base64.b64encode(file_bytes).decode("ascii")
