from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from core.exceptions.base import ConflictError
from modules.financial.domain.value_objects.receivable_status import ReceivableStatus
from shared_kernel.domain.base_entity import BaseEntity

_EDITABLE_STATUSES = frozenset({ReceivableStatus.PENDENTE, ReceivableStatus.VENCIDA})


_RECEIVABLE_STATUSES = _EDITABLE_STATUSES | frozenset({ReceivableStatus.PARCIALMENTE_RECEBIDO})


class AccountsReceivable(BaseEntity[uuid.UUID]):
    """`contas_receber` — sub-recurso de `Invoice` (`fatura_id NOT NULL` fisicamente, D260, nunca
    existe fora de uma Fatura). Sem `audit` (D391-nota: schema nunca prometeu, DDL nunca teve).
    `competencia` (Lote Financeiro, Parte 1) é sempre explícita — nunca calculada de
    `data_vencimento`. `valor_recebido` (Lote Financeiro, Parte 2.1) é o acumulado de baixas já
    recebidas nesta parcela — baixa parcial real, distinta do parcelamento (N parcelas por
    Fatura), que já existia antes e continua existindo em paralelo."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        fatura_id: uuid.UUID,
        numero_parcela: int,
        valor: Decimal,
        valor_recebido: Decimal,
        data_vencimento: date,
        competencia: date,
        data_recebimento: datetime | None,
        status: ReceivableStatus,
    ) -> None:
        super().__init__(id)
        self.fatura_id = fatura_id
        self.numero_parcela = numero_parcela
        self.valor = valor
        self.valor_recebido = valor_recebido
        self.data_vencimento = data_vencimento
        self.competencia = competencia
        self.data_recebimento = data_recebimento
        self.status = status

    @classmethod
    def create(
        cls, *, fatura_id: uuid.UUID, numero_parcela: int, valor: Decimal, data_vencimento: date, competencia: date
    ) -> "AccountsReceivable":
        return cls(
            id=uuid.uuid4(), fatura_id=fatura_id, numero_parcela=numero_parcela, valor=valor,
            valor_recebido=Decimal("0"), data_vencimento=data_vencimento, competencia=competencia,
            data_recebimento=None, status=ReceivableStatus.PENDENTE,
        )

    @property
    def saldo_aberto(self) -> Decimal:
        return self.valor - self.valor_recebido

    @property
    def effective_status(self) -> ReceivableStatus:
        """`PENDENTE→VENCIDA` — Derivada, calculada na leitura (mesmo raciocínio de
        `DriverDocument.status`, Lote 3) — nunca uma coluna gravada como fonte de verdade separada.
        `PARCIALMENTE_RECEBIDO` nunca é sobrescrita por essa derivação, mesmo com vencimento
        passado — já existe progresso real registrado, "vencida" esconderia isso (decisão de V1,
        revisitável, ver nota de reconciliação em `docs/domain/006-financeiro.md`)."""

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

    def receive_payment(self, *, valor: Decimal, now: datetime) -> None:
        """Baixa parcial ou total — cada chamada soma `valor` a `valor_recebido`. Invariante:
        `0 < valor <= saldo_aberto`. `RECEBIDA` só é atingida quando o saldo chega exatamente a
        zero; antes disso, `PARCIALMENTE_RECEBIDO`. Chamável repetidamente enquanto houver saldo
        em aberto — não é uma operação de uma vez só."""

        if self.effective_status not in _RECEIVABLE_STATUSES:
            raise ConflictError(
                "FINANCIAL_RECEIVABLE_INVALID_TRANSITION",
                "Só é possível confirmar recebimento de uma Conta a Receber em aberto "
                "(Pendente, Vencida ou Parcialmente Recebida).",
            )
        if valor <= 0 or valor > self.saldo_aberto:
            raise ConflictError(
                "FINANCIAL_RECEIVABLE_INVALID_PAYMENT_VALUE",
                f"O valor da baixa deve ser maior que zero e no máximo o saldo em aberto ({self.saldo_aberto}).",
            )
        self.valor_recebido += valor
        if self.valor_recebido >= self.valor:
            self.status = ReceivableStatus.RECEBIDA
            self.data_recebimento = now
        else:
            self.status = ReceivableStatus.PARCIALMENTE_RECEBIDO
