from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import DomainError
from modules.fleet.application.dtos.odometer_reading_dto import OdometerReadingDTO
from modules.fleet.domain.entities.odometer_reading import OdometerReading
from modules.fleet.domain.value_objects.odometer_origin import OdometerOrigin
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_odometer_reading_repository import (
    SqlAlchemyOdometerReadingRepository,
)


class TripOdometerRecorder:
    """V1 Operational Hardening, Parte 2 — a única forma de `freight` gravar as leituras de
    fronteira de uma Viagem (`DESPACHO_VIAGEM`/`ENCERRAMENTO_VIAGEM`) em `leituras_hodometro`
    (`fleet`, D034 — dono único do hodômetro). Mesmo espírito não-HTTP de
    `VehicleAvailabilityProjector`: chamado por `DispatchTripHandler`/`FinishTripHandler` depois que
    a própria transação da Viagem já commitou.

    Idempotente por construção: `get_for_trip` + `add` dentro da mesma transação — reprocessar o
    mesmo comando (retry) encontra a leitura já existente e a devolve sem criar uma segunda linha
    nem violar "hodômetro nunca decresce" contra si mesma. Reusa `get_latest_for_vehicle` (mesmo
    invariante de `RegisterOdometerReadingHandler`, D365) em vez de duplicar a regra (D033/D034)."""

    async def record_departure(
        self, *, vehicle_id: uuid.UUID, trip_id: uuid.UUID, value_km: Decimal, now: datetime
    ) -> OdometerReadingDTO:
        return await self._record(
            vehicle_id=vehicle_id, trip_id=trip_id, value_km=value_km, origem=OdometerOrigin.DESPACHO_VIAGEM, now=now,
        )

    async def record_arrival(
        self, *, vehicle_id: uuid.UUID, trip_id: uuid.UUID, value_km: Decimal, now: datetime
    ) -> OdometerReadingDTO:
        return await self._record(
            vehicle_id=vehicle_id, trip_id=trip_id, value_km=value_km, origem=OdometerOrigin.ENCERRAMENTO_VIAGEM,
            now=now,
        )

    async def get_km_rodado(self, *, trip_id: uuid.UUID) -> Decimal | None:
        """`km_rodado = leitura_encerramento.valor_km - leitura_despacho.valor_km` — `None` quando
        a Viagem não tem as duas leituras de fronteira (nunca estimado)."""

        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyOdometerReadingRepository(uow.session)
            departure = await repo.get_for_trip(trip_id, OdometerOrigin.DESPACHO_VIAGEM)
            arrival = await repo.get_for_trip(trip_id, OdometerOrigin.ENCERRAMENTO_VIAGEM)
        if departure is None or arrival is None:
            return None
        return arrival.valor_km - departure.valor_km

    async def _record(
        self, *, vehicle_id: uuid.UUID, trip_id: uuid.UUID, value_km: Decimal, origem: OdometerOrigin, now: datetime
    ) -> OdometerReadingDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyOdometerReadingRepository(uow.session)

            existing = await repo.get_for_trip(trip_id, origem)
            if existing is not None:
                return OdometerReadingDTO.from_entity(existing)

            latest = await repo.get_latest_for_vehicle(vehicle_id)
            if latest is not None and value_km < latest.valor_km:
                raise DomainError(
                    "FLEET_ODOMETER_READING_LOWER_THAN_LAST",
                    f"Leitura ({value_km}km) menor que a última registrada ({latest.valor_km}km) para este veículo.",
                )

            reading = OdometerReading.create(
                veiculo_tracionador_id=vehicle_id, valor_km=value_km, origem=origem, viagem_id=trip_id, now=now,
            )
            await repo.add(reading)
            await uow.commit()

        return OdometerReadingDTO.from_entity(reading)
