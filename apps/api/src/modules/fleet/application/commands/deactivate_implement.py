from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import DomainError, NotFoundError
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_implement_repository import (
    SqlAlchemyImplementRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class DeactivateImplementCommand(Command):
    actor: AuthenticatedActor
    implement_id: uuid.UUID


class DeactivateImplementHandler(CommandHandler[DeactivateImplementCommand, None]):
    """`FLEET_IMPLEMENT_IN_COMPOSITION` (422) implementado de verdade — diferente de outras
    checagens deste lote adiadas por dependência ausente, esta só depende de
    `composicoes_veiculares_implementos`, que existe nesta mesma migration
    (`IMPLEMENT_IMPLEMENTATION.md`)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: DeactivateImplementCommand) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyImplementRepository(uow.session)

            implement = await repo.get_by_id(command.implement_id)
            if implement is None:
                raise NotFoundError("FLEET_IMPLEMENT_NOT_FOUND", "Implemento não encontrado.")

            if await repo.exists_in_active_composition(command.implement_id):
                raise DomainError(
                    "FLEET_IMPLEMENT_IN_COMPOSITION",
                    "Implemento faz parte de uma Composição Veicular vigente — encerre a composição primeiro.",
                )

            implement.soft_delete(now=datetime.now(timezone.utc))
            await repo.add(implement)

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="implementos",
                entidade_id=implement.id,
                acao="EXCLUSAO_LOGICA",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )

            await uow.commit()
