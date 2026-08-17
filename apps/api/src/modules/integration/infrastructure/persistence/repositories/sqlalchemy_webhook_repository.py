from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.integration.domain.entities.webhook import Webhook
from modules.integration.domain.repositories.webhook_repository import WebhookRepository
from modules.integration.domain.value_objects.webhook_status import WebhookStatus
from modules.integration.infrastructure.persistence.models.webhook_model import WebhookModel


def _to_entity(model: WebhookModel) -> Webhook:
    return Webhook(
        id=model.id, configuracao_integracao_id=model.configuracao_integracao_id, url_destino=model.url_destino,
        eventos_assinados=list(model.eventos_assinados), segredo_hmac_arquivo_id=model.segredo_hmac_arquivo_id,
        status=WebhookStatus(model.status),
    )


class SqlAlchemyWebhookRepository(WebhookRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Webhook | None:
        tenant_id = get_current_tenant_id()
        stmt = select(WebhookModel).where(WebhookModel.id == id, WebhookModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page(
        self, *, page: int, limit: int, integration_config_id: uuid.UUID | None, status: str | None
    ) -> tuple[list[Webhook], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(WebhookModel).where(WebhookModel.tenant_id == tenant_id)
        if integration_config_id is not None:
            stmt = stmt.where(WebhookModel.configuracao_integracao_id == integration_config_id)
        if status is not None:
            stmt = stmt.where(WebhookModel.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, webhook: Webhook) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(WebhookModel, webhook.id)
        if model is None:
            model = WebhookModel(id=webhook.id, tenant_id=tenant_id)
            self._session.add(model)
        model.configuracao_integracao_id = webhook.configuracao_integracao_id
        model.url_destino = webhook.url_destino
        model.eventos_assinados = webhook.eventos_assinados
        model.segredo_hmac_arquivo_id = webhook.segredo_hmac_arquivo_id
        model.status = webhook.status.value
        await self._session.flush()
