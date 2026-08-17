from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class ProofOfDeliveryModel(Base):
    """Mapeamento de `canhotos` (D373, `relational/003-operacao.md`) — 1:1 com Entrega.
    `assinatura_arquivo_id` sem FK — referência lógica ao Storage (D107), mesmo padrão de
    `documentos_veiculo.arquivo_id` (Lote 4)."""

    __tablename__ = "canhotos"
    __table_args__ = (UniqueConstraint("entrega_id", name="uq_canhotos_entrega_id"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    entrega_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("entregas.id"), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="PENDENTE")
    data_hora_registro: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    assinatura_arquivo_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
