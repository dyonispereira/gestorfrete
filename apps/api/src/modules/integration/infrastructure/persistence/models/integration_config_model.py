from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class IntegrationConfigModel(Base):
    """Mapeamento de `configuracoes_integracao` (D321, `relational/010-administracao.md`). Sem
    nenhuma coluna de auditoria na DDL congelada (D400-family)."""

    __tablename__ = "configuracoes_integracao"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    credencial_arquivo_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ATIVA")
