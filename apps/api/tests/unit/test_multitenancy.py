from __future__ import annotations

import uuid

import pytest

from core.multitenancy.context import (
    TenantNotSetError,
    get_current_tenant_id,
    reset_current_tenant_id,
    set_current_tenant_id,
)


class TestTenantContext:
    def test_get_without_set_raises_tenant_not_set_error(self) -> None:
        with pytest.raises(TenantNotSetError):
            get_current_tenant_id()

    def test_set_then_get_returns_the_same_tenant(self) -> None:
        tenant_id = uuid.uuid4()
        token = set_current_tenant_id(tenant_id)
        try:
            assert get_current_tenant_id() == tenant_id
        finally:
            reset_current_tenant_id(token)

    def test_reset_clears_the_tenant_back_to_unset(self) -> None:
        token = set_current_tenant_id(uuid.uuid4())
        reset_current_tenant_id(token)

        with pytest.raises(TenantNotSetError):
            get_current_tenant_id()
