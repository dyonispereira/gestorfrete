from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class ClientContactModel(Base):
    """Mapeamento de `contatos_cliente` — tem `tenant_id` (isolamento direto, D338/D339), mas sem
    `criado_por`/`atualizado_por`/`excluido_por` (a tabela não tem essas colunas de auditoria fina,
    D217, `012-contacts.md`)."""

    __tablename__ = "contatos_cliente"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    cliente_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    cargo: Mapped[str | None] = mapped_column(String)
    telefone: Mapped[str | None] = mapped_column(String)
    email: Mapped[str | None] = mapped_column(String)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    excluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
