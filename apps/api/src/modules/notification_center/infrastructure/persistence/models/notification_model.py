from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class NotificationModel(Base):
    """Mapeamento de `notificacoes` (D320/D323, `relational/010-administracao.md`)."""

    __tablename__ = "notificacoes"
    __table_args__ = (
        Index("idx_notificacoes_usuario_destinatario_status", "usuario_destinatario_id", "status", "enviado_em"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    usuario_destinatario_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False
    )
    canal: Mapped[str] = mapped_column(String, nullable=False)
    evento_origem_tipo: Mapped[str] = mapped_column(String, nullable=False)
    entidade_tipo: Mapped[str | None] = mapped_column(String)
    entidade_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    titulo: Mapped[str] = mapped_column(String, nullable=False)
    mensagem: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="NAO_LIDA")
    enviado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    lido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
