from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from core.exceptions.base import ConflictError
from modules.documents.domain.value_objects.cte_status import CteStatus
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot

_TRANSICOES_VALIDAS: dict[CteStatus, frozenset[CteStatus]] = {
    CteStatus.RASCUNHO: frozenset({CteStatus.VALIDADO, CteStatus.INUTILIZADO}),
    CteStatus.VALIDADO: frozenset({CteStatus.ASSINADO, CteStatus.INUTILIZADO}),
    CteStatus.ASSINADO: frozenset({CteStatus.TRANSMITIDO}),
    CteStatus.TRANSMITIDO: frozenset({CteStatus.AUTORIZADO, CteStatus.DENEGADO}),
    CteStatus.AUTORIZADO: frozenset({CteStatus.CANCELADO}),
}


class Cte(BaseAggregateRoot[uuid.UUID]):
    """`ctes` — Aggregate Root de `documents` (D106: máquina própria, mais granular que `Trip.
    status_fiscal`). D109 — nunca excluído fisicamente, sem `soft_delete()`. D400 — `audit` só
    parcial (`criado_em`/`atualizado_em`; sem `criado_por`/`atualizado_por` na DDL congelada)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        viagem_id: uuid.UUID,
        numero: str,
        serie: str,
        chave_acesso: str | None,
        valor_servico: Decimal,
        status: CteStatus,
        xml_arquivo_id: uuid.UUID | None,
        protocolo_sefaz: str | None,
        data_hora_autorizacao: datetime | None,
        criado_em: datetime,
        atualizado_em: datetime,
    ) -> None:
        super().__init__(id)
        self.viagem_id = viagem_id
        self.numero = numero
        self.serie = serie
        self.chave_acesso = chave_acesso
        self.valor_servico = valor_servico
        self.status = status
        self.xml_arquivo_id = xml_arquivo_id
        self.protocolo_sefaz = protocolo_sefaz
        self.data_hora_autorizacao = data_hora_autorizacao
        self.criado_em = criado_em
        self.atualizado_em = atualizado_em

    @classmethod
    def create(
        cls, *, viagem_id: uuid.UUID, numero: str, serie: str, valor_servico: Decimal, now: datetime
    ) -> "Cte":
        return cls(
            id=uuid.uuid4(), viagem_id=viagem_id, numero=numero, serie=serie, chave_acesso=None,
            valor_servico=valor_servico, status=CteStatus.RASCUNHO, xml_arquivo_id=None,
            protocolo_sefaz=None, data_hora_autorizacao=None, criado_em=now, atualizado_em=now,
        )

    def _transition(self, to: CteStatus, *, now: datetime) -> None:
        if to not in _TRANSICOES_VALIDAS.get(self.status, frozenset()):
            raise ConflictError("FISCAL_CTE_INVALID_TRANSITION", f"CT-e não pode ir de {self.status.value} para {to.value}.")
        self.status = to
        self.atualizado_em = now

    def validate(self, *, now: datetime) -> None:
        """`RASCUNHO→VALIDADO` — confere dados obrigatórios contra o schema XML da SEFAZ (validação
        estrutural, `039-cte.md`). Nunca exige `valor_servico > 0`: essa é a captura comum nesta
        fundação (`Trip.receita_prevista_snapshot` ainda não preenchido, Cotação/Programação da
        Viagem fora de escopo, D262) — inventar essa regra aqui bloquearia o fluxo inteiro no caso
        mais comum."""

        self._transition(CteStatus.VALIDADO, now=now)

    def sign(self, *, now: datetime) -> None:
        self._transition(CteStatus.ASSINADO, now=now)

    def transmit(self, *, now: datetime) -> None:
        self._transition(CteStatus.TRANSMITIDO, now=now)

    def authorize(
        self, *, protocolo_sefaz: str, chave_acesso: str, xml_arquivo_id: uuid.UUID | None, now: datetime
    ) -> None:
        self._transition(CteStatus.AUTORIZADO, now=now)
        self.protocolo_sefaz = protocolo_sefaz
        self.chave_acesso = chave_acesso
        self.xml_arquivo_id = xml_arquivo_id
        self.data_hora_autorizacao = now

    def deny(self, *, protocolo_sefaz: str, now: datetime) -> None:
        self._transition(CteStatus.DENEGADO, now=now)
        self.protocolo_sefaz = protocolo_sefaz

    def cancel(self, *, now: datetime) -> None:
        self._transition(CteStatus.CANCELADO, now=now)

    def inutilize(self, *, now: datetime) -> None:
        self._transition(CteStatus.INUTILIZADO, now=now)
