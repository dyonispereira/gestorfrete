from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError, ValidationError
from modules.fleet.application.dtos.vehicle_composition_dto import VehicleCompositionDTO
from modules.fleet.domain.entities.vehicle_composition import VehicleComposition
from modules.fleet.domain.value_objects.combination_type import CombinationType
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_implement_repository import (
    SqlAlchemyImplementRepository,
)
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_composition_repository import (
    SqlAlchemyVehicleCompositionRepository,
)
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_repository import (
    SqlAlchemyVehicleRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateVehicleCompositionCommand(Command):
    actor: AuthenticatedActor
    tractor_unit_id: uuid.UUID
    combination_type: CombinationType
    total_axles: int
    implements: list[tuple[uuid.UUID, int]]


class CreateVehicleCompositionHandler(CommandHandler[CreateVehicleCompositionCommand, VehicleCompositionDTO]):
    """D248 — se já existe uma composição vigente para o mesmo veículo, esta chamada fecha a
    anterior automaticamente antes de inserir a nova, na mesma transação. Nunca duas chamadas
    separadas (`COMPOSITION_IMPLEMENTATION.md`)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateVehicleCompositionCommand) -> VehicleCompositionDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            vehicle_repo = SqlAlchemyVehicleRepository(uow.session)
            implement_repo = SqlAlchemyImplementRepository(uow.session)
            composition_repo = SqlAlchemyVehicleCompositionRepository(uow.session)

            if await vehicle_repo.get_by_id(command.tractor_unit_id) is None:
                raise NotFoundError("FLEET_VEHICLE_NOT_FOUND", "Veículo Tracionador não encontrado.")

            for implement_id, _ in command.implements:
                if await implement_repo.get_by_id(implement_id) is None:
                    raise ValidationError("FLEET_UNKNOWN_IMPLEMENT_ID", f"Implemento inexistente: {implement_id}.")

            now = datetime.now(timezone.utc)

            current = await composition_repo.get_current_for_vehicle(command.tractor_unit_id)
            if current is not None:
                current.end_validity(ended_by=command.actor.user_id, now=now)
                await composition_repo.add(current)

            composition = VehicleComposition.create(
                veiculo_tracionador_id=command.tractor_unit_id,
                tipo_combinacao=command.combination_type,
                eixos_total=command.total_axles,
                implementos=command.implements,
                alterado_por=command.actor.user_id,
                now=now,
            )
            await composition_repo.add(composition)

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="composicoes_veiculares",
                entidade_id=composition.id,
                acao="CRIACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={
                    "veiculo_tracionador_id": str(composition.veiculo_tracionador_id),
                    "tipo_combinacao": composition.tipo_combinacao.value,
                },
                motivo="Composição anterior encerrada automaticamente (D248)." if current is not None else None,
            )

            await uow.commit()

        return VehicleCompositionDTO.from_entity(composition)
