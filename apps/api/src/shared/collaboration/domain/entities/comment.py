from __future__ import annotations

import uuid
from datetime import datetime

from shared_kernel.domain.base_entity import BaseEntity


class Comment(BaseEntity[uuid.UUID]):
    """Implementação física de Comentário (D023/D186) — `comentarios`, infraestrutura
    compartilhada por referência polimórfica (`entidade_tipo`/`entidade_id`). Sem
    `excluido_em`/`excluido_por` — imutável (D371). Sem endpoint HTTP neste lote."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        entidade_tipo: str,
        entidade_id: uuid.UUID,
        usuario_id: uuid.UUID,
        texto: str,
        visivel_cliente: bool,
        criado_em: datetime,
    ) -> None:
        super().__init__(id)
        self.entidade_tipo = entidade_tipo
        self.entidade_id = entidade_id
        self.usuario_id = usuario_id
        self.texto = texto
        self.visivel_cliente = visivel_cliente
        self.criado_em = criado_em

    @classmethod
    def create(
        cls,
        *,
        entidade_tipo: str,
        entidade_id: uuid.UUID,
        usuario_id: uuid.UUID,
        texto: str,
        visivel_cliente: bool,
        now: datetime,
    ) -> "Comment":
        return cls(
            id=uuid.uuid4(),
            entidade_tipo=entidade_tipo,
            entidade_id=entidade_id,
            usuario_id=usuario_id,
            texto=texto,
            visivel_cliente=visivel_cliente,
            criado_em=now,
        )

    def update_text(self, *, texto: str | None, visivel_cliente: bool | None) -> None:
        """`081-comments.md` — D229 parcial. Autoria (`usuario_id`) checada pelo Handler chamador,
        nunca aqui (esta entidade não conhece o ator da requisição)."""

        if texto is not None:
            self.texto = texto
        if visivel_cliente is not None:
            self.visivel_cliente = visivel_cliente
