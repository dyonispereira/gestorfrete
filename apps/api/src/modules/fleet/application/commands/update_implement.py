from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.fleet.application.dtos.implement_dto import ImplementDTO
from modules.fleet.domain.value_objects.body_type import BodyType
from modules.fleet.domain.value_objects.implement_availability import ImplementAvailability
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_implement_repository import (
    SqlAlchemyImplementRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateImplementCommand(Command):
    actor: AuthenticatedActor
    implement_id: uuid.UUID
    body_type: BodyType | None
    load_capacity: Decimal | None
    availability_status: ImplementAvailability | None


class UpdateImplementHandler(CommandHandler[UpdateImplementCommand, ImplementDTO]):
    async def handle(self, command: UpdateImplementCommand) -> ImplementDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyImplementRepository(uow.session)

            implement = await repo.get_by_id(command.implement_id)
            if implement is None:
                raise NotFoundError("FLEET_IMPLEMENT_NOT_FOUND", "Implemento não encontrado.")

            implement.update(
                tipo_carroceria=command.body_type,
                capacidade_carga=command.load_capacity,
                status_disponibilidade=command.availability_status,
                now=datetime.now(timezone.utc),
            )
            await repo.add(implement)
            await uow.commit()

        return ImplementDTO.from_entity(implement)
