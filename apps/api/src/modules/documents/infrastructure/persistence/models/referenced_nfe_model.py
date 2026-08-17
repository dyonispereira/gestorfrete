from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class ReferencedNfeModel(Base):
    """Mapeamento de `nfe_referenciadas` — NF-e Referenciada, sub-recurso de `Cte`."""

    __tablename__ = "nfe_referenciadas"
    __table_args__ = (
        CheckConstraint("chave_acesso ~ '^[0-9]{44}$'", name="ck_nfe_referenciadas_chave_44_digitos"),
        Index("idx_nfe_referenciadas_tenant_id", "tenant_id"),
        Index("idx_nfe_referenciadas_cte_id", "cte_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    cte_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("ctes.id"), nullable=False)
    chave_acesso: Mapped[str] = mapped_column(String, nullable=False)
    xml_arquivo_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
