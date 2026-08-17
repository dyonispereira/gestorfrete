from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class CorrectionLetterModel(Base):
    """Mapeamento de `cartas_correcao` — Carta de Correção, sub-recurso append-only de `Cte`."""

    __tablename__ = "cartas_correcao"
    __table_args__ = (
        UniqueConstraint("cte_id", "numero_sequencial", name="uq_cartas_correcao_cte_id_sequencial"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    cte_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("ctes.id"), nullable=False)
    numero_sequencial: Mapped[int] = mapped_column(Integer, nullable=False)
    texto_correcao: Mapped[str] = mapped_column(String, nullable=False)
    xml_arquivo_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    data_hora_envio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
