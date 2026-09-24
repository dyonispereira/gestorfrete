from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError
from modules.fleet.application.dtos.vehicle_category_dto import VehicleCategoryDTO
from modules.fleet.domain.entities.vehicle_category import VehicleCategory
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_category_repository import (
    SqlAlchemyVehicleCategoryRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateVehicleCategoryCommand(Command):
    actor: AuthenticatedActor
    nome: str


class CreateVehicleCategoryHandler(CommandHandler[CreateVehicleCategoryCommand, VehicleCategoryDTO]):
    """`POST /categorias-veiculo` — V1 Operational Hardening, Parte 5 (D363). `codigo` gerado
    internamente, mesmo padrão de `CreateCostCenterHandler`."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateVehicleCategoryCommand) -> VehicleCategoryDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyVehicleCategoryRepository(uow.session)

            if await repo.exists_with_nome(command.nome):
                raise ConflictError(
                    "FLEET_VEHICLE_CATEGORY_NAME_ALREADY_EXISTS", "Já existe uma Categoria de Veículo com este nome."
                )

            now = datetime.now(timezone.utc)
            category = VehicleCategory.create(codigo=str(uuid.uuid4())[:8], nome=command.nome, now=now)
            await repo.add(category)

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="categorias_veiculo",
                entidade_id=category.id,
                acao="CRIACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"nome": category.nome},
            )

            await uow.commit()

        return VehicleCategoryDTO.from_entity(category)
