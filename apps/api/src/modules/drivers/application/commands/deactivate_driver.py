from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.drivers.infrastructure.persistence.repositories.sqlalchemy_driver_repository import (
    SqlAlchemyDriverRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class DeactivateDriverCommand(Command):
    actor: AuthenticatedActor
    driver_id: uuid.UUID


class DeactivateDriverHandler(CommandHandler[DeactivateDriverCommand, None]):
    """`DRIVERS_DRIVER_HAS_ACTIVE_TRIP` (422) não é checado aqui — depende de
    `alocacoes_recurso_viagem`/`freight`, ainda não implementado. Soft delete incondicional por
    enquanto (`DRIVER_IMPLEMENTATION.md`)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: DeactivateDriverCommand) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyDriverRepository(uow.session)

            driver = await repo.get_by_id(command.driver_id)
            if driver is None:
                raise NotFoundError("DRIVERS_DRIVER_NOT_FOUND", "Motorista não encontrado.")

            driver.deactivate(deactivated_by=command.actor.user_id, now=datetime.now(timezone.utc))
            await repo.add(driver)

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="motoristas",
                entidade_id=driver.id,
                acao="EXCLUSAO_LOGICA",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )

            await uow.commit()
