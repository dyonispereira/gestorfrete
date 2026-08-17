from __future__ import annotations

import uuid
from datetime import datetime

from core.exceptions.base import ConflictError
from modules.documents.domain.value_objects.ciot_status import CiotStatus
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot

_TRANSICOES_VALIDAS: dict[CiotStatus, frozenset[CiotStatus]] = {
    CiotStatus.PENDENTE: frozenset({CiotStatus.REGISTRADO, CiotStatus.CANCELADO}),
    CiotStatus.REGISTRADO: frozenset({CiotStatus.CANCELADO}),
}


class Ciot(BaseAggregateRoot[uuid.UUID]):
    """`ciots` — Aggregate Root de `documents`. Aplicável só a Motorista `AUTONOMO`. D109 — nunca
    excluído fisicamente. D400 — sem `audit` (DDL congelada não tem nenhuma coluna de timestamp)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        viagem_id: uuid.UUID,
        motorista_id: uuid.UUID,
        codigo_ciot: str | None,
        status: CiotStatus,
        protocolo_antt: str | None,
        data_hora_registro: datetime | None,
    ) -> None:
        super().__init__(id)
        self.viagem_id = viagem_id
        self.motorista_id = motorista_id
        self.codigo_ciot = codigo_ciot
        self.status = status
        self.protocolo_antt = protocolo_antt
        self.data_hora_registro = data_hora_registro

    @classmethod
    def create(cls, *, viagem_id: uuid.UUID, motorista_id: uuid.UUID) -> "Ciot":
        return cls(
            id=uuid.uuid4(), viagem_id=viagem_id, motorista_id=motorista_id, codigo_ciot=None,
            status=CiotStatus.PENDENTE, protocolo_antt=None, data_hora_registro=None,
        )

    def _transition(self, to: CiotStatus) -> None:
        if to not in _TRANSICOES_VALIDAS.get(self.status, frozenset()):
            raise ConflictError(
                "FISCAL_CIOT_INVALID_TRANSITION", f"CIOT não pode ir de {self.status.value} para {to.value}."
            )
        self.status = to

    def register(self, *, codigo_ciot: str, protocolo_antt: str, now: datetime) -> None:
        self._transition(CiotStatus.REGISTRADO)
        self.codigo_ciot = codigo_ciot
        self.protocolo_antt = protocolo_antt
        self.data_hora_registro = now

    def cancel(self) -> None:
        self._transition(CiotStatus.CANCELADO)
