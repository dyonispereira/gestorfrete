from __future__ import annotations

import uuid
from typing import Any

from shared_kernel.domain.base_entity import BaseEntity


class SavedFilter(BaseEntity[uuid.UUID]):
    """`filtros_favoritos` — sempre pessoal, nunca guarda o resultado, só o critério. `DELETE` =
    `status=ARQUIVADO` (D422, sem `excluido_em` na DDL)."""

    def __init__(
        self, id: uuid.UUID, *, usuario_id: uuid.UUID, nome: str, criterios: dict[str, Any], status: str
    ) -> None:
        super().__init__(id)
        self.usuario_id = usuario_id
        self.nome = nome
        self.criterios = criterios
        self.status = status

    @classmethod
    def create(cls, *, usuario_id: uuid.UUID, nome: str, criterios: dict[str, Any]) -> "SavedFilter":
        return cls(id=uuid.uuid4(), usuario_id=usuario_id, nome=nome, criterios=criterios, status="ATIVO")

    def update(self, *, nome: str | None, criterios: dict[str, Any] | None, status: str | None) -> None:
        if nome is not None:
            self.nome = nome
        if criterios is not None:
            self.criterios = criterios
        if status is not None:
            self.status = status

    def archive(self) -> None:
        self.status = "ARQUIVADO"
