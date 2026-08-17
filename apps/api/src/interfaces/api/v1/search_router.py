from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from interfaces.api.v1.global_search import run_global_search
from interfaces.dependencies.auth import get_current_actor
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(tags=["Global Search"])


@router.get("/search")
async def global_search(
    q: str = Query(min_length=2),
    types: str | None = Query(default=None, description="Lista separada por vírgula, ex.: viagem,cliente."),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    actor: AuthenticatedActor = Depends(get_current_actor),
) -> dict[str, Any]:
    type_list = [t.strip() for t in types.split(",")] if types else None
    groups = await run_global_search(
        actor=actor, session_factory=get_session_factory(), q=q, types=type_list, limit=limit
    )
    return {
        "query": q,
        "results": [
            {
                "entity_type": g.entity_type, "total_matches": g.total_matches,
                "items": [{"id": i.id, "label": i.label, "entity_type": i.entity_type} for i in g.items],
            }
            for g in groups
        ],
    }
