from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class ChannelPreferenceModel(Base):
    """Mapeamento de `preferencias_notificacao` (`relational/010-administracao.md`)."""

    __tablename__ = "preferencias_notificacao"
    __table_args__ = (
        UniqueConstraint("usuario_id", "canal", name="uq_preferencias_notificacao_usuario_canal"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    usuario_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    canal: Mapped[str] = mapped_column(String, nullable=False)
    habilitado: Mapped[bool] = mapped_column(nullable=False, default=True)
