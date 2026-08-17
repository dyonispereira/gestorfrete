from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class AnalyticalSnapshotModel(Base):
    """Mapeamento de `snapshots_analiticos` (D151, `relational/011-bi.md`). D160 — "quais Métricas
    participaram" nunca é uma coluna própria: a DDL congelada resolve isso via junção com
    `snapshots_analiticos_indicadores` → `indicadores_consolidados` (`metrica_id`/`metrica_versao`
    de cada indicador incluído), nunca um JSONB redundante armazenando o que já está derivável."""

    __tablename__ = "snapshots_analiticos"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    periodo_referencia: Mapped[str] = mapped_column(String, nullable=False)
    data_hora_consolidacao: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    origem_processamento: Mapped[str] = mapped_column(String, nullable=False)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id"))
    status: Mapped[str] = mapped_column(String, nullable=False, default="EM_PROCESSAMENTO")


class AnalyticalSnapshotIndicatorModel(Base):
    """Mapeamento de `snapshots_analiticos_indicadores` (D160)."""

    __tablename__ = "snapshots_analiticos_indicadores"

    snapshot_analitico_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("snapshots_analiticos.id"), primary_key=True
    )
    indicador_consolidado_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("indicadores_consolidados.id"), primary_key=True
    )
