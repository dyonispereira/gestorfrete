from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from core.database.session import get_session_factory
from core.exceptions.base import AuthorizationError
from interfaces.dependencies.auth import get_current_actor
from modules.freight.application.queries.get_trip_financials import (
    ACTUAL_PERMISSION,
    MARGIN_PERMISSION,
    PREDICTED_PERMISSION,
    GetTripFinancialsHandler,
    GetTripFinancialsQuery,
)
from modules.freight.interfaces.schemas.trip_financials_schemas import TripFinancialsViewResponse
from modules.identity_access.interfaces.dependencies.authorization import get_authorization_service
from modules.identity_access.application.authorization_service import AuthorizationService
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/viagens", tags=["Trip Financials"])

_FINANCIAL_VALUE_PERMISSIONS = frozenset({PREDICTED_PERMISSION, ACTUAL_PERMISSION, MARGIN_PERMISSION})


async def _require_trip_financials_access(
    actor: AuthenticatedActor = Depends(get_current_actor),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> tuple[AuthenticatedActor, frozenset[str]]:
    """D389 — este endpoint exige `freight.trip.view` **e** ao menos uma das três permissões de
    valor financeiro (D267-style); sem nenhuma das quatro, `403`. Com `freight.trip.view` mais
    algumas (não todas) das três, `200` com os grupos sem permissão mascarados como `null`
    (`get_trip_financials.py`), nunca um `403` parcial."""

    held = await authz.get_permission_codes(actor)
    if "freight.trip.view" not in held:
        raise AuthorizationError("IDENTITY_PERMISSION_DENIED", "Ação requer a permissão 'freight.trip.view'.")
    if not (held & _FINANCIAL_VALUE_PERMISSIONS):
        raise AuthorizationError(
            "IDENTITY_PERMISSION_DENIED",
            "Ação requer ao menos uma de: financial.trip_predicted_value.view, "
            "financial.trip_actual_value.view, financial.trip_margin.view.",
        )
    return actor, held


@router.get("/{trip_id}/financeiro", response_model=TripFinancialsViewResponse)
async def get_trip_financials(
    trip_id: uuid.UUID,
    actor_and_permissions: tuple[AuthenticatedActor, frozenset[str]] = Depends(_require_trip_financials_access),
) -> TripFinancialsViewResponse:
    actor, held_permissions = actor_and_permissions
    handler = GetTripFinancialsHandler(get_session_factory())
    dto = await handler.handle(GetTripFinancialsQuery(actor=actor, trip_id=trip_id, held_permissions=held_permissions))
    return TripFinancialsViewResponse.from_dto(dto)
