from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class VehicleTechnicalSheetModel(Base):
    """Mapeamento de `fichas_tecnicas_veiculo` — sem colunas de timestamp (a DDL não as tem)."""

    __tablename__ = "fichas_tecnicas_veiculo"
    __table_args__ = (
        UniqueConstraint("veiculo_tracionador_id", name="uq_fichas_tecnicas_veiculo_veiculo_id"),
        UniqueConstraint("chassi", name="uq_fichas_tecnicas_veiculo_chassi"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    veiculo_tracionador_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("veiculos_tracionadores.id"), nullable=False
    )
    chassi: Mapped[str] = mapped_column(String, nullable=False)
    motor: Mapped[str | None] = mapped_column(String)
    eixos: Mapped[int] = mapped_column(Integer, nullable=False)
    tara: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    capacidade_carga: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    pbt: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    rntrc_proprietario: Mapped[str | None] = mapped_column(String)
    combustivel: Mapped[str] = mapped_column(String, nullable=False)
