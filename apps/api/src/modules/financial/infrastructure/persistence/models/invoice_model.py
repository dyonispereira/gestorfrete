from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class InvoiceModel(Base):
    """Mapeamento de `faturas` (D260). D391 — ganha o bloco padrão de auditoria, ausente na DDL
    congelada (que só tinha `criado_em`).

    Reconciliado (Lote Financeiro, Parte 3) — `viagem_id` removida (substituída por
    `InvoiceTripModel`/`fatura_viagens`); `valor_total` vira `valor_bruto + valor_ajuste`."""

    __tablename__ = "faturas"
    __table_args__ = (
        UniqueConstraint("tenant_id", "numero_fatura", name="uq_faturas_tenant_id_numero"),
        Index("idx_faturas_tenant_id_cliente_id", "tenant_id", "cliente_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    numero_fatura: Mapped[str] = mapped_column(String, nullable=False)
    entrega_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("entregas.id"))
    cliente_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False)
    valor_bruto: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    valor_ajuste: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0"))
    motivo_ajuste: Mapped[str | None] = mapped_column(String)
    valor_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    data_emissao: Mapped[date] = mapped_column(Date, nullable=False)
    forma_pagamento_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("formas_pagamento.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String, nullable=False, default="EMITIDA")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    criado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    atualizado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    excluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    excluido_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))


class InvoiceTripModel(Base):
    """Mapeamento de `fatura_viagens` (Lote Financeiro, Parte 3 — Faturamento Agrupado). Filha do
    agregado Fatura — nunca referencia Entrega/CT-e diretamente (D008), só Viagem."""

    __tablename__ = "fatura_viagens"
    __table_args__ = (
        UniqueConstraint("fatura_id", "viagem_id", name="uq_fatura_viagens_fatura_id_viagem_id"),
        CheckConstraint("valor > 0", name="ck_fatura_viagens_valor_positivo"),
        Index("idx_fatura_viagens_tenant_id_viagem_id", "tenant_id", "viagem_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    fatura_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("faturas.id"), nullable=False)
    viagem_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("viagens.id"), nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
