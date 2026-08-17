from __future__ import annotations

import uuid
from datetime import datetime

from core.exceptions.base import ConflictError
from modules.documents.domain.value_objects.mdfe_status import MdfeStatus
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot

_TRANSICOES_VALIDAS: dict[MdfeStatus, frozenset[MdfeStatus]] = {
    MdfeStatus.PENDENTE: frozenset({MdfeStatus.AUTORIZADO, MdfeStatus.CANCELADO}),
    MdfeStatus.AUTORIZADO: frozenset({MdfeStatus.ENCERRADO, MdfeStatus.CANCELADO}),
}


class Mdfe(BaseAggregateRoot[uuid.UUID]):
    """`mdfes` — Aggregate Root de `documents`. D109 — nunca excluído fisicamente. D400 — sem
    `audit` (DDL congelada não tem nenhuma coluna de timestamp)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        viagem_id: uuid.UUID,
        numero: str,
        serie: str,
        chave_acesso: str | None,
        status: MdfeStatus,
        xml_arquivo_id: uuid.UUID | None,
        protocolo_sefaz: str | None,
        data_hora_encerramento: datetime | None,
    ) -> None:
        super().__init__(id)
        self.viagem_id = viagem_id
        self.numero = numero
        self.serie = serie
        self.chave_acesso = chave_acesso
        self.status = status
        self.xml_arquivo_id = xml_arquivo_id
        self.protocolo_sefaz = protocolo_sefaz
        self.data_hora_encerramento = data_hora_encerramento

    @classmethod
    def create(cls, *, viagem_id: uuid.UUID, numero: str, serie: str) -> "Mdfe":
        return cls(
            id=uuid.uuid4(), viagem_id=viagem_id, numero=numero, serie=serie, chave_acesso=None,
            status=MdfeStatus.PENDENTE, xml_arquivo_id=None, protocolo_sefaz=None,
            data_hora_encerramento=None,
        )

    def _transition(self, to: MdfeStatus) -> None:
        if to not in _TRANSICOES_VALIDAS.get(self.status, frozenset()):
            raise ConflictError(
                "FISCAL_MDFE_INVALID_TRANSITION", f"MDF-e não pode ir de {self.status.value} para {to.value}."
            )
        self.status = to

    def authorize(self, *, protocolo_sefaz: str, chave_acesso: str, xml_arquivo_id: uuid.UUID | None) -> None:
        self._transition(MdfeStatus.AUTORIZADO)
        self.protocolo_sefaz = protocolo_sefaz
        self.chave_acesso = chave_acesso
        self.xml_arquivo_id = xml_arquivo_id

    def close(self, *, now: datetime) -> None:
        self._transition(MdfeStatus.ENCERRADO)
        self.data_hora_encerramento = now

    def cancel(self) -> None:
        self._transition(MdfeStatus.CANCELADO)
