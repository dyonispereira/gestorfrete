from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient


def _reset_settings_derived_caches() -> None:
    """Every test here calls the real ``create_app()``, which runs
    ``modules.identity_access.wiring.register()`` — that sets a **module-level global**
    (`core.security.session_validation._session_validator`, outside any ``lru_cache``) to a real
    ``SqlAlchemySessionValidator`` bound to whatever ``get_session_factory()`` returns *at that
    exact moment* — i.e., built from this test's throwaway/fake ``DATABASE_URL``. That object holds
    its session factory by direct reference, so clearing ``get_engine``/``get_session_factory``
    afterward does nothing to it — its own docstring already warns of exactly this leak
    (``core/security/session_validation.py::reset_session_validator``). ``get_engine()``/
    ``get_session_factory()`` are ``@lru_cache``d independently of ``get_settings()`` too, so all
    four need resetting, every time, for a clean slate for whichever test runs next."""

    from core.config.settings import get_settings
    from core.database.session import get_engine, get_session_factory
    from core.security.session_validation import reset_session_validator

    reset_session_validator()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
    get_settings.cache_clear()


@pytest.fixture
def _clean_settings_cache() -> Iterator[None]:
    _reset_settings_derived_caches()
    yield
    _reset_settings_derived_caches()


class TestApiDocsVisibility:
    """Production Readiness Hardening, Parte 4 — /docs, /redoc e /openapi.json sempre ficavam
    habilitados em qualquer ambiente (Discovery de Ambiente). Em produção, desabilitados por
    padrão; em development/test, continuam disponíveis exatamente como antes."""

    def test_docs_enabled_outside_production(
        self, monkeypatch: pytest.MonkeyPatch, _clean_settings_cache: None
    ) -> None:
        monkeypatch.setenv("ENVIRONMENT", "local")

        from main import create_app

        with TestClient(create_app()) as client:
            assert client.get("/docs").status_code == 200
            assert client.get("/redoc").status_code == 200
            assert client.get("/openapi.json").status_code == 200

    def test_docs_disabled_in_production(
        self, monkeypatch: pytest.MonkeyPatch, _clean_settings_cache: None
    ) -> None:
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("JWT_SECRET_KEY", "a-real-random-secret-generated-for-this-deployment")
        # Não localhost/127.0.0.1 (o guard da Parte 1 rejeitaria), mas também nunca precisa
        # resolver/conectar de verdade — nenhuma rota /docs/redoc/openapi.json toca o banco.
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql+asyncpg://gestorfrete_app:a-real-password@db.internal.invalid:5432/gestorfrete",
        )
        monkeypatch.setenv("MINIO_SECRET_KEY", "a-real-random-minio-secret")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("CORS_ORIGINS", '["https://app.pilot.gestorfrete.example.com"]')

        from main import create_app

        with TestClient(create_app()) as client:
            assert client.get("/docs").status_code == 404
            assert client.get("/redoc").status_code == 404
            assert client.get("/openapi.json").status_code == 404
