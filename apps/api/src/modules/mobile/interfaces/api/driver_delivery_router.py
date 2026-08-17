from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends

from core.database.session import get_session_factory
from modules.freight.interfaces.schemas.delivery_schemas import DeliveryResponse, ProofOfDeliveryResponse
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.mobile.application.commands.register_mobile_pod import RegisterMobilePodCommand, RegisterMobilePodHandler
from modules.mobile.application.queries.get_own_delivery import GetOwnDeliveryHandler, GetOwnDeliveryQuery
from modules.mobile.application.queries.list_own_deliveries import ListOwnDeliveriesHandler, ListOwnDeliveriesQuery
from modules.mobile.application.queries.ownership import assert_owns_trip
from modules.mobile.domain.entities.mobile_session import MobileSession
from modules.mobile.domain.value_objects.signatory_role import SignatoryRole
from modules.mobile.interfaces.dependencies import get_current_mobile_session
from modules.mobile.interfaces.schemas.delivery_schemas import MobilePodRequest
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/mobile/trips", tags=["Mobile Deliveries"])

# D429 (Backend Freeze) — `register_own_delivery` (`POST /{trip_id}/deliveries`) existiu aqui até
# o Freeze e foi removida: `060-driver-sync.md` nunca listou criação de Entrega entre as
# capacidades permitidas ao Motorista (só Comandos de Viagem/Ocorrências/Assinatura via Entrega
# já existente), e `openapi.yaml` nunca declarou essa operação. Reaproveitar `CreateDeliveryHandler`
# (D303) não autoriza uma superfície HTTP nova fora do contrato congelado. Se o Mobile precisar
# disso no futuro, entra por uma decisão explícita de evolução/versionamento, nunca implícita.


@router.get("/{trip_id}/deliveries")
async def list_own_deliveries(
    trip_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("freight.delivery.view")),
    mobile_session: MobileSession = Depends(get_current_mobile_session),
) -> dict[str, Any]:
    handler = ListOwnDeliveriesHandler(get_session_factory())
    items = await handler.handle(
        ListOwnDeliveriesQuery(actor=actor, driver_id=mobile_session.motorista_id, trip_id=trip_id)
    )
    responses = [DeliveryResponse.from_dto(d) for d in items]
    return {"data": responses, "meta": {"pagination": {"page": 1, "limit": len(responses), "total": len(responses)}}}


@router.get("/{trip_id}/deliveries/{delivery_id}", response_model=DeliveryResponse)
async def get_own_delivery(
    trip_id: uuid.UUID, delivery_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("freight.delivery.view")),
    mobile_session: MobileSession = Depends(get_current_mobile_session),
) -> DeliveryResponse:
    handler = GetOwnDeliveryHandler(get_session_factory())
    dto = await handler.handle(
        GetOwnDeliveryQuery(actor=actor, driver_id=mobile_session.motorista_id, trip_id=trip_id, delivery_id=delivery_id)
    )
    return DeliveryResponse.from_dto(dto)


@router.post("/{trip_id}/deliveries/{delivery_id}/pod", response_model=ProofOfDeliveryResponse, status_code=201)
async def register_own_pod(
    trip_id: uuid.UUID, delivery_id: uuid.UUID, body: MobilePodRequest,
    actor: AuthenticatedActor = Depends(require_permission("freight.pod.create")),
    mobile_session: MobileSession = Depends(get_current_mobile_session),
) -> ProofOfDeliveryResponse:
    await assert_owns_trip(
        get_session_factory(), actor=actor, driver_id=mobile_session.motorista_id, trip_id=trip_id
    )
    dto = await RegisterMobilePodHandler().handle(
        RegisterMobilePodCommand(
            actor=actor, trip_id=trip_id, delivery_id=delivery_id, photo_file_id=body.photo_file_id,
            signature_file_id=body.signature_file_id, signatory_role=SignatoryRole(body.signatory_role),
            signatory_name=body.signatory_name,
        )
    )
    return ProofOfDeliveryResponse.from_dto(dto)
