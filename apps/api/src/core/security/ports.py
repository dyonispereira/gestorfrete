from __future__ import annotations

from typing import Any, Protocol


class PasswordHasher(Protocol):
    """Contract for hashing and verifying user passwords.

    No concrete implementation exists yet — login is out of scope for this
    foundation stage. This contract exists so ``identity_access`` can be
    built against a stable interface once authentication is implemented.
    """

    def hash(self, plain_password: str) -> str: ...

    def verify(self, plain_password: str, hashed_password: str) -> bool: ...


class TokenService(Protocol):
    """Contract for issuing and validating JWT access tokens."""

    def issue_access_token(self, subject: str, claims: dict[str, Any]) -> str: ...

    def decode_access_token(self, token: str) -> dict[str, Any]: ...
