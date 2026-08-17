from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class OccurrenceModel(Base):
    """Mapeamento de `ocorrencias` (`relational/003-operacao.md`) — genérica por design (D076),
    sem colunas de `latitude`/`longitude` (`017-trip-occurrences.md`, lacuna conhecida)."""

    __tablename__ = "ocorrencias"
    __table_args__ = (
        Index("idx_ocorrencias_viagem_id", "viagem_id"),
        Index("idx_ocorrencias_tenant_id_tipo", "tenant_id", "tipo"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    viagem_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("viagens.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    descricao: Mapped[str] = mapped_column(String, nullable=False)
    gravidade: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ABERTA")
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
