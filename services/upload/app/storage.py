import io

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


def _ensure_bucket() -> None:
    client = _get_client()
    try:
        if not client.bucket_exists(settings.minio_bucket):
            client.make_bucket(settings.minio_bucket)
    except S3Error:
        pass


def upload_file(file_bytes: bytes, content_type: str, file_ref: str) -> None:
    _ensure_bucket()
    client = _get_client()
    client.put_object(
        settings.minio_bucket,
        file_ref,
        io.BytesIO(file_bytes),
        length=len(file_bytes),
        content_type=content_type,
    )
