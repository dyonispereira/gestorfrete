from __future__ import annotations

import uuid
from typing import Protocol


class SessionValidator(Protocol):
    """Port checked by ``interfaces.dependencies.auth.get_current_actor`` before it trusts a
    decoded JWT — Foundation (``core``) declares the contract, ``modules.identity_access`` (the
    bounded context that owns ``Sessão de Acesso``) provides the real implementation, wired once at
    application startup (``modules.identity_access.wiring.register``). ``core`` never imports
    ``modules.identity_access`` directly (``DEPENDENCY_RULES.md``) — this indirection is what keeps
    that true while still letting session revocation take effect on every request.
    """

    async def is_session_valid(self, session_id: uuid.UUID) -> bool: ...


class _NullSessionValidator:
    """Default before any bounded context wires a real validator — every session is considered
    valid, exactly Lote 1's behavior (no session store existed yet). Never used once
    ``identity_access`` registers its real validator during app startup.
    """

    async def is_session_valid(self, session_id: uuid.UUID) -> bool:
        return True


_session_validator: SessionValidator = _NullSessionValidator()


def set_session_validator(validator: SessionValidator) -> None:
    global _session_validator
    _session_validator = validator


def get_session_validator() -> SessionValidator:
    return _session_validator


def reset_session_validator() -> None:
    """Restores the default ``_NullSessionValidator`` — for test isolation only. This holder is
    meant to be set exactly once, at real application startup (``main.py``); a test that builds its
    own app via ``create_app()`` (wiring the real validator through
    ``modules.identity_access.wiring.register``) must call this afterward, or the mutation leaks
    into unrelated tests that run later in the same pytest process.
    """

    global _session_validator
    _session_validator = _NullSessionValidator()
