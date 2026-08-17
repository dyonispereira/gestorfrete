from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class ScheduledUpdateModel(Base):
    """Mapeamento de `agendamentos_atualizacao` (D159, `relational/011-bi.md`)."""

    __tablename__ = "agendamentos_atualizacao"
    __table_args__ = (
        CheckConstraint(
            "(metrica_id IS NOT NULL)::int + (cubo_analitico_id IS NOT NULL)::int = 1",
            name="ck_agendamentos_atualizacao_alvo",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    metrica_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("metricas.id"))
    cubo_analitico_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("cubos_analiticos.id")
    )
    modo: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ATIVO")
