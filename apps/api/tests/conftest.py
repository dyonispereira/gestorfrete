from __future__ import annotations

import os
import uuid
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

# Environment must be set before ``core.config.settings.get_settings()`` is
# ever called by anything imported below — pytest collects this module
# first, so this is the one place allowed to touch ``os.environ`` directly
# in the whole codebase (D-alinhado a BACKEND_ARCHITECTURE.md §1).
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")


@pytest.fixture
def app():
    from main import create_app

    return create_app()


@pytest.fixture
def client(app) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def session_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def access_token(tenant_id: uuid.UUID, user_id: uuid.UUID, session_id: uuid.UUID) -> str:
    from core.config.settings import get_settings
    from core.security.jwt_token_service import JWTTokenService

    service = JWTTokenService(get_settings())
    return service.issue_access_token(
        subject=str(user_id),
        claims={"tenant_id": str(tenant_id), "session_id": str(session_id)},
    )
