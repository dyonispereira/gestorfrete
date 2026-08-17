from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class VehicleCategoryModel(Base):
    """Mapeamento de `categorias_veiculo` (`docs/database/relational/004-frota.md`) — sem
    `versao`/`excluido_em`/`criado_por` (a DDL não tem essas colunas para esta entidade de
    Referência, D036)."""

    __tablename__ = "categorias_veiculo"
    __table_args__ = (UniqueConstraint("tenant_id", "nome", name="uq_categorias_veiculo_tenant_id_nome"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String, nullable=False)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ATIVA")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
