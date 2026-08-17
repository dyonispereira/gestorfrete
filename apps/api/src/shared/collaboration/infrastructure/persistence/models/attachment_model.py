from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class AttachmentModel(Base):
    """Mapeamento de `anexos` (D024/D186, `relational/003-operacao.md`). Sem
    `excluido_em`/`excluido_por` — imutável (D371)."""

    __tablename__ = "anexos"
    __table_args__ = (Index("idx_anexos_entidade_tipo_entidade_id", "entidade_tipo", "entidade_id"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    entidade_tipo: Mapped[str] = mapped_column(String, nullable=False)
    entidade_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    tipo_anexo: Mapped[str] = mapped_column(String, nullable=False)
    arquivo_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    descricao: Mapped[str | None] = mapped_column(String)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    criado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
