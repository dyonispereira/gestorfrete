from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class SavedFilterModel(Base):
    """Mapeamento de `filtros_favoritos` (`relational/011-bi.md`)."""

    __tablename__ = "filtros_favoritos"
    __table_args__ = (UniqueConstraint("usuario_id", "nome", name="uq_filtros_favoritos_usuario_id_nome"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    usuario_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    criterios: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ATIVO")
