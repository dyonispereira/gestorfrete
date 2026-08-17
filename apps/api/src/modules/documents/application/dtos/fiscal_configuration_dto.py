from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from modules.documents.domain.entities.fiscal_configuration import FiscalConfiguration


@dataclass(frozen=True)
class FiscalConfigurationDTO:
    id: uuid.UUID
    certificado_arquivo_id: uuid.UUID
    certificado_validade: date
    ambiente: str
    regime_tributario: str
    serie_cte: str
    proximo_numero_cte: int
    serie_mdfe: str
    proximo_numero_mdfe: int
    status: str

    @staticmethod
    def from_entity(entity: FiscalConfiguration) -> "FiscalConfigurationDTO":
        return FiscalConfigurationDTO(
            id=entity.id, certificado_arquivo_id=entity.certificado_arquivo_id,
            certificado_validade=entity.certificado_validade, ambiente=entity.ambiente.value,
            regime_tributario=entity.regime_tributario, serie_cte=entity.serie_cte,
            proximo_numero_cte=entity.proximo_numero_cte, serie_mdfe=entity.serie_mdfe,
            proximo_numero_mdfe=entity.proximo_numero_mdfe, status=entity.status.value,
        )
