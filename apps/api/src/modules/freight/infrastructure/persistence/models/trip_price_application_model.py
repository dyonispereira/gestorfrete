from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class TripPriceApplicationModel(Base):
    """Mapeamento de `aplicacoes_tabela_preco_viagem` — append-only (D109-consistent), nunca
    `UPDATE` de valores já calculados, só `removido_em`/`removido_por` ao desfazer."""

    __tablename__ = "aplicacoes_tabela_preco_viagem"
    __table_args__ = (Index("idx_aplicacoes_tabela_preco_viagem_viagem_id", "viagem_id"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    viagem_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("viagens.id"), nullable=False)
    tabela_preco_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    item_tabela_preco_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    tabela_preco_versao: Mapped[int] = mapped_column(Integer, nullable=False)
    direcao: Mapped[str] = mapped_column(String, nullable=False)
    unidade_calculo: Mapped[str] = mapped_column(String, nullable=False)
    quantidade_utilizada: Mapped[Decimal | None] = mapped_column(Numeric(14, 3))
    base_percentual_valor: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    tarifa_aplicada: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    valor_minimo_aplicado: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    adicional_fixo_aplicado: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    desconto_fixo_aplicado: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    adicional_percentual_aplicado: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    desconto_percentual_aplicado: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    valor_calculado_bruto: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    valor_final: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    aplicado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    aplicado_por: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    removido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    removido_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id"))
