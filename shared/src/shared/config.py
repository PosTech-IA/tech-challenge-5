from pydantic_settings import BaseSettings


class BaseConfig(BaseSettings):
    redis_url: str = "redis://redis:6379/0"
    # Default database is upload_db (shared by upload and processor services)
    # Reports service should override to use reports_db if needed
    database_url: str = "postgresql://app:app@postgres/upload_db"
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "diagrams"

    model_config = {"env_file": ".env", "extra": "ignore"}
