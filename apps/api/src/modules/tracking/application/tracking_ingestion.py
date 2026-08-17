from __future__ import annotations

import uuid
from datetime import datetime, timezone

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from modules.tracking.domain.entities.heartbeat import Heartbeat
from modules.tracking.domain.entities.telemetry_reading import TelemetryReading
from modules.tracking.domain.entities.tracking_event import TrackingEvent
from modules.tracking.domain.entities.vehicle_position import VehiclePosition
from modules.tracking.domain.value_objects.geo_point import GeoPoint
from modules.tracking.domain.value_objects.sensor_type import SensorType
from modules.tracking.domain.value_objects.tracking_event_severity import TrackingEventSeverity
from modules.tracking.domain.value_objects.tracking_event_type import TrackingEventType
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_geofence_repository import (
    SqlAlchemyGeofenceRepository,
)
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_heartbeat_repository import (
    SqlAlchemyHeartbeatRepository,
)
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_speed_limit_config_repository import (
    SqlAlchemySpeedLimitConfigRepository,
)
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_telemetry_reading_repository import (
    SqlAlchemyTelemetryReadingRepository,
)
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_tracking_event_repository import (
    SqlAlchemyTrackingEventRepository,
)
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_vehicle_position_repository import (
    SqlAlchemyVehiclePositionRepository,
)


class TrackingIngestion:
    """D402 — como dado bruto entra no sistema nesta lote: `048`-`051` são somente leitura (D286),
    nenhum contrato de ingestão pública foi definido ainda. Mesma forma de `TripInternalTransitions`
    (D376)/`FiscalInternalTransitions` (D397) — nunca alcançável por HTTP, só chamado diretamente
    (testes hoje, pipeline real de integração quando existir).

    D116/D285 — nunca importa nada de `modules.freight` (mecanizado também pelo contrato
    `import-linter` D405). Só roda as duas detecções com regra concreta e congelada em algum
    documento: Geofence (`list_active_ids_containing`, PostGIS) e Excesso de Velocidade
    (`SpeedLimitConfig`). Parada/Desvio de Rota deliberadamente não têm gatilho automático — ver
    `docs/backend/tracking/GEOFENCE_AND_EVENTS_IMPLEMENTATION.md`.

    Severidade de evento derivado é uma constante por `tipo` (`INFORMACAO` para geofence,
    `ATENCAO` para excesso de velocidade) — nenhum documento congelado define uma escala por
    magnitude de desvio, então nenhuma é inventada aqui (D127 só exige que o campo nunca seja nulo).
    """

    async def ingest_position(
        self,
        *,
        vehicle_id: uuid.UUID,
        equipment_id: uuid.UUID,
        latitude: float,
        longitude: float,
        origin_id: uuid.UUID,
        precision_meters: float | None = None,
        satellite_count: int | None = None,
        hdop: float | None = None,
        confidence_level: float | None = None,
        captured_at: datetime,
        received_at: datetime | None = None,
        processed_at: datetime | None = None,
    ) -> VehiclePosition:
        received_at = received_at or captured_at
        processed_at = processed_at or datetime.now(timezone.utc)
        new_point = GeoPoint(latitude=latitude, longitude=longitude)

        async with SQLAlchemyUnitOfWork() as uow:
            position_repo = SqlAlchemyVehiclePositionRepository(uow.session)
            geofence_repo = SqlAlchemyGeofenceRepository(uow.session)
            event_repo = SqlAlchemyTrackingEventRepository(uow.session)

            previous = await position_repo.get_latest_for_vehicle(vehicle_id)

            position = VehiclePosition.create(
                veiculo_tracionador_id=vehicle_id, equipamento_rastreamento_id=equipment_id,
                localizacao=new_point, origem_localizacao_id=origin_id, precisao_metros=precision_meters,
                numero_satelites=satellite_count, hdop=hdop, nivel_confianca=confidence_level,
                capturado_em=captured_at, recebido_em=received_at, processado_em=processed_at,
            )
            await position_repo.add(position)

            previously_contained = (
                set(await geofence_repo.list_active_ids_containing(previous.localizacao))
                if previous is not None else set()
            )
            currently_contained = set(await geofence_repo.list_active_ids_containing(new_point))

            for geofence_id in currently_contained - previously_contained:
                await event_repo.add(
                    TrackingEvent.create(
                        veiculo_tracionador_id=vehicle_id, tipo=TrackingEventType.ENTROU_GEOFENCE,
                        severidade=TrackingEventSeverity.INFORMACAO, posicao_veiculo_id=position.id,
                        cerca_eletronica_id=geofence_id, data_hora=captured_at,
                    )
                )
            for geofence_id in previously_contained - currently_contained:
                await event_repo.add(
                    TrackingEvent.create(
                        veiculo_tracionador_id=vehicle_id, tipo=TrackingEventType.SAIU_GEOFENCE,
                        severidade=TrackingEventSeverity.INFORMACAO, posicao_veiculo_id=position.id,
                        cerca_eletronica_id=geofence_id, data_hora=captured_at,
                    )
                )

            await uow.commit()

        return position

    async def ingest_telemetry(
        self,
        *,
        vehicle_id: uuid.UUID,
        equipment_id: uuid.UUID,
        sensor_type: SensorType,
        value: float,
        unit: str,
        position_id: uuid.UUID | None = None,
        vehicle_category_id: uuid.UUID | None = None,
        captured_at: datetime,
        received_at: datetime | None = None,
        processed_at: datetime | None = None,
    ) -> TelemetryReading:
        received_at = received_at or captured_at
        processed_at = processed_at or datetime.now(timezone.utc)

        async with SQLAlchemyUnitOfWork() as uow:
            telemetry_repo = SqlAlchemyTelemetryReadingRepository(uow.session)
            reading = TelemetryReading.create(
                veiculo_tracionador_id=vehicle_id, equipamento_rastreamento_id=equipment_id,
                posicao_veiculo_id=position_id, tipo_sensor=sensor_type, valor=value, unidade=unit,
                capturado_em=captured_at, recebido_em=received_at, processado_em=processed_at,
            )
            await telemetry_repo.add(reading)

            if sensor_type == SensorType.VELOCIDADE:
                speed_limit_repo = SqlAlchemySpeedLimitConfigRepository(uow.session)
                applicable = await speed_limit_repo.get_applicable(vehicle_category_id)
                if applicable is not None and value > applicable.limite_kmh:
                    event_repo = SqlAlchemyTrackingEventRepository(uow.session)
                    # `eventos_rastreamento` não tem `leitura_telemetria_id` — limitação real da DDL
                    # congelada (ver GEOFENCE_AND_EVENTS_IMPLEMENTATION.md), `posicao_veiculo_id`
                    # fica None quando a detecção nasce de Telemetria, não de Posição.
                    await event_repo.add(
                        TrackingEvent.create(
                            veiculo_tracionador_id=vehicle_id, tipo=TrackingEventType.EXCESSO_DE_VELOCIDADE,
                            severidade=TrackingEventSeverity.ATENCAO,
                            configuracao_limite_velocidade_id=applicable.id, valor_detectado=value,
                            data_hora=captured_at,
                        )
                    )

            await uow.commit()

        return reading

    async def ingest_heartbeat(
        self,
        *,
        equipment_id: uuid.UUID,
        protocol: str | None = None,
        captured_at: datetime | None = None,
        received_at: datetime | None = None,
        processed_at: datetime | None = None,
    ) -> Heartbeat | None:
        received_at = received_at or datetime.now(timezone.utc)
        processed_at = processed_at or datetime.now(timezone.utc)

        async with SQLAlchemyUnitOfWork() as uow:
            heartbeat_repo = SqlAlchemyHeartbeatRepository(uow.session)
            if protocol is not None and await heartbeat_repo.exists_with_protocol(equipment_id, protocol):
                # D111 — reenviar o mesmo pacote (mesmo protocolo) nunca duplica.
                return None

            heartbeat = Heartbeat.create(
                equipamento_rastreamento_id=equipment_id, protocolo_externo=protocol, capturado_em=captured_at,
                recebido_em=received_at, processado_em=processed_at,
            )
            await heartbeat_repo.add(heartbeat)
            await uow.commit()

        return heartbeat
