from __future__ import annotations

import time

import pytest

from core.config.settings import Settings
from core.security.jwt_token_service import InvalidTokenError, JWTTokenService, TokenExpiredError
from core.security.password_hasher import BcryptPasswordHasher


@pytest.fixture
def settings() -> Settings:
    return Settings(jwt_secret_key="unit-test-secret", jwt_algorithm="HS256")


class TestJWTTokenService:
    def test_issued_token_decodes_back_to_the_same_claims(self, settings: Settings) -> None:
        service = JWTTokenService(settings)
        token = service.issue_access_token(subject="user-1", claims={"tenant_id": "tenant-1"})

        claims = service.decode_access_token(token)

        assert claims["sub"] == "user-1"
        assert claims["tenant_id"] == "tenant-1"
        assert "exp" in claims and "iat" in claims

    def test_expired_token_raises_token_expired_error(self, settings: Settings) -> None:
        settings.jwt_access_token_expire_minutes = 0
        service = JWTTokenService(settings)
        token = service.issue_access_token(subject="user-1", claims={})
        time.sleep(1.1)

        with pytest.raises(TokenExpiredError):
            service.decode_access_token(token)

    def test_tampered_token_raises_invalid_token_error(self, settings: Settings) -> None:
        service = JWTTokenService(settings)
        token = service.issue_access_token(subject="user-1", claims={})

        with pytest.raises(InvalidTokenError):
            service.decode_access_token(token + "tampered")

    def test_token_signed_with_a_different_secret_is_rejected(self, settings: Settings) -> None:
        issuer = JWTTokenService(Settings(jwt_secret_key="secret-a"))
        verifier = JWTTokenService(Settings(jwt_secret_key="secret-b"))
        token = issuer.issue_access_token(subject="user-1", claims={})

        with pytest.raises(InvalidTokenError):
            verifier.decode_access_token(token)


class TestBcryptPasswordHasher:
    def test_verify_succeeds_for_the_correct_password(self) -> None:
        hasher = BcryptPasswordHasher()
        hashed = hasher.hash("correct horse battery staple")

        assert hasher.verify("correct horse battery staple", hashed)

    def test_verify_fails_for_the_wrong_password(self) -> None:
        hasher = BcryptPasswordHasher()
        hashed = hasher.hash("correct horse battery staple")

        assert not hasher.verify("wrong password", hashed)

    def test_hash_never_equals_the_plain_password(self) -> None:
        hasher = BcryptPasswordHasher()
        assert hasher.hash("my-password") != "my-password"
