from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class AIFeedbackModel(Base):
    """`feedbacks_ia` (`relational/012-ia.md`) — D165/D192, polimórfico sobre as 5 saídas de IA."""

    __tablename__ = "feedbacks_ia"
    __table_args__ = (Index("idx_feedbacks_ia_saida_ia", "saida_ia_tipo", "saida_ia_id"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    saida_ia_tipo: Mapped[str] = mapped_column(String, nullable=False)
    saida_ia_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    usuario_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    resultado: Mapped[str] = mapped_column(String, nullable=False)
    justificativa: Mapped[str | None] = mapped_column(String)
    resultado_real: Mapped[str | None] = mapped_column(String)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
