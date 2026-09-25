from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, Response

from core.idempotency.guard import with_idempotency
from modules.freight.application.commands.register_collection import (
    RegisterCollectionCommand,
    RegisterCollectionHandler,
)
from modules.freight.interfaces.schemas.collection_schemas import CollectionResponse, RegisterCollectionRequest
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/viagens", tags=["Trip Collection"])


@router.post("/{trip_id}/coletas")
async def register_collection(
    trip_id: uuid.UUID,
    body: RegisterCollectionRequest,
    response: Response,
    actor: AuthenticatedActor = Depends(require_permission("freight.pickup.create")),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    """Pilot Hardening Final, Parte 6 (D211) — retry/duplo-clique nunca registra a Coleta duas
    vezes quando `Idempotency-Key` é enviada."""

    async def _run() -> CollectionResponse:
        handler = RegisterCollectionHandler()
        dto = await handler.handle(
            RegisterCollectionCommand(actor=actor, trip_id=trip_id, conferencia_ok=body.cargo_checked)
        )
        return CollectionResponse.from_dto(dto)

    status_code, response_body = await with_idempotency(
        tenant_id=actor.tenant_id, idempotency_key=idempotency_key, method="POST",
        path=f"/viagens/{trip_id}/coletas", payload=body.model_dump(mode="json"), status_code=201, run=_run,
    )
    response.status_code = status_code
    return response_body
