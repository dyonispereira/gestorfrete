from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class LogAuditoriaModel(Base):
    """Mapeamento de `logs_auditoria` (`docs/database/relational/010-administracao.md`).

    A PK física é composta `(id, data_hora)`, não `id` sozinho — achado real deste lote (Sprint 11,
    Lote 2): a tabela é `PARTITION BY RANGE (data_hora)`, e o PostgreSQL exige que toda chave
    única/primária de uma tabela particionada inclua a coluna de particionamento. A documentação
    original (`relational/010-administracao.md`) declarava só `id UUID PRIMARY KEY`, nunca validado
    contra um PostgreSQL real antes deste lote — `CREATE TABLE` falha com esse desenho. Corrigido
    aqui e na migration; `relational/010-administracao.md` marcado para correção (ver
    `docs/backend/core/README.md`, achado do Lote 2).
    """

    __tablename__ = "logs_auditoria"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    entidade_tipo: Mapped[str] = mapped_column(String, nullable=False)
    entidade_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    acao: Mapped[str] = mapped_column(String, nullable=False)
    ator_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    ator_nome_snapshot: Mapped[str] = mapped_column(String, nullable=False)
    origem: Mapped[str] = mapped_column(String, nullable=False)
    dados_antes: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    dados_depois: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    motivo: Mapped[str | None] = mapped_column(String)
    id_correlacao: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
