from __future__ import annotations

import uuid
from typing import Any

from modules.reporting.domain.value_objects.output_format import OutputFormat
from shared_kernel.domain.base_entity import BaseEntity


class SavedReport(BaseEntity[uuid.UUID]):
    """`relatorios_salvos` — só a definição, nunca a query física nem o conteúdo gerado (isso é
    `Export`). `DELETE` = `status=ARQUIVADO` (D422)."""

    def __init__(
        self, id: uuid.UUID, *, usuario_id: uuid.UUID, nome: str, metricas_ids: list[uuid.UUID],
        filtros: dict[str, Any] | None, formato_saida: OutputFormat, status: str,
    ) -> None:
        super().__init__(id)
        self.usuario_id = usuario_id
        self.nome = nome
        self.metricas_ids = metricas_ids
        self.filtros = filtros
        self.formato_saida = formato_saida
        self.status = status

    @classmethod
    def create(
        cls, *, usuario_id: uuid.UUID, nome: str, metricas_ids: list[uuid.UUID], filtros: dict[str, Any] | None,
        formato_saida: OutputFormat,
    ) -> "SavedReport":
        return cls(
            id=uuid.uuid4(), usuario_id=usuario_id, nome=nome, metricas_ids=metricas_ids, filtros=filtros,
            formato_saida=formato_saida, status="ATIVO",
        )

    def update(
        self, *, nome: str | None, metricas_ids: list[uuid.UUID] | None, filtros: dict[str, Any] | None,
        formato_saida: OutputFormat | None, status: str | None,
    ) -> None:
        if nome is not None:
            self.nome = nome
        if metricas_ids is not None:
            self.metricas_ids = metricas_ids
        if filtros is not None:
            self.filtros = filtros
        if formato_saida is not None:
            self.formato_saida = formato_saida
        if status is not None:
            self.status = status

    def archive(self) -> None:
        self.status = "ARQUIVADO"
