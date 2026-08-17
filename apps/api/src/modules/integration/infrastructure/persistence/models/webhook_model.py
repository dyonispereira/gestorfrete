from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class WebhookModel(Base):
    """Mapeamento de `webhooks` (D111/D138, `relational/010-administracao.md`)."""

    __tablename__ = "webhooks"
    __table_args__ = (
        Index("idx_webhooks_tenant_id_status", "tenant_id", "status"),
        Index("idx_webhooks_eventos_assinados", "eventos_assinados", postgresql_using="gin"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    configuracao_integracao_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("configuracoes_integracao.id")
    )
    url_destino: Mapped[str] = mapped_column(String, nullable=False)
    eventos_assinados: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)
    segredo_hmac_arquivo_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ATIVO")
