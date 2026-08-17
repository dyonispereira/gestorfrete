from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class AISuggestionModel(Base):
    """`sugestoes_ia` (`relational/012-ia.md`) — D310, produto derivado da Inferência."""

    __tablename__ = "sugestoes_ia"
    __table_args__ = (
        Index("idx_sugestoes_ia_entidade_alvo", "entidade_alvo_tipo", "entidade_alvo_id"),
        Index("idx_sugestoes_ia_status", "tenant_id", "status"),
        Index("idx_sugestoes_ia_usuario_decisao_id", "usuario_decisao_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    inferencia_ia_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    categoria: Mapped[str] = mapped_column(String, nullable=False)
    entidade_alvo_tipo: Mapped[str] = mapped_column(String, nullable=False)
    entidade_alvo_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    recomendacao: Mapped[str] = mapped_column(String, nullable=False)
    justificativa: Mapped[str] = mapped_column(String, nullable=False)
    nivel_confianca: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="PENDENTE")
    usuario_decisao_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id"))
    data_hora_decisao: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
