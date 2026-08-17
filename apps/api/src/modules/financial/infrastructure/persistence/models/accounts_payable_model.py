from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class AccountsPayableModel(Base):
    """Mapeamento de `contas_pagar`. D391 — ganha o bloco padrão de auditoria, ausente na DDL
    congelada (que só tinha `criado_em`). `ordem_servico_id` sem FK física (D387 — `maintenance`
    ainda não implementa Ordem de Serviço)."""

    __tablename__ = "contas_pagar"
    __table_args__ = (
        CheckConstraint(
            "origem NOT IN ('VIAGEM', 'ORDEM_SERVICO') OR "
            "(origem = 'VIAGEM' AND viagem_id IS NOT NULL) OR "
            "(origem = 'ORDEM_SERVICO' AND ordem_servico_id IS NOT NULL)",
            name="ck_contas_pagar_origem_especifica",
        ),
        Index("idx_contas_pagar_tenant_id_status", "tenant_id", "status"),
        Index("idx_contas_pagar_fornecedor_id", "fornecedor_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    fornecedor_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("fornecedores.id"), nullable=False
    )
    centro_custo_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("centros_custo.id"), nullable=False
    )
    origem: Mapped[str] = mapped_column(String, nullable=False)
    viagem_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("viagens.id"))
    ordem_servico_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    data_vencimento: Mapped[date] = mapped_column(Date, nullable=False)
    plano_contas_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("plano_contas.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String, nullable=False, default="LANCADA")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    criado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    atualizado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    excluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    excluido_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))


class PayableStatusHistoryModel(Base):
    """Mapeamento de `contas_pagar_status_history` (D017/D018)."""

    __tablename__ = "contas_pagar_status_history"
    __table_args__ = (Index("idx_contas_pagar_status_history_tenant_id", "tenant_id"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    conta_pagar_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("contas_pagar.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String, nullable=False)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    observacao: Mapped[str | None] = mapped_column(String)
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ExpenseApprovalModel(Base):
    """Mapeamento de `aprovacoes_despesa`."""

    __tablename__ = "aprovacoes_despesa"
    __table_args__ = (Index("idx_aprovacoes_despesa_tenant_id", "tenant_id"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    conta_pagar_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("contas_pagar.id"), nullable=False
    )
    decisao: Mapped[str] = mapped_column(String, nullable=False)
    justificativa: Mapped[str | None] = mapped_column(String)
    ator_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ExpenseAllocationModel(Base):
    """Mapeamento de `rateios_despesa`."""

    __tablename__ = "rateios_despesa"
    __table_args__ = (
        Index("idx_rateios_despesa_tenant_id", "tenant_id"),
        Index("idx_rateios_despesa_conta_pagar_id", "conta_pagar_id"),
        CheckConstraint(
            "centro_custo_id IS NOT NULL OR viagem_id IS NOT NULL", name="ck_rateios_despesa_alvo"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    conta_pagar_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("contas_pagar.id"), nullable=False
    )
    centro_custo_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("centros_custo.id")
    )
    viagem_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("viagens.id"))
    criterio: Mapped[str] = mapped_column(String, nullable=False)
    valor_rateado: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
