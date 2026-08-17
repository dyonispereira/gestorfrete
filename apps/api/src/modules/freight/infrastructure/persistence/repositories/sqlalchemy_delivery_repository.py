from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.freight.domain.entities.delivery import Delivery
from modules.freight.domain.entities.delivery_window import DeliveryWindow
from modules.freight.domain.repositories.delivery_repository import DeliveryRepository
from modules.freight.domain.value_objects.delivery_status import DeliveryStatus
from modules.freight.infrastructure.persistence.models.delivery_model import DeliveryModel, DeliveryWindowModel


def _to_entity(model: DeliveryModel) -> Delivery:
    return Delivery(
        id=model.id,
        viagem_id=model.viagem_id,
        ordem=model.ordem,
        destinatario=model.destinatario,
        endereco_entrega=model.endereco_entrega,
        status=DeliveryStatus(model.status),
        data_hora_conclusao=model.data_hora_conclusao,
        motivo_recusa=model.motivo_recusa,
    )


def _window_to_entity(model: DeliveryWindowModel) -> DeliveryWindow:
    return DeliveryWindow(id=model.id, entrega_id=model.entrega_id, hora_inicio=model.hora_inicio, hora_fim=model.hora_fim)


class SqlAlchemyDeliveryRepository(DeliveryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Delivery | None:
        tenant_id = get_current_tenant_id()
        stmt = select(DeliveryModel).where(DeliveryModel.id == id, DeliveryModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_for_trip(self, viagem_id: uuid.UUID) -> list[Delivery]:
        tenant_id = get_current_tenant_id()
        stmt = (
            select(DeliveryModel)
            .where(DeliveryModel.tenant_id == tenant_id, DeliveryModel.viagem_id == viagem_id)
            .order_by(DeliveryModel.ordem)
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models]

    async def exists_with_order(self, viagem_id: uuid.UUID, ordem: int) -> bool:
        tenant_id = get_current_tenant_id()
        stmt = select(DeliveryModel.id).where(
            DeliveryModel.tenant_id == tenant_id, DeliveryModel.viagem_id == viagem_id, DeliveryModel.ordem == ordem
        )
        return (await self._session.execute(stmt)).first() is not None

    async def count_pending_for_trip(self, viagem_id: uuid.UUID, *, excluding_id: uuid.UUID | None = None) -> int:
        tenant_id = get_current_tenant_id()
        stmt = select(DeliveryModel.id).where(
            DeliveryModel.tenant_id == tenant_id,
            DeliveryModel.viagem_id == viagem_id,
            DeliveryModel.status == DeliveryStatus.PENDENTE.value,
        )
        if excluding_id is not None:
            stmt = stmt.where(DeliveryModel.id != excluding_id)
        return len((await self._session.execute(stmt)).all())

    async def get_window(self, entrega_id: uuid.UUID) -> DeliveryWindow | None:
        tenant_id = get_current_tenant_id()
        stmt = select(DeliveryWindowModel).where(
            DeliveryWindowModel.tenant_id == tenant_id, DeliveryWindowModel.entrega_id == entrega_id
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _window_to_entity(model) if model is not None else None

    async def add_window(self, window: DeliveryWindow) -> None:
        tenant_id = get_current_tenant_id()
        model = DeliveryWindowModel(
            id=window.id,
            tenant_id=tenant_id,
            entrega_id=window.entrega_id,
            hora_inicio=window.hora_inicio,
            hora_fim=window.hora_fim,
        )
        self._session.add(model)
        await self._session.flush()

    async def add(self, aggregate: Delivery) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(DeliveryModel, aggregate.id)
        if model is None:
            model = DeliveryModel(id=aggregate.id, tenant_id=tenant_id, viagem_id=aggregate.viagem_id, ordem=aggregate.ordem)
            self._session.add(model)
        model.destinatario = aggregate.destinatario
        model.endereco_entrega = aggregate.endereco_entrega
        model.status = aggregate.status.value
        model.data_hora_conclusao = aggregate.data_hora_conclusao
        model.motivo_recusa = aggregate.motivo_recusa
        await self._session.flush()
