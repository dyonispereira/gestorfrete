from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class ChartOfAccountsModel(Base):
    """Mapeamento de `plano_contas` (`relational/006-financeiro.md`). D391 — ganha o bloco padrão
    de auditoria, ausente na DDL congelada (que só tinha `id`/`tenant_id`/`codigo_contabil`/
    `nome`/`tipo`/`categoria_pai_id`/`status`)."""

    __tablename__ = "plano_contas"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo_contabil", name="uq_plano_contas_tenant_id_codigo"),
        Index("idx_plano_contas_categoria_pai_id", "categoria_pai_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    codigo_contabil: Mapped[str] = mapped_column(String, nullable=False)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    categoria_pai_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("plano_contas.id"))
    status: Mapped[str] = mapped_column(String, nullable=False, default="ATIVO")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    criado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    atualizado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    excluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    excluido_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
