from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class VehicleAvailabilityModel(Base):
    """Mapeamento de `disponibilidade_veiculo` (D081, Read Model) — sem
    `criado_por`/`atualizado_por`: ninguém edita diretamente (D032), só o processo consumidor de
    eventos (`AVAILABILITY_IMPLEMENTATION.md`)."""

    __tablename__ = "disponibilidade_veiculo"
    __table_args__ = (Index("idx_disponibilidade_veiculo_tenant_id", "tenant_id"),)

    veiculo_tracionador_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("veiculos_tracionadores.id"), primary_key=True
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    motorista_atual_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("motoristas.id"))
    implemento_atual_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("implementos.id"))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
