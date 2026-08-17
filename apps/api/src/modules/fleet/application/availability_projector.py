from __future__ import annotations

import uuid
from datetime import datetime

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from modules.fleet.domain.value_objects.availability_status import AvailabilityStatus
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_availability_repository import (
    SqlAlchemyVehicleAvailabilityRepository,
)


class VehicleAvailabilityProjector:
    """A **única** forma de escrever em `disponibilidade_veiculo` em todo o código (D247,
    `AVAILABILITY_IMPLEMENTATION.md`) — não é um `CommandHandler`, não é acionável por HTTP, não
    existe schema de request para nenhum destes métodos. `freight`/`maintenance` (Lote 5+/6+)
    ainda não publicam os eventos reais (`ViagemDespachada`, `OrdemServicoAberta`, etc.) — quando
    existirem, o consumidor real (`EventBus.subscribe(...)`) só precisa chamar estes mesmos
    métodos com os dados do evento, nenhuma mudança aqui.
    """

    async def apply_trip_dispatched(
        self, *, vehicle_id: uuid.UUID, driver_id: uuid.UUID, implement_id: uuid.UUID | None, at: datetime
    ) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyVehicleAvailabilityRepository(uow.session)
            await repo.apply(
                veiculo_tracionador_id=vehicle_id, status=AvailabilityStatus.EM_VIAGEM,
                motorista_atual_id=driver_id, implemento_atual_id=implement_id, now=at,
            )
            await uow.commit()

    async def apply_trip_ended(self, *, vehicle_id: uuid.UUID, at: datetime) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyVehicleAvailabilityRepository(uow.session)
            await repo.apply(
                veiculo_tracionador_id=vehicle_id, status=AvailabilityStatus.DISPONIVEL,
                motorista_atual_id=None, implemento_atual_id=None, now=at,
            )
            await uow.commit()

    async def apply_service_order_opened(self, *, vehicle_id: uuid.UUID, at: datetime) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyVehicleAvailabilityRepository(uow.session)
            await repo.apply(
                veiculo_tracionador_id=vehicle_id, status=AvailabilityStatus.EM_MANUTENCAO,
                motorista_atual_id=None, implemento_atual_id=None, now=at,
            )
            await uow.commit()

    async def apply_service_order_closed(self, *, vehicle_id: uuid.UUID, at: datetime) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyVehicleAvailabilityRepository(uow.session)
            await repo.apply(
                veiculo_tracionador_id=vehicle_id, status=AvailabilityStatus.DISPONIVEL,
                motorista_atual_id=None, implemento_atual_id=None, now=at,
            )
            await uow.commit()
