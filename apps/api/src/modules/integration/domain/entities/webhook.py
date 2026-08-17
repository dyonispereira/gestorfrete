from __future__ import annotations

import uuid

from modules.integration.domain.value_objects.webhook_status import WebhookStatus
from shared_kernel.domain.base_entity import BaseEntity

MAX_CONSECUTIVE_FAILURES = 3


class Webhook(BaseEntity[uuid.UUID]):
    """`webhooks` (D111/D138) — sem nenhuma coluna de auditoria na DDL congelada; `WebhookResponse`
    omite `audit` (mesmo tratamento de `IntegrationConfig`, D400-family). `numero_falhas_
    consecutivas` só existe em memória (via `WebhookInternalTransitions`, D413) — não é coluna
    física, já que a entrega real fica fora do contrato deste lote."""

    def __init__(
        self, id: uuid.UUID, *, configuracao_integracao_id: uuid.UUID | None, url_destino: str,
        eventos_assinados: list[str], segredo_hmac_arquivo_id: uuid.UUID, status: WebhookStatus,
    ) -> None:
        super().__init__(id)
        self.configuracao_integracao_id = configuracao_integracao_id
        self.url_destino = url_destino
        self.eventos_assinados = eventos_assinados
        self.segredo_hmac_arquivo_id = segredo_hmac_arquivo_id
        self.status = status

    @classmethod
    def create(
        cls, *, configuracao_integracao_id: uuid.UUID | None, url_destino: str, eventos_assinados: list[str],
        segredo_hmac_arquivo_id: uuid.UUID,
    ) -> "Webhook":
        return cls(
            id=uuid.uuid4(), configuracao_integracao_id=configuracao_integracao_id, url_destino=url_destino,
            eventos_assinados=eventos_assinados, segredo_hmac_arquivo_id=segredo_hmac_arquivo_id,
            status=WebhookStatus.ATIVO,
        )

    def update(self, *, url_destino: str | None, eventos_assinados: list[str] | None) -> None:
        if url_destino is not None:
            self.url_destino = url_destino
        if eventos_assinados is not None:
            self.eventos_assinados = eventos_assinados

    def activate(self) -> None:
        self.status = WebhookStatus.ATIVO

    def suspend(self) -> None:
        self.status = WebhookStatus.SUSPENSO
