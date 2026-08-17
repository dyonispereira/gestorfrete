from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class SavedReportModel(Base):
    """Mapeamento de `relatorios_salvos` (`relational/011-bi.md`)."""

    __tablename__ = "relatorios_salvos"
    __table_args__ = (UniqueConstraint("usuario_id", "nome", name="uq_relatorios_salvos_usuario_id_nome"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    usuario_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    filtros: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    formato_saida: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ATIVO")


class SavedReportMetricModel(Base):
    """Mapeamento de `relatorios_salvos_metricas`."""

    __tablename__ = "relatorios_salvos_metricas"

    relatorio_salvo_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("relatorios_salvos.id"), primary_key=True
    )
    metrica_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("metricas.id"), primary_key=True)
