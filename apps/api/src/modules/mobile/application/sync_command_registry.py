from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from modules.freight.application.commands.accept_trip import AcceptTripCommand, AcceptTripHandler
from modules.freight.application.commands.create_occurrence import CreateOccurrenceCommand, CreateOccurrenceHandler
from modules.freight.application.commands.dispatch_trip import DispatchTripCommand, DispatchTripHandler
from modules.freight.application.commands.finish_trip import FinishTripCommand, FinishTripHandler
from modules.freight.application.commands.interromper_trip import InterromperTripCommand, InterromperTripHandler
from modules.freight.application.commands.retomar_trip import RetomarTripCommand, RetomarTripHandler
from modules.freight.domain.value_objects.occurrence_severity import OccurrenceSeverity
from modules.freight.domain.value_objects.occurrence_type import OccurrenceType
from modules.mobile.application.commands.register_mobile_pod import RegisterMobilePodCommand, RegisterMobilePodHandler
from modules.mobile.domain.value_objects.signatory_role import SignatoryRole
from shared_kernel.domain.actor import AuthenticatedActor

SyncCommandExecutor = Callable[[AuthenticatedActor, uuid.UUID, dict[str, Any]], Awaitable[Any]]


@dataclass(frozen=True)
class SyncCommandSpec:
    """D410 — `execute` chama sempre a MESMA classe `Handler` usada pelo endpoint direto
    equivalente (`/mobile/trips/{id}/commands/X`); `permission_codes` reaproveita exatamente os
    códigos já exigidos por esse endpoint (`055`/`057`/`058`) — nunca uma segunda autorização
    operacional (Auditoria #6)."""

    permission_codes: tuple[str, ...]
    execute: SyncCommandExecutor


async def _accept_trip(actor: AuthenticatedActor, target_id: uuid.UUID, payload: dict[str, Any]) -> Any:
    return await AcceptTripHandler().handle(AcceptTripCommand(actor=actor, trip_id=target_id))


async def _start_trip(actor: AuthenticatedActor, target_id: uuid.UUID, payload: dict[str, Any]) -> Any:
    return await DispatchTripHandler().handle(
        DispatchTripCommand(actor=actor, trip_id=target_id, origin="app_motorista")
    )


async def _interromper_trip(actor: AuthenticatedActor, target_id: uuid.UUID, payload: dict[str, Any]) -> Any:
    return await InterromperTripHandler().handle(
        InterromperTripCommand(actor=actor, trip_id=target_id, notes=str(payload.get("notes", "")))
    )


async def _retomar_trip(actor: AuthenticatedActor, target_id: uuid.UUID, payload: dict[str, Any]) -> Any:
    return await RetomarTripHandler().handle(RetomarTripCommand(actor=actor, trip_id=target_id))


async def _finish_trip(actor: AuthenticatedActor, target_id: uuid.UUID, payload: dict[str, Any]) -> Any:
    return await FinishTripHandler().handle(FinishTripCommand(actor=actor, trip_id=target_id))


async def _register_occurrence(actor: AuthenticatedActor, target_id: uuid.UUID, payload: dict[str, Any]) -> Any:
    occurred_at_raw = payload.get("occurred_at")
    occurred_at = datetime.fromisoformat(occurred_at_raw) if occurred_at_raw else datetime.now(timezone.utc)
    severity_raw = payload.get("severity")
    return await CreateOccurrenceHandler().handle(
        CreateOccurrenceCommand(
            actor=actor, trip_id=target_id, tipo=OccurrenceType(payload["type"]), descricao=payload["description"],
            gravidade=OccurrenceSeverity(severity_raw) if severity_raw else None, occurred_at=occurred_at,
        )
    )


async def _register_pod(actor: AuthenticatedActor, target_id: uuid.UUID, payload: dict[str, Any]) -> Any:
    return await RegisterMobilePodHandler().handle(
        RegisterMobilePodCommand(
            actor=actor, trip_id=uuid.UUID(str(payload["trip_id"])), delivery_id=target_id,
            photo_file_id=uuid.UUID(str(payload["photo_file_id"])),
            signature_file_id=uuid.UUID(str(payload["signature_file_id"])),
            signatory_role=SignatoryRole(payload["signatory_role"]), signatory_name=payload.get("signatory_name"),
        )
    )


SYNC_COMMAND_HANDLERS: dict[str, SyncCommandSpec] = {
    "ACCEPT_TRIP": SyncCommandSpec(("freight.trip.edit",), _accept_trip),
    "START_TRIP": SyncCommandSpec(("freight.trip.start",), _start_trip),
    "INTERROMPER_TRIP": SyncCommandSpec(("freight.trip.edit",), _interromper_trip),
    "RETOMAR_TRIP": SyncCommandSpec(("freight.trip.edit",), _retomar_trip),
    "FINISH_TRIP": SyncCommandSpec(("freight.trip.finish",), _finish_trip),
    "REGISTER_OCCURRENCE": SyncCommandSpec(("freight.occurrence.create",), _register_occurrence),
    # D429 (Backend Freeze) — `REGISTER_DELIVERY` removido: `060-driver-sync.md` nunca listou
    # criação de Entrega entre as capacidades offline permitidas ao Motorista (mesmo achado que
    # eliminou `POST /mobile/trips/{id}/deliveries`, D410 despachava para o mesmo Handler).
    "REGISTER_POD": SyncCommandSpec(("freight.pod.create", "freight.pod.attach"), _register_pod),
}
