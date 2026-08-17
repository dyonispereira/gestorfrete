from __future__ import annotations

import uuid

from shared_kernel.domain.base_entity import BaseEntity


class AnalyticsCube(BaseEntity[uuid.UUID]):
    """`cubos_analiticos` — só a definição estrutural (D065-lote instrução), nenhum dado
    materializado. `metricas_ids` vive na tabela de junção `cubos_analiticos_metricas`."""

    def __init__(
        self, id: uuid.UUID, *, tenant_id: uuid.UUID, nome: str, dimensoes: list[str],
        metricas_ids: list[uuid.UUID], status: str,
    ) -> None:
        super().__init__(id)
        self.tenant_id = tenant_id
        self.nome = nome
        self.dimensoes = dimensoes
        self.metricas_ids = metricas_ids
        self.status = status

    @classmethod
    def create(
        cls, *, tenant_id: uuid.UUID, nome: str, dimensoes: list[str], metricas_ids: list[uuid.UUID]
    ) -> "AnalyticsCube":
        return cls(id=uuid.uuid4(), tenant_id=tenant_id, nome=nome, dimensoes=dimensoes, metricas_ids=metricas_ids, status="ATIVO")

    def update(
        self, *, dimensoes: list[str] | None, metricas_ids: list[uuid.UUID] | None, status: str | None
    ) -> None:
        if dimensoes is not None:
            self.dimensoes = dimensoes
        if metricas_ids is not None:
            self.metricas_ids = metricas_ids
        if status is not None:
            self.status = status
