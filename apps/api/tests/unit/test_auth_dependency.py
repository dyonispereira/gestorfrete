from __future__ import annotations

import uuid

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from core.exceptions.handlers import register_exception_handlers
from core.multitenancy.context import get_current_tenant_id
from interfaces.dependencies.auth import get_current_actor
from shared_kernel.domain.actor import AuthenticatedActor


def _build_test_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/whoami")
    def whoami(actor: AuthenticatedActor = Depends(get_current_actor)):
        # Proves the tenant ContextVar is populated *during* request
        # handling, not just returned as a field on the actor object.
        assert get_current_tenant_id() == actor.tenant_id
        return {"user_id": str(actor.user_id), "tenant_id": str(actor.tenant_id)}

    return app


@pytest.fixture
def client() -> TestClient:
    return TestClient(_build_test_app(), raise_server_exceptions=False)


class TestGetCurrentActor:
    def test_valid_token_resolves_actor_and_sets_tenant_context(
        self, client: TestClient, access_token: str, tenant_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        response = client.get("/whoami", headers={"Authorization": f"Bearer {access_token}"})

        assert response.status_code == 200
        body = response.json()
        assert body["tenant_id"] == str(tenant_id)
        assert body["user_id"] == str(user_id)

    def test_missing_authorization_header_returns_401(self, client: TestClient) -> None:
        response = client.get("/whoami")

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "IDENTITY_MISSING_CREDENTIALS"

    def test_malformed_token_returns_401(self, client: TestClient) -> None:
        response = client.get("/whoami", headers={"Authorization": "Bearer not-a-real-jwt"})

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "IDENTITY_INVALID_CREDENTIALS"

    def test_tenant_context_is_reset_after_the_request_completes(
        self, client: TestClient, access_token: str
    ) -> None:
        client.get("/whoami", headers={"Authorization": f"Bearer {access_token}"})

        from core.multitenancy.context import TenantNotSetError

        with pytest.raises(TenantNotSetError):
            get_current_tenant_id()
