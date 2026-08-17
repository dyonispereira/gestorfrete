from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class FinancialReversalModel(Base):
    """Mapeamento de `estornos_financeiros` (D266)."""

    __tablename__ = "estornos_financeiros"
    __table_args__ = (
        CheckConstraint(
            "(fatura_id IS NOT NULL)::int + (conta_pagar_id IS NOT NULL)::int + "
            "(conta_receber_id IS NOT NULL)::int = 1",
            name="ck_estornos_financeiros_alvo_exclusivo",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    fatura_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("faturas.id"))
    conta_pagar_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("contas_pagar.id"))
    conta_receber_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("contas_receber.id")
    )
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    motivo: Mapped[str] = mapped_column(String, nullable=False)
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
