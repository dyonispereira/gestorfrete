from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class DigitalSignatureModel(Base):
    """Mapeamento de `assinaturas_digitais`. `documento_id` polimórfico, sem FK física (mesmo
    padrão de `anexos`)."""

    __tablename__ = "assinaturas_digitais"
    __table_args__ = (Index("idx_assinaturas_digitais_documento", "documento_tipo", "documento_id"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    documento_tipo: Mapped[str] = mapped_column(String, nullable=False)
    documento_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    papel_signatario: Mapped[str] = mapped_column(String, nullable=False)
    nome_signatario_informado: Mapped[str | None] = mapped_column(String)
    arquivo_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    capturado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recebido_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
