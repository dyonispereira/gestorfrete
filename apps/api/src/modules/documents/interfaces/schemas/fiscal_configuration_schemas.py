from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict

from modules.documents.application.dtos.fiscal_configuration_dto import FiscalConfigurationDTO


class FiscalConfigurationResponse(BaseModel):
    """D400 — sem `audit`: `configuracoes_fiscais_tenant` não tem nenhuma coluna de timestamp na
    DDL congelada."""

    id: uuid.UUID
    certificate_file_id: uuid.UUID
    certificate_expires_at: date
    environment: str
    tax_regime: str
    cte_series: str
    next_cte_number: int
    mdfe_series: str
    next_mdfe_number: int
    status: str

    @staticmethod
    def from_dto(dto: FiscalConfigurationDTO) -> "FiscalConfigurationResponse":
        return FiscalConfigurationResponse(
            id=dto.id, certificate_file_id=dto.certificado_arquivo_id,
            certificate_expires_at=dto.certificado_validade, environment=dto.ambiente,
            tax_regime=dto.regime_tributario, cte_series=dto.serie_cte, next_cte_number=dto.proximo_numero_cte,
            mdfe_series=dto.serie_mdfe, next_mdfe_number=dto.proximo_numero_mdfe, status=dto.status,
        )


class UpdateFiscalConfigurationRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    tax_regime: str | None = None
    certificate_file_id: uuid.UUID | None = None
    certificate_expires_at: date | None = None
    cte_series: str | None = None
    mdfe_series: str | None = None
    environment: str | None = None
