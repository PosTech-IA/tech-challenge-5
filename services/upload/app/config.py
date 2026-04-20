from shared.config import BaseConfig


class UploadConfig(BaseConfig):
    database_url: str = "postgresql://app:app@postgres/upload_db"
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "diagrams"


settings = UploadConfig()
