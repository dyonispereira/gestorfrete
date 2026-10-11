from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class PriceTableModel(Base):
    """Mapeamento de `tabelas_preco` (`alembic/versions/d10bc3b53be7_pricing_tabelas_preco.py`)."""

    __tablename__ = "tabelas_preco"
    __table_args__ = (
        Index("idx_tabelas_preco_tenant_id", "tenant_id"),
        Index("idx_tabelas_preco_tenant_id_direcao_status", "tenant_id", "direcao", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    direcao: Mapped[str] = mapped_column(String, nullable=False)
    versao: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    vigencia_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    vigencia_fim: Mapped[date | None] = mapped_column(Date)
    cliente_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("clientes.id"))
    status: Mapped[str] = mapped_column(String, nullable=False, default="RASCUNHO")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    criado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id"))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    atualizado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id"))


class PriceTableItemModel(Base):
    """Mapeamento de `itens_tabela_preco`."""

    __tablename__ = "itens_tabela_preco"
    __table_args__ = (Index("idx_itens_tabela_preco_tabela_preco_id", "tabela_preco_id"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    tabela_preco_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tabelas_preco.id"), nullable=False
    )
    unidade_calculo: Mapped[str] = mapped_column(String, nullable=False)
    categoria_veiculo_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("categorias_veiculo.id")
    )
    origem_uf: Mapped[str | None] = mapped_column(String(2))
    destino_uf: Mapped[str | None] = mapped_column(String(2))
    faixa_distancia_min_km: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    faixa_distancia_max_km: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    faixa_modo: Mapped[str | None] = mapped_column(String)
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    valor_minimo: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    adicional_fixo: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    desconto_fixo: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    adicional_percentual: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    desconto_percentual: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    base_percentual_descricao: Mapped[str | None] = mapped_column(String)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
