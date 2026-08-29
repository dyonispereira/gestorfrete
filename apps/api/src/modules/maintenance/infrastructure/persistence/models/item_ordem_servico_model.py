from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class ItemOrdemServicoModel(Base):
    """Mapeamento de `itens_ordem_servico`. `valor_total` é `GENERATED ALWAYS AS (quantidade *
    valor_unitario) STORED` no banco — não mapeado aqui, recalculado a partir de `quantidade`/
    `valor_unitario` pela entidade (`ItemOrdemServico.valor_total`, property)."""

    __tablename__ = "itens_ordem_servico"
    __table_args__ = (Index("idx_itens_ordem_servico_ordem_servico_id", "ordem_servico_id"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    ordem_servico_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ordens_servico.id"), nullable=False
    )
    categoria_custo: Mapped[str] = mapped_column(String, nullable=False)
    descricao: Mapped[str] = mapped_column(String, nullable=False)
    peca_estoque_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    quantidade: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    valor_unitario: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
