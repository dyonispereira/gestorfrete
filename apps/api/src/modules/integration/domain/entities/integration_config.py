from __future__ import annotations

import uuid

from modules.integration.domain.value_objects.integration_config_status import IntegrationConfigStatus
from shared_kernel.domain.base_entity import BaseEntity


class IntegrationConfig(BaseEntity[uuid.UUID]):
    """`configuracoes_integracao` (D321) — contrato único, nunca uma API diferente por fornecedor.
    `credencial_arquivo_id` sempre referencia um `File` (`storage`), nunca texto claro. Sem nenhuma
    coluna de auditoria na DDL congelada (nem `criado_em`) — `IntegrationConfigResponse` omite
    `audit` inteiramente, mesmo tratamento de `MDFeResponse`/`CIOTResponse` (D400)."""

    def __init__(
        self, id: uuid.UUID, *, tipo: str, credencial_arquivo_id: uuid.UUID, status: IntegrationConfigStatus,
    ) -> None:
        super().__init__(id)
        self.tipo = tipo
        self.credencial_arquivo_id = credencial_arquivo_id
        self.status = status

    @classmethod
    def create(cls, *, tipo: str, credencial_arquivo_id: uuid.UUID) -> "IntegrationConfig":
        return cls(
            id=uuid.uuid4(), tipo=tipo, credencial_arquivo_id=credencial_arquivo_id,
            status=IntegrationConfigStatus.ATIVA,
        )

    def enable(self) -> None:
        self.status = IntegrationConfigStatus.ATIVA

    def disable(self) -> None:
        self.status = IntegrationConfigStatus.INATIVA

    def rotate_credential(self, credencial_arquivo_id: uuid.UUID) -> None:
        self.credencial_arquivo_id = credencial_arquivo_id
