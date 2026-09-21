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
    valor_recebido: Decimal
    saldo_aberto: Decimal
    data_vencimento: date
    competencia: date
    data_recebimento: datetime | None
    status: str
    # Só preenchido pela consulta agregada entre Faturas (Lote Financeiro, Parte 2.1) — nunca um
    # campo do agregado `AccountsReceivable` em si (`cliente_id` continua proibido ali, D260/D008
    # style — acessível só via Fatura). `None` em qualquer outro caminho (get/list-for-invoice).
    cliente_id: uuid.UUID | None = None

    @staticmethod
    def from_entity(entity: AccountsReceivable, *, cliente_id: uuid.UUID | None = None) -> "AccountsReceivableDTO":
        return AccountsReceivableDTO(
            id=entity.id, fatura_id=entity.fatura_id, numero_parcela=entity.numero_parcela, valor=entity.valor,
            valor_recebido=entity.valor_recebido, saldo_aberto=entity.saldo_aberto,
            data_vencimento=entity.data_vencimento, competencia=entity.competencia,
            data_recebimento=entity.data_recebimento, status=entity.effective_status.value, cliente_id=cliente_id,
        )
