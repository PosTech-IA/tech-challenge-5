from pydantic_settings import BaseSettings


class BaseConfig(BaseSettings):
    redis_url: str = "redis://redis:6379/0"
    database_url: str = "postgresql://app:app@postgres/app"

    model_config = {"env_file": ".env", "extra": "ignore"}
