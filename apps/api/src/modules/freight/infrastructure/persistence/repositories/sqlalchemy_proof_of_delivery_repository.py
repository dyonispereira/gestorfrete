from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.freight.domain.entities.proof_of_delivery import ProofOfDelivery
from modules.freight.domain.repositories.proof_of_delivery_repository import ProofOfDeliveryRepository
from modules.freight.domain.value_objects.proof_of_delivery_status import ProofOfDeliveryStatus
from modules.freight.infrastructure.persistence.models.proof_of_delivery_model import ProofOfDeliveryModel


def _to_entity(model: ProofOfDeliveryModel) -> ProofOfDelivery:
    return ProofOfDelivery(
        id=model.id,
        entrega_id=model.entrega_id,
        status=ProofOfDeliveryStatus(model.status),
        data_hora_registro=model.data_hora_registro,
        assinatura_arquivo_id=model.assinatura_arquivo_id,
    )


class SqlAlchemyProofOfDeliveryRepository(ProofOfDeliveryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_for_delivery(self, entrega_id: uuid.UUID) -> ProofOfDelivery | None:
        tenant_id = get_current_tenant_id()
        stmt = select(ProofOfDeliveryModel).where(
            ProofOfDeliveryModel.tenant_id == tenant_id, ProofOfDeliveryModel.entrega_id == entrega_id
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def exists_for_delivery(self, entrega_id: uuid.UUID) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(ProofOfDeliveryModel.id).where(
            ProofOfDeliveryModel.tenant_id == tenant_id, ProofOfDeliveryModel.entrega_id == entrega_id
        )
        return (await self._session.execute(stmt)).first() is not None

    async def create(self, proof_of_delivery: ProofOfDelivery) -> None:
        tenant_id = get_current_tenant_id()
        model = ProofOfDeliveryModel(
            id=proof_of_delivery.id,
            tenant_id=tenant_id,
            entrega_id=proof_of_delivery.entrega_id,
            status=proof_of_delivery.status.value,
            data_hora_registro=proof_of_delivery.data_hora_registro,
            assinatura_arquivo_id=proof_of_delivery.assinatura_arquivo_id,
        )
        self._session.add(model)
        await self._session.flush()
