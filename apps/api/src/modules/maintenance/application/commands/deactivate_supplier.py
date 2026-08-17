from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_supplier_repository import (
    SqlAlchemySupplierRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class DeactivateSupplierCommand(Command):
    actor: AuthenticatedActor
    supplier_id: uuid.UUID


class DeactivateSupplierHandler(CommandHandler[DeactivateSupplierCommand, None]):
    """`MAINTENANCE_SUPPLIER_HAS_OPEN_ORDERS` (422) não é checado aqui — depende de
    `ordens_servico`, ainda não implementado. Soft delete incondicional por enquanto
    (`SUPPLIER_IMPLEMENTATION.md`)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: DeactivateSupplierCommand) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemySupplierRepository(uow.session)

            supplier = await repo.get_by_id(command.supplier_id)
            if supplier is None:
                raise NotFoundError("MAINTENANCE_SUPPLIER_NOT_FOUND", "Fornecedor não encontrado.")

            supplier.deactivate(deactivated_by=command.actor.user_id, now=datetime.now(timezone.utc))
            await repo.add(supplier)

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="fornecedores",
                entidade_id=supplier.id,
                acao="EXCLUSAO_LOGICA",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )

            await uow.commit()
