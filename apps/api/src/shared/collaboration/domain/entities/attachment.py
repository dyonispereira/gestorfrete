from __future__ import annotations

import uuid
from datetime import datetime

from shared_kernel.domain.base_entity import BaseEntity


class Attachment(BaseEntity[uuid.UUID]):
    """Implementação física de Anexo (D024/D186) — `anexos`, infraestrutura compartilhada por
    referência polimórfica (`entidade_tipo`/`entidade_id`), nunca uma tabela própria por
    consumidor. Sem `excluido_em`/`excluido_por` (D371) — nunca editado, `DELETE` é hard delete real
    (`080-attachments.md`, Lote 10) em vez de soft delete."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        entidade_tipo: str,
        entidade_id: uuid.UUID,
        tipo_anexo: str,
        arquivo_id: uuid.UUID,
        descricao: str | None,
        criado_em: datetime,
        criado_por: uuid.UUID | None,
    ) -> None:
        super().__init__(id)
        self.entidade_tipo = entidade_tipo
        self.entidade_id = entidade_id
        self.tipo_anexo = tipo_anexo
        self.arquivo_id = arquivo_id
        self.descricao = descricao
        self.criado_em = criado_em
        self.criado_por = criado_por

    @classmethod
    def create(
        cls,
        *,
        entidade_tipo: str,
        entidade_id: uuid.UUID,
        tipo_anexo: str,
        arquivo_id: uuid.UUID,
        descricao: str | None,
        now: datetime,
        created_by: uuid.UUID | None,
    ) -> "Attachment":
        return cls(
            id=uuid.uuid4(),
            entidade_tipo=entidade_tipo,
            entidade_id=entidade_id,
            tipo_anexo=tipo_anexo,
            arquivo_id=arquivo_id,
            descricao=descricao,
            criado_em=now,
            criado_por=created_by,
        )
