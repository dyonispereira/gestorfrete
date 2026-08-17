from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError
from modules.financial.application.dtos.cost_center_dto import CostCenterDTO
from modules.financial.domain.entities.cost_center import CostCenter
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_cost_center_repository import (
    SqlAlchemyCostCenterRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor
from shared_kernel.domain.audit_metadata import AuditMetadata


@dataclass(frozen=True)
class CreateCostCenterCommand(Command):
    actor: AuthenticatedActor
    codigo_contabil: str
    nome: str
    filial_id: uuid.UUID | None


class CreateCostCenterHandler(CommandHandler[CreateCostCenterCommand, CostCenterDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateCostCenterCommand) -> CostCenterDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyCostCenterRepository(uow.session)

            if await repo.exists_with_codigo_contabil(command.codigo_contabil):
                raise ConflictError(
                    "FINANCIAL_COST_CENTER_CODE_ALREADY_EXISTS",
                    "Já existe um Centro de Custo com este código contábil neste tenant.",
                )

            now = datetime.now(timezone.utc)
            cost_center = CostCenter.create(
                codigo=str(uuid.uuid4())[:8],
                codigo_contabil=command.codigo_contabil,
                nome=command.nome,
                filial_id=command.filial_id,
                audit=AuditMetadata(
                    created_at=now, created_by=command.actor.user_id, updated_at=now, updated_by=command.actor.user_id
                ),
            )
            await repo.add(cost_center)

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="centros_custo",
                entidade_id=cost_center.id,
                acao="CRIACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"nome": cost_center.nome, "codigo_contabil": cost_center.codigo_contabil},
            )

            await uow.commit()

        return CostCenterDTO.from_entity(cost_center)
