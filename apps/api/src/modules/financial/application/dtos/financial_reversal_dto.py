from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from modules.financial.domain.entities.financial_reversal import FinancialReversal


@dataclass(frozen=True)
class FinancialReversalDTO:
    id: uuid.UUID
    fatura_id: uuid.UUID | None
    conta_pagar_id: uuid.UUID | None
    conta_receber_id: uuid.UUID | None
    valor: Decimal
    motivo: str
    data_hora: datetime
    # Lote Financeiro, Parte 2.1 — nunca um campo do agregado `FinancialReversal` em si (D266: sem
    # `AuditMetadata` própria, decisão deliberada). Resolvido via `AuditTrailReader` sobre a trilha
    # transversal (`logs_auditoria`), que já capturava isso desde sempre — não duplicado aqui.
    criado_por: uuid.UUID | None = None

    @staticmethod
    def from_entity(entity: FinancialReversal, *, criado_por: uuid.UUID | None = None) -> "FinancialReversalDTO":
        return FinancialReversalDTO(
            id=entity.id, fatura_id=entity.fatura_id, conta_pagar_id=entity.conta_pagar_id,
            conta_receber_id=entity.conta_receber_id, valor=entity.valor, motivo=entity.motivo,
            data_hora=entity.data_hora, criado_por=criado_por,
        )
