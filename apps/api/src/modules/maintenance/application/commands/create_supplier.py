from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError
from modules.maintenance.application.dtos.supplier_dto import SupplierDTO
from modules.maintenance.domain.entities.supplier import Supplier
from modules.maintenance.domain.value_objects.supplier_category import SupplierCategory
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_supplier_repository import (
    SqlAlchemySupplierRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor
from shared_kernel.domain.audit_metadata import AuditMetadata


@dataclass(frozen=True)
class CreateSupplierCommand(Command):
    actor: AuthenticatedActor
    razao_social: str
    cnpj: str
    telefone: str | None
    category: SupplierCategory | None


class CreateSupplierHandler(CommandHandler[CreateSupplierCommand, SupplierDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateSupplierCommand) -> SupplierDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemySupplierRepository(uow.session)

            if await repo.exists_with_cnpj(command.cnpj):
                raise ConflictError(
                    "MAINTENANCE_SUPPLIER_CNPJ_ALREADY_EXISTS", "Já existe um Fornecedor com este CNPJ neste tenant."
                )

            now = datetime.now(timezone.utc)
            supplier = Supplier.create(
                codigo=str(uuid.uuid4())[:8],
                razao_social=command.razao_social,
                cnpj=command.cnpj,
                telefone=command.telefone,
                category=command.category,
                audit=AuditMetadata(
                    created_at=now, created_by=command.actor.user_id, updated_at=now, updated_by=command.actor.user_id
                ),
            )
            await repo.add(supplier)

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="fornecedores",
                entidade_id=supplier.id,
                acao="CRIACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"razao_social": supplier.razao_social, "cnpj": supplier.cnpj},
            )

            await uow.commit()

        return SupplierDTO.from_entity(supplier)
