from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class TelemetryReadingModel(Base):
    """Mapeamento de `leituras_telemetria` (D191, EAV D120) — particionada por `capturado_em` (SQL
    bruto na migration). PK composta `(id, capturado_em)`."""

    __tablename__ = "leituras_telemetria"
    __table_args__ = (
        Index(
            "idx_leituras_telemetria_veiculo_id_tipo_sensor_capturado_em",
            "veiculo_tracionador_id", "tipo_sensor", "capturado_em",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    veiculo_tracionador_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    equipamento_rastreamento_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    posicao_veiculo_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    tipo_sensor: Mapped[str] = mapped_column(String, nullable=False)
    valor: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    unidade: Mapped[str] = mapped_column(String, nullable=False)
    capturado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True, nullable=False)
    recebido_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
