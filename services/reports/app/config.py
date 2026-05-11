from shared.config import BaseConfig


class ReportsConfig(BaseConfig):
    # Reports service uses its own database
    database_url: str = "postgresql://app:app@postgres/reports_db"


settings = ReportsConfig()


