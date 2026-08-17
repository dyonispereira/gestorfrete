from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from modules.financial.domain.entities.accounts_receivable import AccountsReceivable


@dataclass(frozen=True)
class AccountsReceivableDTO:
    id: uuid.UUID
    fatura_id: uuid.UUID
    numero_parcela: int
    valor: Decimal
    data_vencimento: date
    data_recebimento: datetime | None
    status: str

    @staticmethod
    def from_entity(entity: AccountsReceivable) -> "AccountsReceivableDTO":
        return AccountsReceivableDTO(
            id=entity.id, fatura_id=entity.fatura_id, numero_parcela=entity.numero_parcela, valor=entity.valor,
            data_vencimento=entity.data_vencimento, data_recebimento=entity.data_recebimento,
            status=entity.effective_status.value,
        )
