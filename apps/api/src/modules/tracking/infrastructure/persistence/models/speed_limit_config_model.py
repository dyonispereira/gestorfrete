from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class SpeedLimitConfigModel(Base):
    """Mapeamento de `configuracoes_limite_velocidade`."""

    __tablename__ = "configuracoes_limite_velocidade"
    __table_args__ = (CheckConstraint("limite_kmh > 0", name="ck_configuracoes_limite_velocidade_limite_kmh"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    categoria_veiculo_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("categorias_veiculo.id")
    )
    limite_kmh: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ATIVA")
