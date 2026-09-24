from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class CollectionModel(Base):
    """Mapeamento de `coletas` (`relational/003-operacao.md`). `local` (Geography) existe
    fisicamente mas não é mapeado aqui ainda — mesmo gap documentado de `OccurrenceModel`."""

    __tablename__ = "coletas"
    __table_args__ = (Index("idx_coletas_viagem_id", "viagem_id"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    viagem_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("viagens.id"), nullable=False)
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    conferencia_ok: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
