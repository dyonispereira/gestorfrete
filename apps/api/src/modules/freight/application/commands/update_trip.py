from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.freight.application.dtos.trip_dto import TripDTO
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateTripCommand(Command):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    data_programada: date | None
    janela_programada: datetime | None


class UpdateTripHandler(CommandHandler[UpdateTripCommand, TripDTO]):
    """D233/D237 — só `data_programada`/`janela_programada`. `status`/`references`/`snapshots`/
    `financials` nunca aceitos aqui (`014-trips.md`)."""

    async def handle(self, command: UpdateTripCommand) -> TripDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyTripRepository(uow.session)
            trip = await repo.get_by_id(command.trip_id)
            if trip is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")

            trip.update(
                data_programada=command.data_programada,
                janela_programada=command.janela_programada,
                updated_by=command.actor.user_id,
                now=datetime.now(timezone.utc),
            )
            await repo.add(trip)
            await uow.commit()

        return TripDTO.from_entity(trip)
