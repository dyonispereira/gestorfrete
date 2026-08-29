from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class VehicleImpedimentModel(Base):
    """Mapeamento de `veiculo_impedimentos` — ledger interno que sustenta a projeção de
    `disponibilidade_veiculo` (ver `vehicle_availability_model.py`, D081/D247). `referencia_id`
    sem FK física — aponta para `viagens` ou `ordens_servico` dependendo de `tipo`."""

    __tablename__ = "veiculo_impedimentos"
    __table_args__ = (
        Index("idx_veiculo_impedimentos_veiculo_ativo", "veiculo_tracionador_id", "encerrado_em"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    veiculo_tracionador_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("veiculos_tracionadores.id"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    referencia_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    motorista_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("motoristas.id"))
    implemento_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("implementos.id"))
    iniciado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    encerrado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
