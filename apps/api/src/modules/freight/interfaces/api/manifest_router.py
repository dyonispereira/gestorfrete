from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from modules.freight.application.commands.confirm_manifest import ConfirmManifestCommand, ConfirmManifestHandler
from modules.freight.domain.entities.cargo_item import CargoItemSpec
from modules.freight.interfaces.schemas.manifest_schemas import ConfirmManifestRequest, ManifestResponse
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/viagens", tags=["Trip Manifest"])


@router.post("/{trip_id}/romaneios", response_model=ManifestResponse, status_code=201)
async def confirm_manifest(
    trip_id: uuid.UUID,
    body: ConfirmManifestRequest,
    actor: AuthenticatedActor = Depends(require_permission("freight.packing_list.create")),
) -> ManifestResponse:
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
