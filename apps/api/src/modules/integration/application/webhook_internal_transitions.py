from __future__ import annotations

import uuid

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.integration.domain.entities.webhook import MAX_CONSECUTIVE_FAILURES
from modules.integration.domain.value_objects.webhook_status import WebhookStatus
from modules.integration.infrastructure.persistence.repositories.sqlalchemy_webhook_repository import (
    SqlAlchemyWebhookRepository,
)

_consecutive_failures: dict[uuid.UUID, int] = {}
"""D413 — a entrega real de evento de domínio a um Webhook fica fora deste contrato (worker
assíncrono, infraestrutura, `088-webhooks.md`); este dict em processo só existe para
`WebhookInternalTransitions` provar a regra "3 falhas consecutivas suspendem o Webhook" em teste,
nunca uma fonte de verdade persistida (não há coluna física para isso em `webhooks`)."""


class WebhookInternalTransitions:
    """Mesmo espírito de `TripInternalTransitions`/`FiscalInternalTransitions` — nunca alcançável
    por HTTP, só chamado diretamente por teste, simulando o worker de entrega que este lote não
    constrói (D413)."""

    async def simulate_delivery_attempt(self, *, webhook_id: uuid.UUID, success: bool) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyWebhookRepository(uow.session)
            webhook = await repo.get_by_id(webhook_id)
            if webhook is None:
                raise NotFoundError("INTEGRATION_WEBHOOK_NOT_FOUND", "Webhook não encontrado.")

            if success:
                _consecutive_failures[webhook_id] = 0
            else:
                failures = _consecutive_failures.get(webhook_id, 0) + 1
                _consecutive_failures[webhook_id] = failures
                if failures >= MAX_CONSECUTIVE_FAILURES and webhook.status == WebhookStatus.ATIVO:
                    webhook.suspend()
                    await repo.add(webhook)

            await uow.commit()
