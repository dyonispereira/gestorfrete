from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class AnalyticsCubeModel(Base):
    """Mapeamento de `cubos_analiticos` (`relational/011-bi.md`)."""

    __tablename__ = "cubos_analiticos"
    __table_args__ = (UniqueConstraint("tenant_id", "nome", name="uq_cubos_analiticos_tenant_id_nome"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    dimensoes: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ATIVO")


class AnalyticsCubeMetricModel(Base):
    """Mapeamento de `cubos_analiticos_metricas`."""

    __tablename__ = "cubos_analiticos_metricas"

    cubo_analitico_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("cubos_analiticos.id"), primary_key=True
    )
    metrica_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("metricas.id"), primary_key=True)
