from __future__ import annotations

import pytest
from pydantic import ValidationError

from core.config.settings import Settings

_SECURE_KWARGS: dict[str, object] = {
    "environment": "production",
    "jwt_secret_key": "a-real-random-secret-generated-for-this-deployment",
    "database_url": "postgresql+asyncpg://gestorfrete_app:a-real-password@db.internal.example.com:5432/gestorfrete",
    "minio_secret_key": "a-real-random-minio-secret",
    "debug": False,
    "cors_origins": ["https://app.pilot.gestorfrete.example.com"],
}


class TestProductionConfigGuard:
    """Production Readiness Hardening, Parte 1 — `ENVIRONMENT=production` com qualquer default
    inseguro de desenvolvimento deve derrubar `Settings()` na construção (startup), nunca subir
    silenciosamente. Fora de `environment="production"`, nenhuma dessas checagens roda — os mesmos
    defaults continuam válidos para local/test/staging."""

    def test_secure_production_config_does_not_raise(self) -> None:
        settings = Settings(**_SECURE_KWARGS)  # type: ignore[arg-type]

        assert settings.is_production is True

    def test_non_production_environment_skips_every_check(self) -> None:
        # Todos os campos explicitamente inseguros — environment != production nunca valida isso,
        # mesmo com todo o resto igual ao que rejeitaria a construção em produção.
        insecure_but_local = {**_SECURE_KWARGS, "environment": "local"}
        insecure_but_local.update(
            jwt_secret_key="change-me",
            database_url="postgresql+asyncpg://gestorfrete:gestorfrete@localhost:5432/gestorfrete",
            minio_secret_key="gestorfrete123",
            debug=True,
            cors_origins=["http://localhost:3000"],
        )

        settings = Settings(**insecure_but_local)  # type: ignore[arg-type]

        assert settings.jwt_secret_key == "change-me"
        assert settings.is_production is False

    @pytest.mark.parametrize(
        "override,expected_fragment",
        [
            ({"jwt_secret_key": "change-me"}, "JWT_SECRET_KEY"),
            ({"jwt_secret_key": ""}, "JWT_SECRET_KEY"),
            ({"database_url": "postgresql+asyncpg://gestorfrete:gestorfrete@localhost:5432/gestorfrete"}, "DATABASE_URL"),
            ({"database_url": "postgresql+asyncpg://user:pass@127.0.0.1:5432/db"}, "DATABASE_URL"),
            ({"database_url": ""}, "DATABASE_URL"),
            (
                {"database_url": "postgresql+asyncpg://gestorfrete:gestorfrete@db.internal.example.com:5432/gestorfrete"},
                "DATABASE_URL",
            ),
            ({"minio_secret_key": "gestorfrete123"}, "MINIO_SECRET_KEY"),
            ({"minio_secret_key": ""}, "MINIO_SECRET_KEY"),
            ({"debug": True}, "DEBUG"),
            ({"cors_origins": ["http://localhost:3000"]}, "CORS_ORIGINS"),
            ({"cors_origins": ["http://localhost:3000", "http://127.0.0.1:3001"]}, "CORS_ORIGINS"),
            ({"cors_origins": []}, "CORS_ORIGINS"),
            ({"rabbitmq_enabled": True, "rabbitmq_url": ""}, "RABBITMQ_URL"),
        ],
    )
    def test_each_insecure_default_rejects_startup(
        self, override: dict[str, object], expected_fragment: str
    ) -> None:
        kwargs = {**_SECURE_KWARGS, **override}

        with pytest.raises(ValidationError) as exc_info:
            Settings(**kwargs)  # type: ignore[arg-type]

        assert expected_fragment in str(exc_info.value)

    def test_rabbitmq_disabled_does_not_require_a_real_url(self) -> None:
        settings = Settings(**{**_SECURE_KWARGS, "rabbitmq_enabled": False, "rabbitmq_url": ""})  # type: ignore[arg-type]

        assert settings.rabbitmq_enabled is False

    def test_multiple_problems_are_all_reported_at_once(self) -> None:
        # Todo campo explicitamente inseguro — nunca depende do ambiente de teste ambiente já ter
        # sobrescrito algum default (ex.: JWT_SECRET_KEY do conftest.py).
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                environment="production",
                jwt_secret_key="change-me",
                database_url="postgresql+asyncpg://gestorfrete:gestorfrete@localhost:5432/gestorfrete",
                minio_secret_key="gestorfrete123",
                debug=True,
                cors_origins=["http://localhost:3000"],
            )

        message = str(exc_info.value)
        assert "JWT_SECRET_KEY" in message
        assert "DATABASE_URL" in message
        assert "MINIO_SECRET_KEY" in message
        assert "CORS_ORIGINS" in message
