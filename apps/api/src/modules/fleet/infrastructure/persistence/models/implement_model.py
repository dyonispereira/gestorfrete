from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class ImplementModel(Base):
    """Mapeamento de `implementos` (`docs/database/relational/004-frota.md`) — sem
    `criado_por`/`atualizado_por`/`excluido_por` (a DDL não os tem)."""

    __tablename__ = "implementos"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_implementos_tenant_id_codigo"),
        UniqueConstraint("tenant_id", "placa", name="uq_implementos_tenant_id_placa"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String, nullable=False)
    placa: Mapped[str] = mapped_column(String, nullable=False)
    renavam: Mapped[str] = mapped_column(String, nullable=False)
    tipo_carroceria: Mapped[str] = mapped_column(String, nullable=False)
    categoria_veiculo_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("categorias_veiculo.id"), nullable=False
    )
    capacidade_carga: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status_disponibilidade: Mapped[str] = mapped_column(String, nullable=False, default="DISPONIVEL")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    excluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
