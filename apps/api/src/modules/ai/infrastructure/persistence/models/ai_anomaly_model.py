from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class AIAnomalyModel(Base):
    """`anomalias_detectadas` (`relational/012-ia.md`). `inferencia_ia_id` sem FK física — mesmo
    motivo de `AIPredictionModel` (D202-style, `inferencias_ia` particionada não pode ser alvo de
    `UNIQUE(id)` isolado)."""

    __tablename__ = "anomalias_detectadas"
    __table_args__ = (Index("idx_anomalias_detectadas_leitura_origem", "leitura_origem_tipo", "leitura_origem_id"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    inferencia_ia_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    leitura_origem_tipo: Mapped[str] = mapped_column(String, nullable=False)
    leitura_origem_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    nivel_confianca: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ABERTA")
