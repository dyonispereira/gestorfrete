from __future__ import annotations

import uuid
from dataclasses import dataclass

from modules.integration.domain.entities.integration_config import IntegrationConfig


@dataclass(frozen=True)
class IntegrationConfigDTO:
    id: uuid.UUID
    type: str
    credential_file_id: uuid.UUID
    status: str

    @staticmethod
    def from_entity(config: IntegrationConfig) -> "IntegrationConfigDTO":
        return IntegrationConfigDTO(
            id=config.id, type=config.tipo, credential_file_id=config.credencial_arquivo_id,
            status=config.status.value,
        )
