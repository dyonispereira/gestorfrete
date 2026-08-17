from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class TrackingEventModel(Base):
    """Mapeamento de `eventos_rastreamento` (D119/D288) — derivado, particionado por `data_hora`
    (SQL bruto na migration), mas com um único timestamp (não segue o esqueleto de três timestamps
    do D191 — é detectado pelo sistema, não capturado de fonte externa). PK composta
    `(id, data_hora)`."""

    __tablename__ = "eventos_rastreamento"
    __table_args__ = (
        Index("idx_eventos_rastreamento_veiculo_id_tipo", "veiculo_tracionador_id", "tipo", "data_hora"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    veiculo_tracionador_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    posicao_veiculo_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    cerca_eletronica_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("cercas_eletronicas.id")
    )
    configuracao_limite_velocidade_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    valor_detectado: Mapped[float | None] = mapped_column(Numeric(12, 4))
    severidade: Mapped[str] = mapped_column(String, nullable=False)
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True, nullable=False)
