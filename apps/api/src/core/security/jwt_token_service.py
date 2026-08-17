from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError

from core.config.settings import Settings


class TokenExpiredError(Exception):
    """Raised when decoding a JWT whose ``exp`` claim has already passed."""


class InvalidTokenError(Exception):
    """Raised when a JWT is malformed, has an invalid signature, or is
    otherwise unusable — never exposes the underlying ``jose`` exception to
    callers, so this is the only exception type ``core.security`` raises.
    """


class JWTTokenService:
    """Concrete ``TokenService`` (``core.security.ports``) using
    ``python-jose``. Issues and validates the access tokens used by every
    authentication surface (Web/Mobile/API, ``AUTHENTICATION.md``) — no
    login endpoint exists yet (Sprint 11 Lote 2), this only provides the
    mechanism so ``identity_access`` has a stable contract to build against.
    """

    def __init__(self, settings: Settings) -> None:
        self._secret_key = settings.jwt_secret_key
        self._algorithm = settings.jwt_algorithm
        self._expire_minutes = settings.jwt_access_token_expire_minutes

    def issue_access_token(self, subject: str, claims: dict[str, Any]) -> str:
        now = datetime.now(timezone.utc)
        payload: dict[str, Any] = {
            **claims,
            "sub": subject,
            "iat": now,
            "exp": now + timedelta(minutes=self._expire_minutes),
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def decode_access_token(self, token: str) -> dict[str, Any]:
        try:
            return jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
        except ExpiredSignatureError as exc:
            raise TokenExpiredError("Access token has expired") from exc
        except JWTError as exc:
            raise InvalidTokenError("Access token is malformed or has an invalid signature") from exc
