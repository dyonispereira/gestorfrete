from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from core.audit.audit_logger import AuditLogger
from core.config.settings import Settings
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import AuthenticationError, AuthorizationError
from core.security.jwt_token_service import JWTTokenService
from core.security.password_hasher import BcryptPasswordHasher
from modules.identity_access.application.dtos.auth_dto import LoginResultDTO
from modules.identity_access.application.dtos.user_dto import UserDTO
from modules.identity_access.domain.entities.session import Session
from modules.identity_access.domain.value_objects.enums import UserStatus
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_session_repository import (
    SqlAlchemySessionRepository,
)
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from shared_kernel.application.command import Command, CommandHandler

SESSION_TTL_MINUTES = 60 * 8
"""Janela de validade da Sessão (`sessoes_acesso`) — independente do TTL do access_token JWT em si
(`Settings.jwt_access_token_expire_minutes`, tipicamente bem menor); `refresh` estende esta janela
sem criar uma nova Sessão (`SESSION_IMPLEMENTATION.md`)."""


@dataclass(frozen=True)
class LoginCommand(Command):
    email: str
    password: str


class LoginHandler(CommandHandler[LoginCommand, LoginResultDTO]):
    def __init__(self, settings: Settings, audit_logger: AuditLogger | None = None) -> None:
        self._settings = settings
        self._token_service = JWTTokenService(settings)
        self._hasher = BcryptPasswordHasher()
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: LoginCommand) -> LoginResultDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            user_repo = SqlAlchemyUserRepository(uow.session)
            session_repo = SqlAlchemySessionRepository(uow.session)

            found = await user_repo.get_by_email(command.email)
            # D-ERROR_MODEL: e-mail inexistente e senha errada retornam exatamente o mesmo erro —
            # nunca revelar qual dos dois faltou.
            if found is None:
                raise AuthenticationError("IDENTITY_INVALID_CREDENTIALS", "Credenciais inválidas.")
            user, tenant_id = found

            if not self._hasher.verify(command.password, user.senha_hash):
                raise AuthenticationError("IDENTITY_INVALID_CREDENTIALS", "Credenciais inválidas.")

            if user.status == UserStatus.BLOQUEADO:
                raise AuthorizationError("IDENTITY_USER_BLOCKED", "Usuário bloqueado.")
            if user.status == UserStatus.INATIVO:
                raise AuthorizationError("IDENTITY_USER_INACTIVE", "Usuário inativo.")

            now = datetime.now(timezone.utc)
            session = Session.start(
                user_id=user.id, started_at=now, expires_at=now + timedelta(minutes=SESSION_TTL_MINUTES)
            )
            await session_repo.add(session)

            access_token, refresh_token, expires_in = self._issue_tokens(user.id, tenant_id, session.id)

            await self._audit.record(
                uow.session,
                tenant_id=tenant_id,
                entidade_tipo="sessoes_acesso",
                entidade_id=session.id,
                acao="LOGIN",
                ator_id=user.id,
                ator_nome_snapshot=user.nome,
            )

            await uow.commit()

        return LoginResultDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            user=UserDTO.from_entity(user),
        )

    def _issue_tokens(
        self, user_id: uuid.UUID, tenant_id: uuid.UUID, session_id: uuid.UUID
    ) -> tuple[str, str, int]:
        claims = {"tenant_id": str(tenant_id), "session_id": str(session_id)}
        access_token = self._token_service.issue_access_token(subject=str(user_id), claims=claims)
        refresh_token = self._token_service.issue_access_token(
            subject=str(user_id), claims={**claims, "purpose": "refresh"}
        )
        expires_in = self._settings.jwt_access_token_expire_minutes * 60
        return access_token, refresh_token, expires_in
