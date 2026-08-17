from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from core.config.settings import Settings
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import AuthenticationError
from core.security.jwt_token_service import InvalidTokenError, JWTTokenService, TokenExpiredError
from modules.identity_access.application.commands.login import SESSION_TTL_MINUTES
from modules.identity_access.application.dtos.auth_dto import TokenPairDTO
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_session_repository import (
    SqlAlchemySessionRepository,
)
from shared_kernel.application.command import Command, CommandHandler


@dataclass(frozen=True)
class RefreshTokenCommand(Command):
    refresh_token: str


class RefreshTokenHandler(CommandHandler[RefreshTokenCommand, TokenPairDTO]):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._token_service = JWTTokenService(settings)

    async def handle(self, command: RefreshTokenCommand) -> TokenPairDTO:
        try:
            claims = self._token_service.decode_access_token(command.refresh_token)
        except (TokenExpiredError, InvalidTokenError) as exc:
            raise AuthenticationError(
                "IDENTITY_REFRESH_TOKEN_INVALID", "Refresh token inválido ou expirado."
            ) from exc

        if claims.get("purpose") != "refresh":
            raise AuthenticationError(
                "IDENTITY_REFRESH_TOKEN_INVALID", "Token informado não é um refresh token."
            )

        try:
            user_id = uuid.UUID(str(claims["sub"]))
            tenant_id = uuid.UUID(str(claims["tenant_id"]))
            session_id = uuid.UUID(str(claims["session_id"]))
        except (KeyError, ValueError) as exc:
            raise AuthenticationError("IDENTITY_REFRESH_TOKEN_INVALID", "Refresh token malformado.") from exc

        async with SQLAlchemyUnitOfWork() as uow:
            session_repo = SqlAlchemySessionRepository(uow.session)
            session = await session_repo.get_by_id(session_id)
            now = datetime.now(timezone.utc)
            if session is None or not session.is_valid(now):
                raise AuthenticationError(
                    "IDENTITY_REFRESH_TOKEN_INVALID", "Sessão associada não está mais ativa."
                )

            session.extend(now + timedelta(minutes=SESSION_TTL_MINUTES))
            await session_repo.add(session)
            await uow.commit()

        claims_out = {"tenant_id": str(tenant_id), "session_id": str(session_id)}
        access_token = self._token_service.issue_access_token(subject=str(user_id), claims=claims_out)
        new_refresh_token = self._token_service.issue_access_token(
            subject=str(user_id), claims={**claims_out, "purpose": "refresh"}
        )
        return TokenPairDTO(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=self._settings.jwt_access_token_expire_minutes * 60,
        )
