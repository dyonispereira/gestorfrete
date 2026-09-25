from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, Response

from core.idempotency.guard import with_idempotency
from modules.freight.application.commands.confirm_manifest import ConfirmManifestCommand, ConfirmManifestHandler
from modules.freight.domain.entities.cargo_item import CargoItemSpec
from modules.freight.interfaces.schemas.manifest_schemas import ConfirmManifestRequest, ManifestResponse
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/viagens", tags=["Trip Manifest"])


@router.post("/{trip_id}/romaneios")
async def confirm_manifest(
    trip_id: uuid.UUID,
    body: ConfirmManifestRequest,
    response: Response,
    actor: AuthenticatedActor = Depends(require_permission("freight.packing_list.create")),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    """Pilot Hardening Final, Parte 6 (D211) — retry/duplo-clique nunca confirma o Romaneio duas
    vezes quando `Idempotency-Key` é enviada."""

    async def _run() -> ManifestResponse:
        handler = ConfirmManifestHandler()
        dto = await handler.handle(
            ConfirmManifestCommand(
                actor=actor, trip_id=trip_id, numero_documento=body.document_number,
                itens=[
                    CargoItemSpec(descricao=item.description, peso=item.weight_kg, quantidade=item.quantity)
                    for item in body.items
                ],
            )
        )
        return ManifestResponse.from_dto(dto)

    status_code, response_body = await with_idempotency(
        tenant_id=actor.tenant_id, idempotency_key=idempotency_key, method="POST",
        path=f"/viagens/{trip_id}/romaneios", payload=body.model_dump(mode="json"), status_code=201, run=_run,
    )
    response.status_code = status_code
    return response_body
