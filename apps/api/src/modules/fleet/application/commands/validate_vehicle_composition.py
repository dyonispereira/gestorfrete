from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import DomainError, NotFoundError
from modules.fleet.application.dtos.vehicle_composition_dto import VehicleCompositionDTO
from modules.fleet.domain.entities.vehicle_composition import VehicleComposition
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_composition_repository import (
    SqlAlchemyVehicleCompositionRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ValidateVehicleCompositionCommand(Command):
    actor: AuthenticatedActor
    composition_id: uuid.UUID


class ValidateVehicleCompositionHandler(CommandHandler[ValidateVehicleCompositionCommand, VehicleCompositionDTO]):
    """`POST /vehicle-compositions/{id}/commands/validate` — algoritmo CONTRAN real fora de
    escopo (D368); reusa a mesma faixa de eixos por tipo de combinação já checada em
    `POST /vehicle-compositions`."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: ValidateVehicleCompositionCommand) -> VehicleCompositionDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyVehicleCompositionRepository(uow.session)

            composition = await repo.get_by_id(command.composition_id)
            if composition is None:
                raise NotFoundError("FLEET_COMPOSITION_NOT_FOUND", "Composição Veicular não encontrada.")

            is_valid = True
            try:
                VehicleComposition.check_axles(composition.tipo_combinacao, composition.eixos_total)
            except DomainError:
                is_valid = False

            composition.validate(is_valid=is_valid, validated_by=command.actor.user_id)
            await repo.add(composition)

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="composicoes_veiculares",
                entidade_id=composition.id,
                acao="TRANSICAO_STATUS",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"status": composition.status.value},
            )

            await uow.commit()

        return VehicleCompositionDTO.from_entity(composition)
