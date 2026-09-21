from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from core.exceptions.base import ConflictError, ValidationError
from modules.financial.domain.value_objects.payable_origin import PayableOrigin
from modules.financial.domain.value_objects.payable_status import PayableStatus
from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot

# D255-style placeholder: sem endpoint de alçada configurável neste lote (`settings` não expõe
# isso ainda) — valor fixo documentado, substituível sem quebrar o contrato HTTP quando a alçada
# real existir. `032-accounts-payable.md`: "consultada em settings/Administração, nunca duplicada
# aqui... ainda sem endpoint próprio".
ALCADA_PADRAO = Decimal("1000.00")

_ORIGENS_COM_ALVO_OBRIGATORIO = frozenset({PayableOrigin.VIAGEM, PayableOrigin.ORDEM_SERVICO})


class AccountsPayable(BaseAggregateRoot[uuid.UUID]):
    """`contas_pagar` — Aggregate Root de `financial`. D273: sem `CANCELADA`, desfecho negativo
    real é `REJEITADA`. D391 — ganha o bloco padrão de auditoria, ausente na DDL congelada.
    `competencia` (Lote Financeiro, Parte 1) é sempre explícita — nunca calculada de
    `data_vencimento`. `veiculo_tracionador_id`/`motorista_id` são opcionais e independentes:
    `motorista_id` nunca é herdado automaticamente de `viagem_id`, mesmo quando ambos fazem
    sentido — só setado quando o lançamento é atribuível ao motorista por si só (D033/D034 — não
    duplica uma dimensão que já é derivável via Viagem quando não é o caso)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        fornecedor_id: uuid.UUID,
        centro_custo_id: uuid.UUID,
        origem: PayableOrigin,
        viagem_id: uuid.UUID | None,
        ordem_servico_id: uuid.UUID | None,
        veiculo_tracionador_id: uuid.UUID | None,
        motorista_id: uuid.UUID | None,
        valor: Decimal,
        data_vencimento: date,
        competencia: date,
        plano_contas_id: uuid.UUID,
        status: PayableStatus,
        audit: AuditMetadata,
    ) -> None:
        super().__init__(id)
        self.fornecedor_id = fornecedor_id
        self.centro_custo_id = centro_custo_id
        self.origem = origem
        self.viagem_id = viagem_id
        self.ordem_servico_id = ordem_servico_id
        self.veiculo_tracionador_id = veiculo_tracionador_id
        self.motorista_id = motorista_id
        self.valor = valor
        self.data_vencimento = data_vencimento
        self.competencia = competencia
        self.plano_contas_id = plano_contas_id
        self.status = status
        self.audit = audit

    @staticmethod
    def check_origin(origem: PayableOrigin, *, viagem_id: uuid.UUID | None, ordem_servico_id: uuid.UUID | None) -> None:
        """`ck_contas_pagar_origem_especifica` (D099) reforçado no Domain, não só na DDL."""

        if origem == PayableOrigin.VIAGEM and viagem_id is None:
            raise ValidationError("FINANCIAL_PAYABLE_ORIGIN_MISMATCH", "origin=VIAGEM exige trip_id.")
        if origem == PayableOrigin.ORDEM_SERVICO and ordem_servico_id is None:
            raise ValidationError(
                "FINANCIAL_PAYABLE_ORIGIN_MISMATCH", "origin=ORDEM_SERVICO exige maintenance_order_id."
            )

    @classmethod
    def create(
        cls,
        *,
        fornecedor_id: uuid.UUID,
        centro_custo_id: uuid.UUID,
        origem: PayableOrigin,
        viagem_id: uuid.UUID | None,
        ordem_servico_id: uuid.UUID | None,
        veiculo_tracionador_id: uuid.UUID | None,
        motorista_id: uuid.UUID | None,
        valor: Decimal,
        data_vencimento: date,
        competencia: date,
        plano_contas_id: uuid.UUID,
        audit: AuditMetadata,
    ) -> "AccountsPayable":
        cls.check_origin(origem, viagem_id=viagem_id, ordem_servico_id=ordem_servico_id)
        # LANCADA→AGUARDANDO_APROVACAO / LANCADA→APROVADA — Derivada (018-trip-status.md/032's own
        # precedent): comparação contra alçada, nunca uma ação de ator.
        status = PayableStatus.AGUARDANDO_APROVACAO if valor > ALCADA_PADRAO else PayableStatus.APROVADA
        return cls(
            id=uuid.uuid4(), fornecedor_id=fornecedor_id, centro_custo_id=centro_custo_id, origem=origem,
            viagem_id=viagem_id, ordem_servico_id=ordem_servico_id, veiculo_tracionador_id=veiculo_tracionador_id,
            motorista_id=motorista_id, valor=valor, data_vencimento=data_vencimento, competencia=competencia,
            plano_contas_id=plano_contas_id, status=status, audit=audit,
        )

    @property
    def requires_approval(self) -> bool:
        return self.status == PayableStatus.AGUARDANDO_APROVACAO

    @property
    def allocation_target_trip_id(self) -> uuid.UUID | None:
        """Alvo do Rateio automático (D393) quando a origem tem viagem associada."""

        return self.viagem_id if self.origem in _ORIGENS_COM_ALVO_OBRIGATORIO else None

    def update(
        self,
        *,
        fornecedor_id: uuid.UUID | None,
        centro_custo_id: uuid.UUID | None,
        valor: Decimal | None,
        data_vencimento: date | None,
        plano_contas_id: uuid.UUID | None,
        updated_by: uuid.UUID,
        now: datetime,
    ) -> None:
        if self.status != PayableStatus.LANCADA:
            raise ConflictError("FINANCIAL_PAYABLE_INVALID_STATUS", "Só é possível editar uma Conta a Pagar LANCADA.")
        if fornecedor_id is not None:
            self.fornecedor_id = fornecedor_id
        if centro_custo_id is not None:
            self.centro_custo_id = centro_custo_id
        if valor is not None:
            self.valor = valor
        if data_vencimento is not None:
            self.data_vencimento = data_vencimento
        if plano_contas_id is not None:
            self.plano_contas_id = plano_contas_id
        self.audit = self.audit.touched(by=updated_by, at=now)

    def soft_delete(self, *, deleted_by: uuid.UUID, now: datetime) -> None:
        if self.status != PayableStatus.LANCADA:
            raise ConflictError(
                "FINANCIAL_PAYABLE_DELETE_INVALID_STATUS", "Só é possível excluir uma Conta a Pagar LANCADA."
            )
        self.audit = self.audit.soft_deleted(by=deleted_by, at=now)

    def approve(self) -> None:
        if self.status != PayableStatus.AGUARDANDO_APROVACAO:
            raise ConflictError(
                "FINANCIAL_PAYABLE_INVALID_TRANSITION", "Conta a Pagar não está aguardando aprovação."
            )
        self.status = PayableStatus.APROVADA

    def reject(self) -> None:
        if self.status != PayableStatus.AGUARDANDO_APROVACAO:
            raise ConflictError(
                "FINANCIAL_PAYABLE_INVALID_TRANSITION", "Conta a Pagar não está aguardando aprovação."
            )
        self.status = PayableStatus.REJEITADA

    def pay(self) -> None:
        if self.status != PayableStatus.APROVADA:
            raise ConflictError("FINANCIAL_PAYABLE_INVALID_TRANSITION", "Conta a Pagar não está APROVADA.")
        self.status = PayableStatus.PAGA
