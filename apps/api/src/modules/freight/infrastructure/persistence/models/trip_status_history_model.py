from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class TripStatusHistoryModel(Base):
    """Mapeamento de `viagem_status_history` (`relational/003-operacao.md`) — maior volume de
    transições do sistema, `PARTITION BY RANGE (data_hora)` criada via SQL bruto na migration
    (SQLAlchemy declarative não expressa isso), com uma partição `DEFAULT` (mesmo padrão de
    `logs_auditoria`/D346, `leituras_hodometro`/D364). PK composta `(id, data_hora)` —
    particionamento por Postgres exige a coluna de partição em toda chave primária."""

    __tablename__ = "viagem_status_history"
    __table_args__ = (Index("idx_viagem_status_history_viagem_id_dimensao", "viagem_id", "dimensao", "data_hora"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    viagem_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("viagens.id"), nullable=False)
    dimensao: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    origem: Mapped[str] = mapped_column(String, nullable=False)
    observacao: Mapped[str | None] = mapped_column(String)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True, nullable=False)
