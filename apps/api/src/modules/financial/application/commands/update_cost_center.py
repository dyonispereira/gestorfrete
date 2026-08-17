from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.financial.application.dtos.cost_center_dto import CostCenterDTO
from modules.financial.domain.value_objects.cost_center_status import CostCenterStatus
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_cost_center_repository import (
    SqlAlchemyCostCenterRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateCostCenterCommand(Command):
    actor: AuthenticatedActor
    cost_center_id: uuid.UUID
    nome: str | None
    filial_id: uuid.UUID | None
    status: CostCenterStatus | None


class UpdateCostCenterHandler(CommandHandler[UpdateCostCenterCommand, CostCenterDTO]):
    """`status: INATIVO` via `PATCH` é a única forma de "desativar" — não existe `DELETE`
    (`RBAC_MATRIX.md` não tem `financial.cost_center.delete`, `COST_CENTER_IMPLEMENTATION.md`)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: UpdateCostCenterCommand) -> CostCenterDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyCostCenterRepository(uow.session)

            cost_center = await repo.get_by_id(command.cost_center_id)
            if cost_center is None:
                raise NotFoundError("FINANCIAL_COST_CENTER_NOT_FOUND", "Centro de Custo não encontrado.")

            cost_center.update(
                nome=command.nome,
                filial_id=command.filial_id,
                status=command.status,
                updated_by=command.actor.user_id,
                now=datetime.now(timezone.utc),
            )
            await repo.add(cost_center)

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="centros_custo",
                entidade_id=cost_center.id,
                acao="ALTERACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )

            await uow.commit()

        return CostCenterDTO.from_entity(cost_center)
