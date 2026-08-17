from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class CiotModel(Base):
    """Mapeamento de `ciots` (`relational/007-fiscal.md`). D109 — nunca excluído fisicamente. D400
    — sem `audit` (DDL congelada não tem nenhuma coluna de timestamp)."""

    __tablename__ = "ciots"
    __table_args__ = (
        UniqueConstraint("codigo_ciot", name="uq_ciots_codigo_ciot"),
        Index("uq_ciots_protocolo_antt", "protocolo_antt", unique=True, postgresql_where=text("protocolo_antt IS NOT NULL")),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    viagem_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("viagens.id"), nullable=False)
    motorista_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("motoristas.id"), nullable=False)
    codigo_ciot: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, nullable=False, default="PENDENTE")
    protocolo_antt: Mapped[str | None] = mapped_column(String)
    data_hora_registro: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CiotStatusHistoryModel(Base):
    """Mapeamento de `ciots_status_history` (D017/D018/D284)."""

    __tablename__ = "ciots_status_history"
    __table_args__ = (Index("idx_ciots_status_history_tenant_id", "tenant_id"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    ciot_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("ciots.id"), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    origem: Mapped[str] = mapped_column(String, nullable=False)
    observacao: Mapped[str | None] = mapped_column(String)
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
