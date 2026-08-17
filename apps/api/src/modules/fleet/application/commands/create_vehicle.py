from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, ValidationError
from modules.fleet.application.dtos.vehicle_dto import VehicleDTO
from modules.fleet.domain.entities.vehicle import Vehicle
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_category_repository import (
    SqlAlchemyVehicleCategoryRepository,
)
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_repository import (
    SqlAlchemyVehicleRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor
from shared_kernel.domain.audit_metadata import AuditMetadata


@dataclass(frozen=True)
class CreateVehicleCommand(Command):
    actor: AuthenticatedActor
    placa: str
    renavam: str
    fabricante: str
    modelo: str
    ano_fabricacao: int
    categoria_id: uuid.UUID
    filial_id: uuid.UUID | None


class CreateVehicleHandler(CommandHandler[CreateVehicleCommand, VehicleDTO]):
    """Nunca toca em `disponibilidade_veiculo` — só o projetor de eventos escreve lá
    (`AVAILABILITY_IMPLEMENTATION.md`, D247)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateVehicleCommand) -> VehicleDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyVehicleRepository(uow.session)
            category_repo = SqlAlchemyVehicleCategoryRepository(uow.session)

            if await category_repo.get_by_id(command.categoria_id) is None:
                raise ValidationError("FLEET_UNKNOWN_VEHICLE_CATEGORY_ID", "Categoria de Veículo inexistente.")
            if await repo.exists_with_placa(command.placa):
                raise ConflictError("FLEET_VEHICLE_PLATE_ALREADY_EXISTS", "Já existe um Veículo com esta placa neste tenant.")
            if await repo.exists_with_renavam(command.renavam):
                raise ConflictError(
                    "FLEET_VEHICLE_RENAVAM_ALREADY_EXISTS", "Já existe um Veículo com este RENAVAM neste tenant."
                )

            now = datetime.now(timezone.utc)
            vehicle = Vehicle.create(
                codigo=str(uuid.uuid4())[:8],
                placa=command.placa,
                renavam=command.renavam,
                fabricante=command.fabricante,
                modelo=command.modelo,
                ano_fabricacao=command.ano_fabricacao,
                categoria_veiculo_id=command.categoria_id,
                filial_id=command.filial_id,
                audit=AuditMetadata(
                    created_at=now, created_by=command.actor.user_id, updated_at=now, updated_by=command.actor.user_id
                ),
            )
            await repo.add(vehicle)

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="veiculos_tracionadores",
                entidade_id=vehicle.id,
                acao="CRIACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"placa": vehicle.placa, "renavam": vehicle.renavam},
            )

            await uow.commit()

        return VehicleDTO.from_entity(vehicle)
