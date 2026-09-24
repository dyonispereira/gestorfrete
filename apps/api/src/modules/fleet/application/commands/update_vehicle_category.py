from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError
from modules.fleet.application.dtos.vehicle_category_dto import VehicleCategoryDTO
from modules.fleet.domain.value_objects.vehicle_category_status import VehicleCategoryStatus
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_category_repository import (
    SqlAlchemyVehicleCategoryRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateVehicleCategoryCommand(Command):
    actor: AuthenticatedActor
    vehicle_category_id: uuid.UUID
    nome: str | None
    status: VehicleCategoryStatus | None


class UpdateVehicleCategoryHandler(CommandHandler[UpdateVehicleCategoryCommand, VehicleCategoryDTO]):
    """`PATCH /categorias-veiculo/{id}` — `status: INATIVA` é a única forma de "desativar", sem
    `DELETE` (`RBAC_MATRIX.md` não tem `fleet.vehicle_category.delete`, mesmo padrão de
    `UpdateCostCenterHandler`)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: UpdateVehicleCategoryCommand) -> VehicleCategoryDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyVehicleCategoryRepository(uow.session)

            category = await repo.get_by_id(command.vehicle_category_id)
            if category is None:
                raise NotFoundError("FLEET_VEHICLE_CATEGORY_NOT_FOUND", "Categoria de Veículo não encontrada.")

            if command.nome is not None and await repo.exists_with_nome(
                command.nome, excluding_id=category.id
            ):
                raise ConflictError(
                    "FLEET_VEHICLE_CATEGORY_NAME_ALREADY_EXISTS", "Já existe uma Categoria de Veículo com este nome."
                )

            category.update(nome=command.nome, status=command.status, now=datetime.now(timezone.utc))
            await repo.add(category)

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="categorias_veiculo",
                entidade_id=category.id,
                acao="ALTERACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )

            await uow.commit()

        return VehicleCategoryDTO.from_entity(category)
