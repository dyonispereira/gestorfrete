from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict

from modules.integration.application.dtos.integration_config_dto import IntegrationConfigDTO


class CreateIntegrationConfigRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str
    credential_file_id: uuid.UUID


class UpdateIntegrationConfigRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    credential_file_id: uuid.UUID


class IntegrationConfigResponse(BaseModel):
    """Sem `audit` — `configuracoes_integracao` não tem nenhuma coluna de timestamp na DDL congelada
    (D400-family, ver `INTEGRATION_IMPLEMENTATION.md`)."""

    id: uuid.UUID
    type: str
    credential_file_id: uuid.UUID
    status: str

    @staticmethod
    def from_dto(dto: IntegrationConfigDTO) -> "IntegrationConfigResponse":
        return IntegrationConfigResponse(id=dto.id, type=dto.type, credential_file_id=dto.credential_file_id, status=dto.status)
