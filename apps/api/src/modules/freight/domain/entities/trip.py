from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from core.exceptions.base import ConflictError, DomainError
from modules.freight.domain.value_objects.trip_financial_status import TripFinancialStatus
from modules.freight.domain.value_objects.trip_fiscal_status import TripFiscalStatus
from modules.freight.domain.value_objects.trip_operational_status import TripOperationalStatus
from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot

_INTERRUPTIBLE_STATUSES = frozenset(
    {
        TripOperationalStatus.EM_DESLOCAMENTO,
        TripOperationalStatus.CARREGANDO,
        TripOperationalStatus.EM_TRANSITO,
        TripOperationalStatus.EM_ENTREGA,
    }
)
_CANCELLABLE_STATUSES = frozenset(
    {
        TripOperationalStatus.RASCUNHO,
        TripOperationalStatus.PLANEJADA,
        TripOperationalStatus.AGUARDANDO_CHECKLIST,
        TripOperationalStatus.LIBERADA,
        TripOperationalStatus.INTERROMPIDA,
    }
)
_TERMINAL_STATUSES = frozenset({TripOperationalStatus.FINALIZADA, TripOperationalStatus.CANCELADA})


class Trip(BaseAggregateRoot[uuid.UUID]):
    """Aggregate Root de `freight` — `flows/002-VIAGEM.md`, o core domain do sistema. Cada método
    de transição só valida o estado atual e muda `status_operacional`; a gravação da linha
    correspondente em `viagem_status_history` é responsabilidade do Application (Handler), nunca
    desta entidade (que não tem acesso a sessão de banco) — ver `TRIP_IMPLEMENTATION.md`.

    `encerrada`/`margem_prevista` são colunas `GENERATED` no Postgres (D019/D185) — nunca definidas
    por nenhum método aqui; `SqlAlchemyTripRepository.add()` sempre as recarrega do banco logo após
    `flush()` e as atribui de volta nesta entidade, para que o DTO devolvido ao cliente (D238) nunca
    fique com um valor obsoleto.
    """

    def __init__(
        self,
        id: uuid.UUID,
        *,
        codigo: str,
        cliente_id: uuid.UUID,
        motorista_id: uuid.UUID | None,
        veiculo_tracionador_id: uuid.UUID | None,
        data_programada: date | None,
        janela_programada: datetime | None,
        status_operacional: TripOperationalStatus,
        status_fiscal: TripFiscalStatus,
        status_financeiro: TripFinancialStatus,
        nome_motorista_snapshot: str | None,
        placa_veiculo_snapshot: str | None,
        cliente_snapshot: dict[str, Any] | None,
        receita_prevista_snapshot: Decimal | None,
        tabela_preco_aplicada_snapshot_id: uuid.UUID | None,
        custo_previsto: Decimal | None,
        custo_realizado: Decimal | None,
        receita_realizada: Decimal | None,
        margem_realizada: Decimal | None,
        desvio_financeiro: Decimal | None,
        km_rodado: Decimal | None,
        encerrada: bool,
        margem_prevista: Decimal | None,
        audit: AuditMetadata,
    ) -> None:
        super().__init__(id)
        self.codigo = codigo
        self.cliente_id = cliente_id
        self.motorista_id = motorista_id
        self.veiculo_tracionador_id = veiculo_tracionador_id
        self.data_programada = data_programada
        self.janela_programada = janela_programada
        self.status_operacional = status_operacional
        self.status_fiscal = status_fiscal
        self.status_financeiro = status_financeiro
        self.nome_motorista_snapshot = nome_motorista_snapshot
        self.placa_veiculo_snapshot = placa_veiculo_snapshot
        self.cliente_snapshot = cliente_snapshot
        self.receita_prevista_snapshot = receita_prevista_snapshot
        self.tabela_preco_aplicada_snapshot_id = tabela_preco_aplicada_snapshot_id
        self.custo_previsto = custo_previsto
        self.custo_realizado = custo_realizado
        self.receita_realizada = receita_realizada
        self.margem_realizada = margem_realizada
        self.desvio_financeiro = desvio_financeiro
        self.km_rodado = km_rodado
        self.encerrada = encerrada
        self.margem_prevista = margem_prevista
        self.audit = audit

    @classmethod
    def create(
        cls,
        *,
        cliente_id: uuid.UUID,
        data_programada: date | None,
        janela_programada: datetime | None,
        cliente_snapshot: dict[str, Any] | None,
        now: datetime,
        audit: AuditMetadata,
    ) -> "Trip":
        return cls(
            id=uuid.uuid4(),
            codigo=f"VG-{now.year}-{uuid.uuid4().hex[:6].upper()}",
            cliente_id=cliente_id,
            motorista_id=None,
            veiculo_tracionador_id=None,
            data_programada=data_programada,
            janela_programada=janela_programada,
            status_operacional=TripOperationalStatus.RASCUNHO,
            status_fiscal=TripFiscalStatus.PENDENTE,
            status_financeiro=TripFinancialStatus.AGUARDANDO_FATURAMENTO,
            nome_motorista_snapshot=None,
            placa_veiculo_snapshot=None,
            cliente_snapshot=cliente_snapshot,
            receita_prevista_snapshot=None,
            tabela_preco_aplicada_snapshot_id=None,
            custo_previsto=None,
            custo_realizado=None,
            receita_realizada=None,
            margem_realizada=None,
            desvio_financeiro=None,
            km_rodado=None,
            encerrada=False,
            margem_prevista=None,
            audit=audit,
        )

    def update(
        self, *, data_programada: date | None, janela_programada: datetime | None, updated_by: uuid.UUID, now: datetime
    ) -> None:
        if self.status_operacional in _TERMINAL_STATUSES:
            raise DomainError(
                "FREIGHT_TRIP_CANNOT_EDIT_TERMINAL", "Viagem em estado terminal não pode ser editada."
            )
        if data_programada is not None:
            self.data_programada = data_programada
        if janela_programada is not None:
            self.janela_programada = janela_programada
        self.audit = self.audit.touched(by=updated_by, at=now)

    def delete(self, *, deleted_by: uuid.UUID, now: datetime) -> None:
        if self.status_operacional not in (TripOperationalStatus.RASCUNHO, TripOperationalStatus.PLANEJADA):
            raise DomainError(
                "FREIGHT_TRIP_CANNOT_DELETE_STARTED",
                "Viagem já iniciada não pode ser excluída — use commands/cancelar.",
            )
        self.audit = self.audit.soft_deleted(by=deleted_by, at=now)

    def set_current_allocation(self, *, motorista_id: uuid.UUID, veiculo_tracionador_id: uuid.UUID) -> None:
        """Colunas denormalizadas em `viagens` (D188) — mantidas em sincronia pelo Handler de
        alocação/realocação, nunca lidas de volta de `alocacoes_recurso_viagem` via JOIN."""

        self.motorista_id = motorista_id
        self.veiculo_tracionador_id = veiculo_tracionador_id

    def plan(self) -> None:
        """`RASCUNHO→PLANEJADA` — automática, disparada pela primeira Alocação de Recurso
        (`016-trip-resources.md`). Para **aqui**, não em cascata até `AGUARDANDO_CHECKLIST`: a
        Viagem precisa descansar observável em `PLANEJADA` para `commands/accept` (D129) fazer
        sentido — ver `await_checklist` para a transição seguinte, deliberadamente separada."""

        if self.status_operacional != TripOperationalStatus.RASCUNHO:
            raise ConflictError("FREIGHT_TRIP_INVALID_TRANSITION", "Viagem não está em RASCUNHO.")
        self.status_operacional = TripOperationalStatus.PLANEJADA

    def await_checklist(self) -> None:
        """D376 — simula o futuro gatilho "pronta para a data/rota programada" (`018-trip-
        status.md`, sem comando/RBAC próprio). Nunca uma rota HTTP."""

        if self.status_operacional != TripOperationalStatus.PLANEJADA:
            raise ConflictError("FREIGHT_TRIP_INVALID_TRANSITION", "Viagem não está PLANEJADA.")
        self.status_operacional = TripOperationalStatus.AGUARDANDO_CHECKLIST

    def release_after_checklist(self) -> None:
        """D376 — simula o futuro consumidor de `ChecklistAprovado` (`maintenance`, Checklist ainda
        não implementado). Nunca uma rota HTTP."""

        if self.status_operacional != TripOperationalStatus.AGUARDANDO_CHECKLIST:
            raise ConflictError("FREIGHT_TRIP_INVALID_TRANSITION", "Viagem não está aguardando checklist.")
        self.status_operacional = TripOperationalStatus.LIBERADA

    def dispatch(
        self, *, nome_motorista_snapshot: str, placa_veiculo_snapshot: str
    ) -> None:
        """`commands/dispatch`/`commands/start` — mesma transição, `origem` diferente gravada pelo
        Handler no histórico. D378 — momento em que os snapshots de Motorista/Veículo são
        congelados pela primeira e única vez."""

        if self.status_operacional != TripOperationalStatus.LIBERADA:
            raise ConflictError("FREIGHT_TRIP_INVALID_TRANSITION", "Viagem não está LIBERADA.")
        self.status_operacional = TripOperationalStatus.EM_DESLOCAMENTO
        self.nome_motorista_snapshot = nome_motorista_snapshot
        self.placa_veiculo_snapshot = placa_veiculo_snapshot

    def mark_collected(self) -> None:
        """D376 — simula o futuro endpoint de Coleta (fora de escopo, `015-trip-deliveries.md`)."""

        if self.status_operacional != TripOperationalStatus.EM_DESLOCAMENTO:
            raise ConflictError("FREIGHT_TRIP_INVALID_TRANSITION", "Viagem não está EM_DESLOCAMENTO.")
        self.status_operacional = TripOperationalStatus.CARREGANDO

    def mark_manifest_checked(self, *, has_pending_deliveries: bool) -> list[TripOperationalStatus]:
        """D376 — simula o futuro endpoint de Romaneio conferido (fora de escopo). Cascata para
        `EM_ENTREGA` quando já há Entregas `PENDENTE` a atender (mesmo raciocínio de
        `plan_and_await_checklist`)."""

        if self.status_operacional != TripOperationalStatus.CARREGANDO:
            raise ConflictError("FREIGHT_TRIP_INVALID_TRANSITION", "Viagem não está CARREGANDO.")
        if has_pending_deliveries:
            self.status_operacional = TripOperationalStatus.EM_ENTREGA
            return [TripOperationalStatus.EM_TRANSITO, TripOperationalStatus.EM_ENTREGA]
        self.status_operacional = TripOperationalStatus.EM_TRANSITO
        return [TripOperationalStatus.EM_TRANSITO]

    def accept(self) -> None:
        """`commands/accept` — D129, nunca muda `status_operacional` (aditivo). A checagem de
        idempotência (`FREIGHT_TRIP_ALREADY_ACCEPTED`, D379) é feita pelo Handler consultando o
        histórico antes de chamar este método."""

        if self.status_operacional != TripOperationalStatus.PLANEJADA:
            raise ConflictError("FREIGHT_TRIP_INVALID_TRANSITION", "Viagem não está PLANEJADA.")

    def interromper(self) -> TripOperationalStatus:
        """Retorna o estado de origem (o Handler grava essa informação só no histórico — não existe
        coluna própria para isso, D377)."""

        if self.status_operacional not in _INTERRUPTIBLE_STATUSES:
            raise ConflictError("FREIGHT_TRIP_INVALID_TRANSITION", "Viagem não pode ser interrompida neste estado.")
        origin_status = self.status_operacional
        self.status_operacional = TripOperationalStatus.INTERROMPIDA
        return origin_status

    def retomar(self, *, previous_status: TripOperationalStatus) -> None:
        """D377 — `previous_status` já resolvido pelo Handler consultando `viagem_status_history`."""

        if self.status_operacional != TripOperationalStatus.INTERROMPIDA:
            raise ConflictError("FREIGHT_TRIP_INVALID_TRANSITION", "Viagem não está INTERROMPIDA.")
        self.status_operacional = previous_status

    def cancelar(self) -> None:
        if self.status_operacional not in _CANCELLABLE_STATUSES:
            raise ConflictError(
                "FREIGHT_TRIP_INVALID_TRANSITION",
                "Viagem não pode ser cancelada neste estado — use commands/interromper primeiro.",
            )
        self.status_operacional = TripOperationalStatus.CANCELADA

    def finish(self) -> None:
        """Pré-condição de Entregas/Canhotos (`FREIGHT_TRIP_DELIVERIES_PENDING`, 422) verificada
        pelo Handler antes de chamar este método — não é uma regra sobre o estado da máquina, D235."""

        if self.status_operacional != TripOperationalStatus.EM_ENTREGA:
            raise ConflictError("FREIGHT_TRIP_INVALID_TRANSITION", "Viagem não está EM_ENTREGA.")
        self.status_operacional = TripOperationalStatus.FINALIZADA

    def close_administrative(self) -> None:
        if self.status_operacional in _TERMINAL_STATUSES:
            raise ConflictError("FREIGHT_TRIP_INVALID_TRANSITION", "Viagem já está em estado terminal.")
        self.status_operacional = TripOperationalStatus.FINALIZADA

    def on_delivery_terminal(self, *, has_pending_deliveries: bool) -> list[TripOperationalStatus]:
        """D237 — efeito colateral controlado pelo Aggregate Root, nunca pelo Controller. Sub-ciclo
        multi-drop (`002-VIAGEM.md`): enquanto houver Entregas `PENDENTE`, a Viagem alterna
        `EM_ENTREGA→EM_TRANSITO→EM_ENTREGA` (comportamento esperado, não uma transição inválida).
        Nunca avança sozinha para `FINALIZADA` — isso é sempre `commands/finish`, explícito."""

        if self.status_operacional != TripOperationalStatus.EM_ENTREGA:
            return []
        if not has_pending_deliveries:
            return []
        return [TripOperationalStatus.EM_TRANSITO, TripOperationalStatus.EM_ENTREGA]

    def update_realized_cost(self, *, value: Decimal) -> None:
        """D390/D392 — chamado por `TripInternalTransitions` a partir de `financial` (Rateio de
        Despesa criado/removido). Nunca um `PATCH` direto em Viagem."""

        self.custo_realizado = value
        self._recompute_realized_margin()

    def update_realized_revenue(self, *, value: Decimal) -> None:
        """D390/D392 — chamado por `TripInternalTransitions` a partir de `financial`
        (`commands/confirm-receipt`)."""

        self.receita_realizada = value
        self._recompute_realized_margin()

    def _recompute_realized_margin(self) -> None:
        """D392 — `margem_realizada`/`desvio_financeiro` recalculados pela Application a cada
        atualização de custo/receita realizado, nunca por trigger de banco (D365-consistent);
        `margem_realizada` só é significativa quando os dois lados já existem, `desvio_financeiro`
        só quando `margem_prevista` (GENERATED) também já está disponível."""

        if self.receita_realizada is not None and self.custo_realizado is not None:
            self.margem_realizada = self.receita_realizada - self.custo_realizado
            if self.margem_prevista is not None:
                self.desvio_financeiro = self.margem_realizada - self.margem_prevista

    def record_fiscal_transition(self, status: TripFiscalStatus) -> None:
        """D375 — simula o futuro consumidor de evento de `documents` (`MDFeEncerrado`, etc.).
        Nunca uma rota HTTP; `viagens.status_fiscal` é sempre `readOnly` no contrato (`018-trip-
        status.md`)."""

        self.status_fiscal = status

    def record_financial_transition(self, status: TripFinancialStatus) -> None:
        """D375 — simula o futuro consumidor de evento de `financial` (`RecebimentoConfirmado`,
        etc.). Nunca uma rota HTTP; `viagens.status_financeiro` é sempre `readOnly`."""

        self.status_financeiro = status
