from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.financial.domain.entities.payment_method import PaymentMethod
from modules.financial.domain.repositories.payment_method_repository import PaymentMethodRepository
from modules.financial.domain.value_objects.payment_method_status import PaymentMethodStatus
from modules.financial.infrastructure.persistence.models.payment_method_model import PaymentMethodModel


def _to_entity(model: PaymentMethodModel) -> PaymentMethod:
    return PaymentMethod(id=model.id, nome=model.nome, status=PaymentMethodStatus(model.status))


class SqlAlchemyPaymentMethodRepository(PaymentMethodRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> PaymentMethod | None:
        tenant_id = get_current_tenant_id()
        stmt = select(PaymentMethodModel).where(PaymentMethodModel.id == id, PaymentMethodModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def add(self, payment_method: PaymentMethod) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(PaymentMethodModel, payment_method.id)
        if model is None:
            model = PaymentMethodModel(id=payment_method.id, tenant_id=tenant_id)
            self._session.add(model)
        model.nome = payment_method.nome
        model.status = payment_method.status.value
        await self._session.flush()
