from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class SyncQueueItemModel(Base):
    """Mapeamento de `filas_sincronizacao` — a tabela mais crítica do módulo. `payload` (`JSONB`)
    nunca é sobrescrito depois de criado (D139); `resolucao_conflito` é uma coluna adicional."""

    __tablename__ = "filas_sincronizacao"
    __table_args__ = (
        UniqueConstraint(
            "sessao_mobile_id", "identificador_local_unico", name="uq_filas_sincronizacao_identificador_local"
        ),
        UniqueConstraint("sessao_mobile_id", "sequencia_local", name="uq_filas_sincronizacao_sessao_sequencia"),
        Index("idx_filas_sincronizacao_entidade_destino", "entidade_destino_tipo", "entidade_destino_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    sessao_mobile_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("sessoes_mobile.id"), nullable=False
    )
    sequencia_local: Mapped[int] = mapped_column(Integer, nullable=False)
    tipo_comando: Mapped[str] = mapped_column(String, nullable=False)
    entidade_destino_tipo: Mapped[str] = mapped_column(String, nullable=False)
    entidade_destino_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    identificador_local_unico: Mapped[str] = mapped_column(String, nullable=False)
    numero_tentativa: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String, nullable=False, default="PENDENTE")
    resolucao_conflito: Mapped[str | None] = mapped_column(String)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
