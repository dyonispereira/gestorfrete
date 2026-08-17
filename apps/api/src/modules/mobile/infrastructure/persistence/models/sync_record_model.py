from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Computed, DateTime, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class SyncRecordModel(Base):
    """Mapeamento de `registros_sincronizacao` (D135) — nível de lote. `duracao_ms` é `GENERATED`
    (mesmo critério de D382/Lote 5/Lote 7/Lote 8: depende só de duas colunas da própria linha)."""

    __tablename__ = "registros_sincronizacao"
    __table_args__ = (Index("idx_registros_sincronizacao_sessao_mobile_id", "sessao_mobile_id"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    sessao_mobile_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("sessoes_mobile.id"), nullable=False
    )
    data_hora_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data_hora_fim: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duracao_ms: Mapped[int | None] = mapped_column(
        Integer, Computed("EXTRACT(EPOCH FROM (data_hora_fim - data_hora_inicio)) * 1000")
    )
    quantidade_comandos: Mapped[int] = mapped_column(Integer, nullable=False)
    quantidade_sucesso: Mapped[int] = mapped_column(Integer, nullable=False)
    quantidade_falha: Mapped[int] = mapped_column(Integer, nullable=False)
