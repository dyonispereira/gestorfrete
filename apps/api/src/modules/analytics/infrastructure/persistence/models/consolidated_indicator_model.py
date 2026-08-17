from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class ConsolidatedIndicatorModel(Base):
    """Mapeamento de `indicadores_consolidados` (`relational/011-bi.md`)."""

    __tablename__ = "indicadores_consolidados"
    __table_args__ = (
        Index(
            "idx_indicadores_consolidados_metrica_dimensao", "metrica_id", "dimensao_tipo", "dimensao_id",
            "periodo_referencia",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    metrica_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("metricas.id"), nullable=False)
    metrica_versao: Mapped[int] = mapped_column(nullable=False)
    dimensao_tipo: Mapped[str] = mapped_column(String, nullable=False)
    dimensao_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    periodo_referencia: Mapped[str] = mapped_column(String, nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    data_hora_calculo: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="VALIDO")
