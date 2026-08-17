from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class TrackingProviderModel(Base):
    """Mapeamento de `provedores_rastreamento` (`relational/008-rastreamento.md`)."""

    __tablename__ = "provedores_rastreamento"
    __table_args__ = (UniqueConstraint("tenant_id", "nome", name="uq_provedores_rastreamento_tenant_id_nome"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ATIVO")
