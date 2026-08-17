from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class DashboardModel(Base):
    """Mapeamento de `dashboards_personalizados` (D152, `relational/011-bi.md`). Sem nenhuma
    coluna de auditoria (D422)."""

    __tablename__ = "dashboards_personalizados"
    __table_args__ = (
        UniqueConstraint("usuario_id", "nome", name="uq_dashboards_personalizados_usuario_id_nome"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    usuario_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    layout: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    widgets: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)
    filtros: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    permissoes_compartilhamento: Mapped[str] = mapped_column(String, nullable=False, default="PRIVADO")
    preferencias: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ATIVO")
