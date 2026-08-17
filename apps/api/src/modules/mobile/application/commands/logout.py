from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from modules.identity_access.domain.value_objects.enums import SessionEndedReason, SessionStatus
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_session_repository import (
    SqlAlchemySessionRepository,
)
from modules.mobile.domain.value_objects.mobile_session_end_reason import MobileSessionEndReason
from modules.mobile.domain.value_objects.mobile_session_status import MobileSessionStatus
from modules.mobile.infrastructure.persistence.repositories.sqlalchemy_mobile_session_repository import (
    SqlAlchemyMobileSessionRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class MobileLogoutCommand(Command):
    actor: AuthenticatedActor


class MobileLogoutHandler(CommandHandler[MobileLogoutCommand, None]):
    """D407 — encerra a `SessaoMobile` **e** a `Sessão` (`sessoes_acesso`) subjacente juntas, para
    que `is_session_valid` reflita a revogação imediatamente (Auditoria #4: nunca toca
    `dispositivos_mobile`)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: MobileLogoutCommand) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            mobile_session_repo = SqlAlchemyMobileSessionRepository(uow.session)
            identity_session_repo = SqlAlchemySessionRepository(uow.session)
            now = datetime.now(timezone.utc)

            mobile_session = await mobile_session_repo.get_by_id(command.actor.session_id)
            if mobile_session is not None and mobile_session.status == MobileSessionStatus.ATIVA:
                mobile_session.end(reason=MobileSessionEndReason.LOGOUT, now=now)
                await mobile_session_repo.add(mobile_session)

            identity_session = await identity_session_repo.get_by_id(command.actor.session_id)
            if identity_session is not None and identity_session.status == SessionStatus.ATIVA:
                identity_session.end(SessionEndedReason.LOGOUT)
                await identity_session_repo.add(identity_session)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="sessoes_mobile",
                entidade_id=command.actor.session_id, acao="LOGOUT", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )
            await uow.commit()
