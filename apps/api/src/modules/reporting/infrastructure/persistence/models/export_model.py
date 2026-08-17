from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class ExportModel(Base):
    """Mapeamento de `exportacoes_geradas` (D157/D307, `relational/011-bi.md`)."""

    __tablename__ = "exportacoes_geradas"
    __table_args__ = (Index("idx_exportacoes_geradas_usuario_id", "usuario_id", "data_hora_solicitacao"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    relatorio_salvo_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("relatorios_salvos.id")
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    filtros_utilizados: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    periodo: Mapped[str] = mapped_column(String, nullable=False)
    metricas_versoes: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)
    arquivo_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    mensagem_erro: Mapped[str | None] = mapped_column(String)
    data_hora_solicitacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="PROCESSANDO")
