from pydantic_settings import BaseSettings


class BaseConfig(BaseSettings):
    # Railway auto-provides DATABASE_URL and REDIS_URL
    # Fallbacks are for local development
    database_url: str = "postgresql://app:app@postgres/upload_db"
    redis_url: str = "redis://redis:6379/0"
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "diagrams"

    model_config = {"env_file": ".env", "extra": "ignore"}
