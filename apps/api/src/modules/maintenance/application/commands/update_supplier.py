from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.maintenance.application.dtos.supplier_dto import SupplierDTO
from modules.maintenance.domain.value_objects.supplier_category import SupplierCategory
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_supplier_repository import (
    SqlAlchemySupplierRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateSupplierCommand(Command):
    actor: AuthenticatedActor
    supplier_id: uuid.UUID
    razao_social: str | None
    telefone: str | None
    category: SupplierCategory | None


class UpdateSupplierHandler(CommandHandler[UpdateSupplierCommand, SupplierDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: UpdateSupplierCommand) -> SupplierDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemySupplierRepository(uow.session)

            supplier = await repo.get_by_id(command.supplier_id)
            if supplier is None:
                raise NotFoundError("MAINTENANCE_SUPPLIER_NOT_FOUND", "Fornecedor não encontrado.")

            supplier.update(
                razao_social=command.razao_social,
                telefone=command.telefone,
                category=command.category,
                updated_by=command.actor.user_id,
                now=datetime.now(timezone.utc),
            )
            await repo.add(supplier)

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="fornecedores",
                entidade_id=supplier.id,
                acao="ALTERACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )

            await uow.commit()

        return SupplierDTO.from_entity(supplier)
