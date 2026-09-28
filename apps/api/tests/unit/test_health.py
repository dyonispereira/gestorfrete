from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    def test_health_returns_ok(self, client: TestClient) -> None:
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_liveness_never_checks_external_dependencies(self, client: TestClient) -> None:
        """Must always return 200 regardless of Postgres/Redis/RabbitMQ/MinIO
        availability — this sandbox has none of them running, which is
        exactly what proves liveness never depends on them."""

        response = client.get("/health/live")

        assert response.status_code == 200
        assert response.json() == {"status": "alive"}

    def test_readiness_reports_every_dependency_individually(self, client: TestClient) -> None:
        """Environment-agnostic on purpose: asserts the *shape* of the
        readiness contract (all four dependencies reported, status code
        matches the aggregate) rather than a specific pass/fail outcome —
        the same test must be meaningful both with no infra running (this
        sandbox) and with ``docker compose up`` actually up (CI/local).
        ``RABBITMQ_ENABLED`` defaults to ``true`` (unset in this fixture's
        env), so ``rabbitmq`` is still a real bool here — the "disabled"
        string case is covered by ``TestRabbitMqReadinessToggle`` below."""

        response = client.get("/health/ready")
        body = response.json()

        assert set(body["checks"].keys()) == {"database", "redis", "rabbitmq", "storage"}
        assert all(isinstance(v, bool) for v in body["checks"].values())

        all_ready = all(body["checks"].values())
        if all_ready:
            assert response.status_code == 200
            assert body["status"] == "ready"
        else:
            assert response.status_code == 503
            assert body["status"] == "not_ready"

    def test_request_and_correlation_id_headers_are_always_present(self, client: TestClient) -> None:
        response = client.get("/health")

        assert response.headers["X-Request-Id"]
        assert response.headers["X-Correlation-Id"]

    def test_correlation_id_supplied_by_the_caller_is_echoed_back(self, client: TestClient) -> None:
        response = client.get("/health", headers={"X-Correlation-Id": "caller-supplied-id"})

        assert response.headers["X-Correlation-Id"] == "caller-supplied-id"


class TestRabbitMqReadinessToggle:
    """Production Readiness Hardening, Parte 2 — o piloto roda com RABBITMQ_ENABLED=false (nenhum
    publisher/consumidor real existe hoje); `/health/ready` nunca pode ficar permanentemente 503 por
    uma dependência que a configuração do ambiente explicitamente desligou."""

    @staticmethod
    def _reset_settings_derived_caches() -> None:
        """`create_app()` runs `identity_access.wiring.register()`, which sets a module-level
        global (`core.security.session_validation._session_validator`, outside any `lru_cache`) to
        a real `SqlAlchemySessionValidator` bound to whatever `get_session_factory()` returns *at
        that exact moment* — its own docstring warns this leaks into later tests if not reset.
        `get_engine()`/`get_session_factory()` are separately `@lru_cache`d too — all need clearing
        for a clean slate regardless of which test runs next."""

        from core.config.settings import get_settings
        from core.database.session import get_engine, get_session_factory
        from core.security.session_validation import reset_session_validator

        reset_session_validator()
        get_engine.cache_clear()
        get_session_factory.cache_clear()
        get_settings.cache_clear()

    def test_disabled_rabbitmq_is_reported_but_never_blocks_readiness(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("RABBITMQ_ENABLED", "false")
        self._reset_settings_derived_caches()
        try:
            from main import create_app

            with TestClient(create_app()) as disabled_client:
                response = disabled_client.get("/health/ready")
                body = response.json()

                assert body["checks"]["rabbitmq"] == "disabled"

                # "disabled" nunca entra na conta de pronto/não-pronto — o status agregado depende
                # só das dependências que o ambiente de fato declara como necessárias.
                other_checks = {key: value for key, value in body["checks"].items() if key != "rabbitmq"}
                if all(other_checks.values()):
                    assert response.status_code == 200
                    assert body["status"] == "ready"
                else:
                    assert response.status_code == 503
                    assert body["status"] == "not_ready"
        finally:
            self._reset_settings_derived_caches()

    def test_enabled_rabbitmq_is_still_genuinely_checked(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("RABBITMQ_ENABLED", "true")
        self._reset_settings_derived_caches()
        try:
            from main import create_app

            with TestClient(create_app()) as enabled_client:
                response = enabled_client.get("/health/ready")
                body = response.json()

                # Nunca "disabled" quando habilitado — sempre o resultado real de
                # check_rabbitmq_connection(), mesmo que o resultado seja False (sem infra rodando).
                assert isinstance(body["checks"]["rabbitmq"], bool)
        finally:
            self._reset_settings_derived_caches()
