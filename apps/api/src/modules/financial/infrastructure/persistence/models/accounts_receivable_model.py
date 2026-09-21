from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class AccountsReceivableModel(Base):
    """Mapeamento de `contas_receber`. Sem colunas de auditoria (D391-nota: a DDL congelada nunca
    teve, o schema `AccountsReceivable` nunca prometeu `audit`)."""

    __tablename__ = "contas_receber"
    __table_args__ = (
        UniqueConstraint("fatura_id", "numero_parcela", name="uq_contas_receber_fatura_id_parcela"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    fatura_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("faturas.id"), nullable=False)
    numero_parcela: Mapped[int] = mapped_column(Integer, nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    data_vencimento: Mapped[date] = mapped_column(Date, nullable=False)
    competencia: Mapped[date] = mapped_column(Date, nullable=False)
    data_recebimento: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String, nullable=False, default="PENDENTE")


class ReceivableStatusHistoryModel(Base):
    """Mapeamento de `contas_receber_status_history` (D017/D018)."""

    __tablename__ = "contas_receber_status_history"
    __table_args__ = (Index("idx_contas_receber_status_history_tenant_id", "tenant_id"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    conta_receber_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("contas_receber.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String, nullable=False)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
