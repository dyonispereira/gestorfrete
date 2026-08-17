from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class OdometerReadingModel(Base):
    """Mapeamento de `leituras_hodometro` (`docs/database/relational/004-frota.md`) — Time
    Series/Histórica (D037/D050), `PARTITION BY RANGE (data_hora)` criada via SQL bruto na
    migration (SQLAlchemy declarative não expressa isso), com uma partição `DEFAULT` (D364) em vez
    da partição mensal fixa da DDL literal. `viagem_id` sem FK física (`viagens`/`freight` é Lote
    5+, mesmo padrão de D355)."""

    __tablename__ = "leituras_hodometro"
    __table_args__ = (
        Index("idx_leituras_hodometro_veiculo_id_data_hora", "veiculo_tracionador_id", "data_hora"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    veiculo_tracionador_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("veiculos_tracionadores.id"), nullable=False
    )
    valor_km: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    origem: Mapped[str] = mapped_column(String, nullable=False)
    viagem_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True, nullable=False)
