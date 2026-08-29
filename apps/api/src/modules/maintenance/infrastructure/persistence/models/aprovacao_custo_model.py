from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class AprovacaoCustoModel(Base):
    """Mapeamento de `aprovacoes_custo` — registro pontual, nunca alterado depois de criado."""

    __tablename__ = "aprovacoes_custo"
    __table_args__ = (Index("idx_aprovacoes_custo_ordem_servico_id", "ordem_servico_id", "nivel"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    ordem_servico_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ordens_servico.id"), nullable=False
    )
    nivel: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    decisao: Mapped[str] = mapped_column(String, nullable=False)
    justificativa: Mapped[str | None] = mapped_column(String)
    ator_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
