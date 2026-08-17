from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import AuthorizationError
from modules.freight.application.queries.get_trip import GetTripHandler, GetTripQuery
from shared_kernel.domain.actor import AuthenticatedActor


async def assert_owns_trip(
    session_factory: async_sessionmaker[AsyncSession], *, actor: AuthenticatedActor, driver_id: uuid.UUID,
    trip_id: uuid.UUID,
) -> None:
    """D295 — usado por toda query/comando mobile que opera sobre um sub-recurso de Viagem
    (Ocorrência/Entrega/Canhoto); `403`, nunca `404` (mesmo raciocínio de `GetOwnTripHandler`)."""

    dto = await GetTripHandler(session_factory).handle(GetTripQuery(actor=actor, trip_id=trip_id))
    if dto.motorista_id != driver_id:
        raise AuthorizationError("FREIGHT_TRIP_FORBIDDEN", "Viagem não pertence ao Motorista da sessão.")
