from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from core.config.settings import Settings
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import AuthenticationError
from core.security.jwt_token_service import InvalidTokenError, JWTTokenService, TokenExpiredError
from core.security.token_hasher import hash_token
from modules.identity_access.application.commands.login import SESSION_TTL_MINUTES
from modules.identity_access.application.dtos.auth_dto import TokenPairDTO
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_session_repository import (
    SqlAlchemySessionRepository,
)
from modules.mobile.infrastructure.persistence.repositories.sqlalchemy_mobile_session_repository import (
    SqlAlchemyMobileSessionRepository,
)
from shared_kernel.application.command import Command, CommandHandler


@dataclass(frozen=True)
class MobileRefreshCommand(Command):
    refresh_token: str


class MobileRefreshHandler(CommandHandler[MobileRefreshCommand, TokenPairDTO]):
    """D407 — mesma mecânica de `identity_access.application.commands.refresh_token.
    RefreshTokenHandler` (reutilizada, não reimplementada); a única adição é estender também
    `sessoes_mobile.data_hora_expiracao_prevista`/`token_acesso_hash` para acompanhar a `Sessão`
    subjacente."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._token_service = JWTTokenService(settings)

    async def handle(self, command: MobileRefreshCommand) -> TokenPairDTO:
        try:
            claims = self._token_service.decode_access_token(command.refresh_token)
        except (TokenExpiredError, InvalidTokenError) as exc:
            raise AuthenticationError(
                "MOBILE_REFRESH_TOKEN_INVALID", "Refresh token inválido ou expirado."
            ) from exc

        if claims.get("purpose") != "refresh":
            raise AuthenticationError("MOBILE_REFRESH_TOKEN_INVALID", "Token informado não é um refresh token.")

        try:
            user_id = uuid.UUID(str(claims["sub"]))
            tenant_id = uuid.UUID(str(claims["tenant_id"]))
            session_id = uuid.UUID(str(claims["session_id"]))
        except (KeyError, ValueError) as exc:
            raise AuthenticationError("MOBILE_REFRESH_TOKEN_INVALID", "Refresh token malformado.") from exc

        async with SQLAlchemyUnitOfWork() as uow:
            identity_session_repo = SqlAlchemySessionRepository(uow.session)
            mobile_session_repo = SqlAlchemyMobileSessionRepository(uow.session)

            identity_session = await identity_session_repo.get_by_id(session_id)
            now = datetime.now(timezone.utc)
            if identity_session is None or not identity_session.is_valid(now):
                raise AuthenticationError("MOBILE_REFRESH_TOKEN_INVALID", "Sessão associada não está mais ativa.")

            new_expires_at = now + timedelta(minutes=SESSION_TTL_MINUTES)
            identity_session.extend(new_expires_at)
            await identity_session_repo.add(identity_session)

            claims_out = {"tenant_id": str(tenant_id), "session_id": str(session_id)}
            access_token = self._token_service.issue_access_token(subject=str(user_id), claims=claims_out)
            new_refresh_token = self._token_service.issue_access_token(
                subject=str(user_id), claims={**claims_out, "purpose": "refresh"}
            )

            mobile_session = await mobile_session_repo.get_by_id(session_id)
            if mobile_session is not None:
                mobile_session.data_hora_expiracao_prevista = new_expires_at
                mobile_session.token_acesso_hash = hash_token(access_token)
                await mobile_session_repo.add(mobile_session)

            await uow.commit()

        return TokenPairDTO(
            access_token=access_token, refresh_token=new_refresh_token,
            expires_in=self._settings.jwt_access_token_expire_minutes * 60,
        )
