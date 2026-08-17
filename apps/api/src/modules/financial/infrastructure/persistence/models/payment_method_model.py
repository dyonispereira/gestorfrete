from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class PaymentMethodModel(Base):
    """Mapeamento de `formas_pagamento` (D386, `relational/006-financeiro.md`)."""

    __tablename__ = "formas_pagamento"
    __table_args__ = (UniqueConstraint("tenant_id", "nome", name="uq_formas_pagamento_tenant_id_nome"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ATIVA")
