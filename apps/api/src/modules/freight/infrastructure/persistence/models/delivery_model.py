from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class DeliveryModel(Base):
    """Mapeamento de `entregas` (`relational/003-operacao.md`) — multi-drop real via
    `UNIQUE (viagem_id, ordem)`, nunca `entrega1`/`entrega2`."""

    __tablename__ = "entregas"
    __table_args__ = (
        UniqueConstraint("viagem_id", "ordem", name="uq_entregas_viagem_id_ordem"),
        Index("idx_entregas_viagem_id", "viagem_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    viagem_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("viagens.id"), nullable=False)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)
    destinatario: Mapped[str] = mapped_column(String, nullable=False)
    endereco_entrega: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="PENDENTE")
    data_hora_conclusao: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    motivo_recusa: Mapped[str | None] = mapped_column(String)


class DeliveryWindowModel(Base):
    """Mapeamento de `janelas_entrega` — 1:1 com Entrega, sem endpoint próprio
    (`DELIVERY_IMPLEMENTATION.md`)."""

    __tablename__ = "janelas_entrega"
    __table_args__ = (UniqueConstraint("entrega_id", name="uq_janelas_entrega_entrega_id"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    entrega_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("entregas.id"), nullable=False)
    hora_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    hora_fim: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
