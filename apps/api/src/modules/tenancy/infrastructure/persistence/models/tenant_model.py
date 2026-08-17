from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class TenantModel(Base):
    """Mapeamento 1:1 de `tenants` (`docs/database/relational/001-core.md`) — nenhuma coluna
    adicionada, nenhuma renomeada; nomes físicos preservados em português, exatamente como a DDL
    já congelada."""

    __tablename__ = "tenants"
    __table_args__ = (
        UniqueConstraint("codigo", name="uq_tenants_codigo"),
        UniqueConstraint("cnpj", name="uq_tenants_cnpj"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    codigo: Mapped[str] = mapped_column(String, nullable=False)
    versao: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    razao_social: Mapped[str] = mapped_column(String, nullable=False)
    cnpj: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="TRIAL")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    criado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    atualizado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    excluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    excluido_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
