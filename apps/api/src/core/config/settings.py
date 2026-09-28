from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
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

    # RabbitMQ — Production Readiness Hardening, Parte 2: nenhum publisher/consumidor real existe
    # hoje (D375-style, todo lote anterior só documentou o consumo futuro). `rabbitmq_enabled=False`
    # é a configuração explícita do piloto — `/health/ready` para de depender de uma dependência que
    # nenhum fluxo de negócio realmente usa, sem apagar o código de mensageria em si (fica pronto
    # para quando um consumidor real existir).
    rabbitmq_url: str = Field(default="amqp://gestorfrete:gestorfrete@localhost:5672/")
    rabbitmq_enabled: bool = Field(default=True)

    # MinIO
    minio_endpoint: str = Field(default="localhost:9000")
    minio_access_key: str = Field(default="gestorfrete")
    minio_secret_key: str = Field(default="gestorfrete123")
    minio_secure: bool = Field(default=False)

    # Upload — Production Readiness Hardening, Parte 3: teto de tamanho por ambiente. 15MB cobre com
    # folga XML de CT-e/MDF-e (poucos KB) e foto de canhoto/evidência (poucos MB) sem abrir a porta
    # para upload de qualquer tamanho direto ao Storage via URL assinada.
    upload_max_size_bytes: int = Field(default=15 * 1024 * 1024)

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

    @model_validator(mode="after")
    def _reject_insecure_production_config(self) -> "Settings":
        """Production Readiness Hardening, Parte 1 — `is_production` existia como propriedade desde
        sempre mas nenhum código a consultava (Discovery de Ambiente confirmou isso como gap real):
        nada impedia `ENVIRONMENT=production` de subir com `JWT_SECRET_KEY=change-me` ou a senha de
        banco padrão de desenvolvimento. Roda no momento em que `Settings()` é construído — que é
        `main.py:create_app()`, chamado na importação do módulo (`app = create_app()`), então uma
        configuração insegura derruba o processo antes de aceitar uma única requisição, nunca
        silenciosamente em produção."""

        if self.environment != "production":
            return self

        problems: list[str] = []

        if not self.jwt_secret_key.strip() or self.jwt_secret_key == "change-me":
            problems.append("JWT_SECRET_KEY não pode ser vazio nem o valor padrão 'change-me'.")

        if not self.database_url.strip():
            problems.append("DATABASE_URL não pode estar vazio.")
        elif "localhost" in self.database_url or "127.0.0.1" in self.database_url:
            problems.append("DATABASE_URL não pode apontar para localhost/127.0.0.1 em produção.")
        elif "gestorfrete:gestorfrete@" in self.database_url:
            problems.append(
                "DATABASE_URL não pode usar a credencial padrão de desenvolvimento (gestorfrete:gestorfrete)."
            )

        if not self.minio_secret_key.strip() or self.minio_secret_key == "gestorfrete123":
            problems.append("MINIO_SECRET_KEY não pode ser vazio nem o valor padrão de desenvolvimento.")

        if self.rabbitmq_enabled and not self.rabbitmq_url.strip():
            problems.append("RABBITMQ_URL não pode estar vazio quando RABBITMQ_ENABLED=true.")

        if self.debug:
            problems.append("DEBUG deve ser false em produção.")

        if not self.cors_origins or all(
            "localhost" in origin or "127.0.0.1" in origin for origin in self.cors_origins
        ):
            problems.append("CORS_ORIGINS não pode conter somente origens localhost/127.0.0.1 em produção.")

        if problems:
            raise ValueError(
                "Configuração insegura para ENVIRONMENT=production:\n- " + "\n- ".join(problems)
            )

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()

