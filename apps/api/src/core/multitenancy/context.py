from __future__ import annotations

import uuid
from contextvars import ContextVar, Token

_current_tenant_id: ContextVar[uuid.UUID | None] = ContextVar("current_tenant_id", default=None)


class TenantNotSetError(RuntimeError):
    """Raised when code that requires a tenant in scope runs without one.

    Every request that reaches a bounded context must have a tenant resolved
    first (by the tenant-resolution middleware, added in a later stage) —
    this guards against accidentally querying/writing data with no tenant
    isolation.
    """


def set_current_tenant_id(tenant_id: uuid.UUID) -> Token[uuid.UUID | None]:
    return _current_tenant_id.set(tenant_id)


def reset_current_tenant_id(token: Token[uuid.UUID | None]) -> None:
    _current_tenant_id.reset(token)


def get_current_tenant_id() -> uuid.UUID:
    tenant_id = _current_tenant_id.get()
    if tenant_id is None:
        raise TenantNotSetError("No tenant is set in the current execution context")
    return tenant_id
