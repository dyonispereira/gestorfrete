from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from core.exceptions.base import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DomainError,
    IntegrationError,
    InfrastructureError,
    NotFoundError,
    ValidationError,
)
from core.exceptions.handlers import register_exception_handlers


@pytest.mark.parametrize(
    ("exc_class", "expected_status"),
    [
        (ValidationError, 400),
        (AuthenticationError, 401),
        (AuthorizationError, 403),
        (NotFoundError, 404),
        (ConflictError, 409),
        (DomainError, 422),
        (InfrastructureError, 500),
    ],
)
def test_each_exception_class_carries_its_error_model_http_status(exc_class, expected_status) -> None:
    assert exc_class.http_status == expected_status


def test_integration_error_defaults_to_502_but_accepts_504_for_timeouts() -> None:
    assert IntegrationError("X", "msg").http_status == 502
    assert IntegrationError("X", "msg", http_status=504).http_status == 504


class _Payload(BaseModel):
    name: str


def _build_test_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom/domain")
    def boom_domain():
        raise DomainError("FREIGHT_TRIP_INVALID_STATUS_TRANSITION", "Transição inválida.")

    @app.get("/boom/not-found")
    def boom_not_found():
        raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")

    @app.get("/boom/unhandled")
    def boom_unhandled():
        raise ValueError("some internal detail that must never leak")

    @app.post("/validate")
    def validate(payload: _Payload):
        return {"ok": True}

    return app


@pytest.fixture
def client() -> TestClient:
    return TestClient(_build_test_app(), raise_server_exceptions=False)


class TestExceptionHandlers:
    def test_domain_error_returns_422_with_error_envelope(self, client: TestClient) -> None:
        response = client.get("/boom/domain")

        assert response.status_code == 422
        body = response.json()
        assert body["error"]["code"] == "FREIGHT_TRIP_INVALID_STATUS_TRANSITION"
        assert body["error"]["message"] == "Transição inválida."
        assert body["error"]["details"] == []

    def test_not_found_error_returns_404(self, client: TestClient) -> None:
        response = client.get("/boom/not-found")

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "FREIGHT_TRIP_NOT_FOUND"

    def test_unhandled_exception_returns_500_without_leaking_the_exception_message(
        self, client: TestClient
    ) -> None:
        response = client.get("/boom/unhandled")

        assert response.status_code == 500
        body = response.json()
        assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
        assert "some internal detail" not in response.text

    def test_request_validation_error_returns_400_with_field_details(self, client: TestClient) -> None:
        response = client.post("/validate", json={})

        assert response.status_code == 400
        body = response.json()
        assert body["error"]["code"] == "VALIDATION_FAILED"
        assert any(detail["field"] == "name" for detail in body["error"]["details"])

    def test_envelope_always_carries_request_id_and_correlation_id_keys(self, client: TestClient) -> None:
        response = client.get("/boom/not-found")

        assert "request_id" in response.json()["error"]
        assert "correlation_id" in response.json()["error"]
