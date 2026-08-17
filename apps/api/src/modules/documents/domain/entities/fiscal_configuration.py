from __future__ import annotations

import uuid
from datetime import date

from modules.documents.domain.value_objects.fiscal_configuration_environment import (
    FiscalConfigurationEnvironment,
)
from modules.documents.domain.value_objects.fiscal_configuration_status import FiscalConfigurationStatus
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class FiscalConfiguration(BaseAggregateRoot[uuid.UUID]):
    """`configuracoes_fiscais_tenant` — única fonte de numeração de CT-e/MDF-e (D110). Singular por
    tenant. D400 — sem `audit` (DDL congelada não tem nenhuma coluna de timestamp)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        certificado_arquivo_id: uuid.UUID,
        certificado_validade: date,
        ambiente: FiscalConfigurationEnvironment,
        regime_tributario: str,
        serie_cte: str,
        proximo_numero_cte: int,
        serie_mdfe: str,
        proximo_numero_mdfe: int,
        status: FiscalConfigurationStatus,
    ) -> None:
        super().__init__(id)
        self.certificado_arquivo_id = certificado_arquivo_id
        self.certificado_validade = certificado_validade
        self.ambiente = ambiente
        self.regime_tributario = regime_tributario
        self.serie_cte = serie_cte
        self.proximo_numero_cte = proximo_numero_cte
        self.serie_mdfe = serie_mdfe
        self.proximo_numero_mdfe = proximo_numero_mdfe
        self.status = status

    @classmethod
    def create(
        cls,
        *,
        certificado_arquivo_id: uuid.UUID,
        certificado_validade: date,
        ambiente: FiscalConfigurationEnvironment,
        regime_tributario: str,
        serie_cte: str,
        serie_mdfe: str,
    ) -> "FiscalConfiguration":
        return cls(
            id=uuid.uuid4(), certificado_arquivo_id=certificado_arquivo_id,
            certificado_validade=certificado_validade, ambiente=ambiente,
            regime_tributario=regime_tributario, serie_cte=serie_cte, proximo_numero_cte=1,
            serie_mdfe=serie_mdfe, proximo_numero_mdfe=1, status=FiscalConfigurationStatus.ATIVA,
        )

    def update(
        self,
        *,
        regime_tributario: str | None,
        certificado_arquivo_id: uuid.UUID | None,
        certificado_validade: date | None,
        serie_cte: str | None,
        serie_mdfe: str | None,
        ambiente: FiscalConfigurationEnvironment | None,
    ) -> None:
        if regime_tributario is not None:
            self.regime_tributario = regime_tributario
        if certificado_arquivo_id is not None:
            self.certificado_arquivo_id = certificado_arquivo_id
        if certificado_validade is not None:
            self.certificado_validade = certificado_validade
        if serie_cte is not None:
            self.serie_cte = serie_cte
        if serie_mdfe is not None:
            self.serie_mdfe = serie_mdfe
        if ambiente is not None:
            self.ambiente = ambiente

    def reserve_next_cte_number(self) -> int:
        """D110/D399 — chamado só dentro de uma transação que já obteve `SELECT ... FOR UPDATE`
        nesta linha (repositório de `FiscalConfiguration`); nunca decresce nem é reutilizado (D084)."""

        number = self.proximo_numero_cte
        self.proximo_numero_cte += 1
        return number

    def reserve_next_mdfe_number(self) -> int:
        number = self.proximo_numero_mdfe
        self.proximo_numero_mdfe += 1
        return number
