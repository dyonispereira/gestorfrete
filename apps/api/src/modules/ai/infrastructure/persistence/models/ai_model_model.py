from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class AIModelModel(Base):
    """`modelos_ia` (`relational/012-ia.md`). `tenant_id` nulo = modelo padrão da plataforma
    (mesmo padrão de `MetricModel`, D046)."""

    __tablename__ = "modelos_ia"
    __table_args__ = (UniqueConstraint("nome", "versao", name="uq_modelos_ia_nome_versao"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"))
    nome: Mapped[str] = mapped_column(String, nullable=False)
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    versao: Mapped[str] = mapped_column(String, nullable=False)
    fornecedor_logico: Mapped[str] = mapped_column(String, nullable=False)
    capacidade: Mapped[str] = mapped_column(String, nullable=False)
    contexto_maximo: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String, nullable=False, default="EM_TREINAMENTO")
