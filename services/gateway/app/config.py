from shared.config import BaseConfig


class GatewayConfig(BaseConfig):
    cors_origins: str = "https://tech-challenge-5-front.vercel.app"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allow_headers: list[str] = ["*"]
    cors_expose_headers: list[str] = ["X-Correlation-ID"]
    cors_max_age: int = 600

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = GatewayConfig()
