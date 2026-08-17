from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, ValidationError
from modules.fleet.application.dtos.implement_dto import ImplementDTO
from modules.fleet.domain.entities.implement import Implement
from modules.fleet.domain.value_objects.body_type import BodyType
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_implement_repository import (
    SqlAlchemyImplementRepository,
)
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_category_repository import (
    SqlAlchemyVehicleCategoryRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateImplementCommand(Command):
    actor: AuthenticatedActor
    placa: str
    renavam: str
    body_type: BodyType
    category_id: uuid.UUID
    load_capacity: Decimal


class CreateImplementHandler(CommandHandler[CreateImplementCommand, ImplementDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateImplementCommand) -> ImplementDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyImplementRepository(uow.session)
            category_repo = SqlAlchemyVehicleCategoryRepository(uow.session)

            if await category_repo.get_by_id(command.category_id) is None:
                raise ValidationError("FLEET_UNKNOWN_VEHICLE_CATEGORY_ID", "Categoria de Veículo inexistente.")
            if await repo.exists_with_placa(command.placa):
                raise ConflictError(
                    "FLEET_IMPLEMENT_PLATE_ALREADY_EXISTS", "Já existe um Implemento com esta placa neste tenant."
                )

            now = datetime.now(timezone.utc)
            implement = Implement.create(
                codigo=str(uuid.uuid4())[:8],
                placa=command.placa,
                renavam=command.renavam,
                tipo_carroceria=command.body_type,
                categoria_veiculo_id=command.category_id,
                capacidade_carga=command.load_capacity,
                now=now,
            )
            await repo.add(implement)

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="implementos",
                entidade_id=implement.id,
                acao="CRIACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"placa": implement.placa},
            )

            await uow.commit()

        return ImplementDTO.from_entity(implement)
