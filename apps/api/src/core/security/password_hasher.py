from __future__ import annotations

from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class BcryptPasswordHasher:
    """Concrete ``PasswordHasher`` (``core.security.ports``) using bcrypt via
    ``passlib``. Matches ``usuarios.senha_hash`` (D084 — never reversible,
    never logged, never returned by any endpoint, ``AUTHENTICATION.md``).
    """

    def hash(self, plain_password: str) -> str:
        return _pwd_context.hash(plain_password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return _pwd_context.verify(plain_password, hashed_password)
