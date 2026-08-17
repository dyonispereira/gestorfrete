from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from core.exceptions.base import ConflictError
from modules.financial.domain.value_objects.receivable_status import ReceivableStatus
from shared_kernel.domain.base_entity import BaseEntity

_EDITABLE_STATUSES = frozenset({ReceivableStatus.PENDENTE, ReceivableStatus.VENCIDA})


class AccountsReceivable(BaseEntity[uuid.UUID]):
    """`contas_receber` — sub-recurso de `Invoice` (`fatura_id NOT NULL` fisicamente, D260, nunca
    existe fora de uma Fatura). Sem `audit` (D391-nota: schema nunca prometeu, DDL nunca teve)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        fatura_id: uuid.UUID,
        numero_parcela: int,
        valor: Decimal,
        data_vencimento: date,
        data_recebimento: datetime | None,
        status: ReceivableStatus,
    ) -> None:
        super().__init__(id)
        self.fatura_id = fatura_id
        self.numero_parcela = numero_parcela
        self.valor = valor
        self.data_vencimento = data_vencimento
        self.data_recebimento = data_recebimento
        self.status = status

    @classmethod
    def create(
        cls, *, fatura_id: uuid.UUID, numero_parcela: int, valor: Decimal, data_vencimento: date
    ) -> "AccountsReceivable":
        return cls(
            id=uuid.uuid4(), fatura_id=fatura_id, numero_parcela=numero_parcela, valor=valor,
            data_vencimento=data_vencimento, data_recebimento=None, status=ReceivableStatus.PENDENTE,
        )

    @property
    def effective_status(self) -> ReceivableStatus:
        """`PENDENTE→VENCIDA` — Derivada, calculada na leitura (mesmo raciocínio de
        `DriverDocument.status`, Lote 3) — nunca uma coluna gravada como fonte de verdade separada."""

        if self.status == ReceivableStatus.PENDENTE and self.data_vencimento < datetime.now(timezone.utc).date():
            return ReceivableStatus.VENCIDA
        return self.status

    def update(self, *, valor: Decimal | None, data_vencimento: date | None) -> None:
        if self.effective_status not in _EDITABLE_STATUSES:
            raise ConflictError(
                "FINANCIAL_RECEIVABLE_INVALID_STATUS", "Só é possível editar uma Conta a Receber PENDENTE/VENCIDA."
            )
        if valor is not None:
            self.valor = valor
        if data_vencimento is not None:
            self.data_vencimento = data_vencimento

    def confirm_receipt(self, *, now: datetime) -> None:
        if self.effective_status not in _EDITABLE_STATUSES:
            raise ConflictError(
                "FINANCIAL_RECEIVABLE_INVALID_TRANSITION",
                "Só é possível confirmar recebimento de uma Conta a Receber PENDENTE/VENCIDA.",
            )
        self.status = ReceivableStatus.RECEBIDA
        self.data_recebimento = now
