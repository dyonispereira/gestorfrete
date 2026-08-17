from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.tracking.application.queries.list_location_origins import (
    ListLocationOriginsHandler,
    ListLocationOriginsQuery,
)
from modules.tracking.interfaces.schemas.location_origin_schemas import LocationOriginResponse
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/tracking", tags=["Location Origins"])


@router.get("/origins")
async def list_origins(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    actor: AuthenticatedActor = Depends(require_permission("tracking.position.view")),
) -> dict[str, Any]:
    handler = ListLocationOriginsHandler(get_session_factory())
    result = await handler.handle(ListLocationOriginsQuery(actor=actor, page=page, limit=limit))
    return {
        "data": [LocationOriginResponse.from_dto(o) for o in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }
