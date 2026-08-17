from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "test", "staging", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Central, typed application configuration read from environment
    variables / ``.env``. No module reads ``os.environ`` directly — every
    setting the application needs is declared here (D-alinhado a
    ``docs/backend/BACKEND_ARCHITECTURE.md`` §1).
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "GestorFrete ERP Enterprise API"
    environment: Environment = Field(default="local")
    debug: bool = Field(default=False)
    log_level: LogLevel = Field(default="INFO")

    # PostgreSQL
    database_url: str = Field(
        default="postgresql+asyncpg://gestorfrete:gestorfrete@localhost:5432/gestorfrete"
    )
    database_pool_size: int = Field(default=5)
    database_max_overflow: int = Field(default=10)
    database_pool_timeout_seconds: int = Field(default=30)

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")

    # RabbitMQ
    rabbitmq_url: str = Field(default="amqp://gestorfrete:gestorfrete@localhost:5672/")

    # MinIO
    minio_endpoint: str = Field(default="localhost:9000")
    minio_access_key: str = Field(default="gestorfrete")
    minio_secret_key: str = Field(default="gestorfrete123")
    minio_secure: bool = Field(default=False)

    # Mapbox
    mapbox_access_token: str = Field(default="")

    # CORS — origens do Frontend autorizadas a chamar a API a partir do navegador (Sprint 12).
    # `curl`/servidor-a-servidor não são afetados por CORS; sem isso, todo `fetch()` real do
    # navegador falha silenciosamente antes mesmo de chegar à autenticação.
    cors_origins: list[str] = Field(default=["http://localhost:3000", "http://localhost:3001"])

    # JWT (fundação — sem fluxo de login implementado nesta etapa, D-alinhado a AUTHENTICATION.md)
    jwt_secret_key: str = Field(default="change-me")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=30)

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()

