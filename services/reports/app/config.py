from shared.config import BaseConfig


class ProcessorConfig(BaseConfig):
    # Use the same database as upload service for shared Analysis model
    database_url: str = "postgresql://app:app@postgres/app"
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "diagrams"


settings = ProcessorConfig()
