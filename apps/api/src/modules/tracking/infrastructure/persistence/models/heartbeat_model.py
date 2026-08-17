from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class HeartbeatModel(Base):
    """Mapeamento de `heartbeats` (D105) — particionada por `recebido_em`, não `capturado_em`, única
    exceção ao padrão D191 (heartbeat pode não informar captura). PK composta `(id, recebido_em)`."""

    __tablename__ = "heartbeats"
    __table_args__ = (
        # D201/D202-style — `recebido_em` (coluna de partição) entra por exigência física do
        # Postgres em toda UNIQUE de tabela particionada; `exists_with_protocol` já verifica antes
        # de inserir, esta é a segunda camada de defesa.
        Index(
            "uq_heartbeats_equipamento_protocolo", "equipamento_rastreamento_id", "protocolo_externo",
            "recebido_em", unique=True, postgresql_where=text("protocolo_externo IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    equipamento_rastreamento_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("equipamentos_rastreamento.id"), nullable=False
    )
    protocolo_externo: Mapped[str | None] = mapped_column(String)
    capturado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    recebido_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True, nullable=False)
    processado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
