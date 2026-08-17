from __future__ import annotations

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
        sandbox) and with ``docker compose up`` actually up (CI/local)."""

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
