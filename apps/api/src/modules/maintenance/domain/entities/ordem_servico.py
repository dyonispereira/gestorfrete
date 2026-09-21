from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from core.exceptions.base import ConflictError, DomainError
from modules.maintenance.domain.value_objects.ordem_servico_causa import OrdemServicoCausa
from modules.maintenance.domain.value_objects.ordem_servico_origem_abertura import OrdemServicoOrigemAbertura
from modules.maintenance.domain.value_objects.ordem_servico_status import OrdemServicoStatus
from modules.maintenance.domain.value_objects.ordem_servico_tipo import OrdemServicoTipo
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot

_TRANSICOES_VALIDAS: dict[OrdemServicoStatus, frozenset[OrdemServicoStatus]] = {
    OrdemServicoStatus.ABERTA: frozenset({OrdemServicoStatus.EM_DIAGNOSTICO, OrdemServicoStatus.CANCELADA}),
    OrdemServicoStatus.EM_DIAGNOSTICO: frozenset({
        OrdemServicoStatus.AGUARDANDO_APROVACAO, OrdemServicoStatus.EM_EXECUCAO, OrdemServicoStatus.CANCELADA,
    }),
    OrdemServicoStatus.AGUARDANDO_APROVACAO: frozenset({
        OrdemServicoStatus.EM_DIAGNOSTICO, OrdemServicoStatus.EM_EXECUCAO, OrdemServicoStatus.CANCELADA,
    }),
    OrdemServicoStatus.EM_EXECUCAO: frozenset({OrdemServicoStatus.CONCLUIDA}),
    OrdemServicoStatus.CONCLUIDA: frozenset({OrdemServicoStatus.FECHADA}),
}


class OrdemServico(BaseAggregateRoot[uuid.UUID]):
    """`ordens_servico` — Aggregate Root de `maintenance` (`003-MANUTENCAO.md`).
    `centro_custo_id`/`plano_contas_id` são opcionais (Lote Financeiro, Parte 1) — quando ambos e
    `fornecedor_executor_id` estão presentes no fechamento, habilitam a Conta a Pagar automática
    (`006-financeiro.md`); OS sem os três segue fechando normalmente, só sem gerar a Conta a Pagar
    sozinha. `FECHADA` nunca é
    reaberta — uma recorrência sempre gera uma nova OS referenciando o veículo, nunca reabre esta
    (mesmo princípio de D017/D018 já aplicado a Trip/Cte/Checklist). `AGUARDANDO_PECA` existe no
    enum mas não é alcançável nesta Lote — depende do subsistema de peças, deliberadamente fora de
    escopo (ver plano). `custo_previsto`/`custo_realizado` nunca são digitados pelo usuário — são
    recalculados pela Application a partir de `itens_ordem_servico` (D086, não é coluna `GENERATED`
    porque depende de outra tabela)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        codigo: str,
        veiculo_tracionador_id: uuid.UUID,
        composicao_veicular_id: uuid.UUID | None,
        fornecedor_executor_id: uuid.UUID | None,
        tipo: OrdemServicoTipo,
        origem_abertura: OrdemServicoOrigemAbertura,
        descricao_problema: str,
        causa: OrdemServicoCausa | None,
        causa_raiz: str | None,
        diagnostico_tecnico: str | None,
        mecanico_id: uuid.UUID | None,
        custo_previsto: Decimal | None,
        custo_realizado: Decimal | None,
        necessita_aprovacao: bool,
        evidencia_conclusao_exigida: bool,
        status: OrdemServicoStatus,
        data_inicio_execucao: datetime | None,
        data_conclusao: datetime | None,
        hodometro_abertura_km: Decimal | None,
        hodometro_conclusao_km: Decimal | None,
        centro_custo_id: uuid.UUID | None,
        plano_contas_id: uuid.UUID | None,
        criado_em: datetime,
        criado_por: uuid.UUID | None,
        atualizado_em: datetime,
        atualizado_por: uuid.UUID | None,
    ) -> None:
        super().__init__(id)
        self.codigo = codigo
        self.veiculo_tracionador_id = veiculo_tracionador_id
        self.composicao_veicular_id = composicao_veicular_id
        self.fornecedor_executor_id = fornecedor_executor_id
        self.tipo = tipo
        self.origem_abertura = origem_abertura
        self.descricao_problema = descricao_problema
        self.causa = causa
        self.causa_raiz = causa_raiz
        self.diagnostico_tecnico = diagnostico_tecnico
        self.mecanico_id = mecanico_id
        self.custo_previsto = custo_previsto
        self.custo_realizado = custo_realizado
        self.necessita_aprovacao = necessita_aprovacao
        self.evidencia_conclusao_exigida = evidencia_conclusao_exigida
        self.status = status
        self.data_inicio_execucao = data_inicio_execucao
        self.data_conclusao = data_conclusao
        self.hodometro_abertura_km = hodometro_abertura_km
        self.hodometro_conclusao_km = hodometro_conclusao_km
        self.centro_custo_id = centro_custo_id
        self.plano_contas_id = plano_contas_id
        self.criado_em = criado_em
        self.criado_por = criado_por
        self.atualizado_em = atualizado_em
        self.atualizado_por = atualizado_por

    @classmethod
    def create(
        cls,
        *,
        veiculo_tracionador_id: uuid.UUID,
        composicao_veicular_id: uuid.UUID | None,
        fornecedor_executor_id: uuid.UUID | None,
        tipo: OrdemServicoTipo,
        origem_abertura: OrdemServicoOrigemAbertura,
        descricao_problema: str,
        hodometro_abertura_km: Decimal | None,
        centro_custo_id: uuid.UUID | None,
        plano_contas_id: uuid.UUID | None,
        criado_por: uuid.UUID | None,
        now: datetime,
    ) -> "OrdemServico":
        codigo = f"OS-{now.year}-{uuid.uuid4().hex[:6].upper()}"
        return cls(
            id=uuid.uuid4(), codigo=codigo, veiculo_tracionador_id=veiculo_tracionador_id,
            composicao_veicular_id=composicao_veicular_id, fornecedor_executor_id=fornecedor_executor_id,
            tipo=tipo, origem_abertura=origem_abertura, descricao_problema=descricao_problema, causa=None,
            causa_raiz=None, diagnostico_tecnico=None, mecanico_id=None, custo_previsto=None,
            custo_realizado=None, necessita_aprovacao=False, evidencia_conclusao_exigida=False,
            status=OrdemServicoStatus.ABERTA, data_inicio_execucao=None, data_conclusao=None,
            hodometro_abertura_km=hodometro_abertura_km, hodometro_conclusao_km=None,
            centro_custo_id=centro_custo_id, plano_contas_id=plano_contas_id, criado_em=now,
            criado_por=criado_por, atualizado_em=now, atualizado_por=criado_por,
        )

    def _transition(self, to: OrdemServicoStatus, *, now: datetime, atualizado_por: uuid.UUID | None) -> None:
        if to not in _TRANSICOES_VALIDAS.get(self.status, frozenset()):
            raise ConflictError(
                "MAINTENANCE_WORK_ORDER_INVALID_TRANSITION",
                f"Ordem de Serviço não pode ir de {self.status.value} para {to.value}.",
            )
        self.status = to
        self.atualizado_em = now
        self.atualizado_por = atualizado_por

    def diagnosticar(
        self, *, causa: OrdemServicoCausa | None, causa_raiz: str | None, diagnostico_tecnico: str | None,
        mecanico_id: uuid.UUID | None, necessita_aprovacao: bool, now: datetime, atualizado_por: uuid.UUID | None,
    ) -> None:
        if causa is not None and self.tipo is not OrdemServicoTipo.CORRETIVA:
            raise DomainError(
                "MAINTENANCE_WORK_ORDER_CAUSA_SO_CORRETIVA", "Causa só se aplica a Ordem de Serviço Corretiva."
            )
        self.causa = causa
        self.causa_raiz = causa_raiz
        self.diagnostico_tecnico = diagnostico_tecnico
        self.mecanico_id = mecanico_id
        self.necessita_aprovacao = necessita_aprovacao
        self._transition(OrdemServicoStatus.EM_DIAGNOSTICO, now=now, atualizado_por=atualizado_por)

    def submeter_aprovacao(self, *, now: datetime, atualizado_por: uuid.UUID | None) -> None:
        self._transition(OrdemServicoStatus.AGUARDANDO_APROVACAO, now=now, atualizado_por=atualizado_por)

    def aprovar_custo(self, *, now: datetime, atualizado_por: uuid.UUID | None) -> None:
        self._transition(OrdemServicoStatus.EM_EXECUCAO, now=now, atualizado_por=atualizado_por)
        self.data_inicio_execucao = now

    def reprovar_custo(self, *, now: datetime, atualizado_por: uuid.UUID | None) -> None:
        self._transition(OrdemServicoStatus.EM_DIAGNOSTICO, now=now, atualizado_por=atualizado_por)

    def iniciar_execucao(self, *, now: datetime, atualizado_por: uuid.UUID | None) -> None:
        self._transition(OrdemServicoStatus.EM_EXECUCAO, now=now, atualizado_por=atualizado_por)
        self.data_inicio_execucao = now

    def concluir(self, *, hodometro_km: Decimal | None, now: datetime, atualizado_por: uuid.UUID | None) -> None:
        self._transition(OrdemServicoStatus.CONCLUIDA, now=now, atualizado_por=atualizado_por)
        self.data_conclusao = now
        self.hodometro_conclusao_km = hodometro_km

    def fechar(self, *, now: datetime, atualizado_por: uuid.UUID | None) -> None:
        self._transition(OrdemServicoStatus.FECHADA, now=now, atualizado_por=atualizado_por)

    def cancelar(self, *, now: datetime, atualizado_por: uuid.UUID | None) -> None:
        self._transition(OrdemServicoStatus.CANCELADA, now=now, atualizado_por=atualizado_por)

    def recompute_custo_previsto(self, *, value: Decimal) -> None:
        self.custo_previsto = value

    def recompute_custo_realizado(self, *, value: Decimal) -> None:
        self.custo_realizado = value
