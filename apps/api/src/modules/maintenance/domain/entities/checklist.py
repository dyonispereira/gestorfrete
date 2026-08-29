from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from core.exceptions.base import ConflictError, DomainError
from modules.maintenance.domain.value_objects.checklist_referencia_tipo import ChecklistReferenciaTipo
from modules.maintenance.domain.value_objects.checklist_status import ChecklistStatus
from modules.maintenance.domain.value_objects.checklist_type import ChecklistType
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot

_TRANSICOES_VALIDAS: dict[ChecklistStatus, frozenset[ChecklistStatus]] = {
    ChecklistStatus.PENDENTE: frozenset({ChecklistStatus.EM_PREENCHIMENTO}),
    ChecklistStatus.EM_PREENCHIMENTO: frozenset({ChecklistStatus.CONCLUIDO}),
    ChecklistStatus.CONCLUIDO: frozenset({ChecklistStatus.APROVADO, ChecklistStatus.REPROVADO}),
}


class Checklist(BaseAggregateRoot[uuid.UUID]):
    """`checklists` — Aggregate Root de `maintenance` (`007-CHECKLIST.md`, formalizado em
    `domain/004-manutencao.md` para desbloquear `Trip.AGUARDANDO_CHECKLIST → LIBERADA`). Um
    `Aprovado`/`Reprovado` nunca é reaberto — uma reprovação sempre gera um novo registro
    `Pendente` (feito pelo Handler, não por este método, que só marca REPROVADO)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        codigo: str,
        tipo: ChecklistType,
        referencia_tipo: ChecklistReferenciaTipo,
        referencia_id: uuid.UUID,
        veiculo_tracionador_id: uuid.UUID,
        motorista_id: uuid.UUID | None,
        itens: list[dict[str, Any]],
        status: ChecklistStatus,
        checklist_reprovado_id: uuid.UUID | None,
        criado_em: datetime,
        atualizado_em: datetime,
    ) -> None:
        super().__init__(id)
        self.codigo = codigo
        self.tipo = tipo
        self.referencia_tipo = referencia_tipo
        self.referencia_id = referencia_id
        self.veiculo_tracionador_id = veiculo_tracionador_id
        self.motorista_id = motorista_id
        self.itens = itens
        self.status = status
        self.checklist_reprovado_id = checklist_reprovado_id
        self.criado_em = criado_em
        self.atualizado_em = atualizado_em

    @classmethod
    def create(
        cls,
        *,
        tipo: ChecklistType,
        referencia_tipo: ChecklistReferenciaTipo,
        referencia_id: uuid.UUID,
        veiculo_tracionador_id: uuid.UUID,
        motorista_id: uuid.UUID | None,
        now: datetime,
        checklist_reprovado_id: uuid.UUID | None = None,
    ) -> "Checklist":
        codigo = f"CL-{now.year}-{uuid.uuid4().hex[:6].upper()}"
        return cls(
            id=uuid.uuid4(), codigo=codigo, tipo=tipo, referencia_tipo=referencia_tipo,
            referencia_id=referencia_id, veiculo_tracionador_id=veiculo_tracionador_id,
            motorista_id=motorista_id, itens=[], status=ChecklistStatus.PENDENTE,
            checklist_reprovado_id=checklist_reprovado_id, criado_em=now, atualizado_em=now,
        )

    def _transition(self, to: ChecklistStatus, *, now: datetime) -> None:
        if to not in _TRANSICOES_VALIDAS.get(self.status, frozenset()):
            raise ConflictError(
                "MAINTENANCE_CHECKLIST_INVALID_TRANSITION",
                f"Checklist não pode ir de {self.status.value} para {to.value}.",
            )
        self.status = to
        self.atualizado_em = now

    def start(self, *, now: datetime) -> None:
        self._transition(ChecklistStatus.EM_PREENCHIMENTO, now=now)

    def submit(self, *, itens: list[dict[str, Any]], now: datetime) -> None:
        if not itens:
            raise DomainError(
                "MAINTENANCE_CHECKLIST_ITEMS_REQUIRED", "Todo item precisa ser respondido antes de concluir."
            )
        for item in itens:
            if item.get("resposta") is None:
                raise DomainError(
                    "MAINTENANCE_CHECKLIST_ITEMS_REQUIRED", "Todo item precisa ser respondido antes de concluir."
                )
        self.itens = itens
        self._transition(ChecklistStatus.CONCLUIDO, now=now)

    def approve(self, *, now: datetime) -> None:
        self._transition(ChecklistStatus.APROVADO, now=now)

    def reject(self, *, now: datetime) -> None:
        self._transition(ChecklistStatus.REPROVADO, now=now)
