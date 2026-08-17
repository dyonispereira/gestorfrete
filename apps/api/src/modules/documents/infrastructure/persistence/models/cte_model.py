from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class CteModel(Base):
    """Mapeamento de `ctes` (`relational/007-fiscal.md`). D109 — nunca excluído fisicamente, sem
    colunas de soft delete. D400 — `audit` só parcial (`criado_em`/`atualizado_em`, sem
    `criado_por`/`atualizado_por` — a DDL congelada nunca teve essas duas)."""

    __tablename__ = "ctes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "serie", "numero", name="uq_ctes_tenant_id_serie_numero"),
        UniqueConstraint("chave_acesso", name="uq_ctes_chave_acesso"),
        Index("idx_ctes_tenant_id_status", "tenant_id", "status"),
        Index("idx_ctes_viagem_id", "viagem_id"),
        # Idempotência por constraint (D108/D111/D275) — índice único parcial, mesmo padrão de
        # `formas_pagamento`-adjacent partial indexes já usados no projeto (`idx_viagens_tenant_id_
        # encerrada`, Lote 5): só reforça unicidade quando o protocolo já existe.
        Index("uq_ctes_protocolo_sefaz", "protocolo_sefaz", unique=True, postgresql_where=text("protocolo_sefaz IS NOT NULL")),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    viagem_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("viagens.id"), nullable=False)
    numero: Mapped[str] = mapped_column(String, nullable=False)
    serie: Mapped[str] = mapped_column(String, nullable=False)
    chave_acesso: Mapped[str | None] = mapped_column(String)
    valor_servico: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="RASCUNHO")
    xml_arquivo_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    protocolo_sefaz: Mapped[str | None] = mapped_column(String)
    data_hora_autorizacao: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CteStatusHistoryModel(Base):
    """Mapeamento de `ctes_status_history` (D017/D018/D284)."""

    __tablename__ = "ctes_status_history"
    __table_args__ = (Index("idx_ctes_status_history_tenant_id", "tenant_id"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    cte_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("ctes.id"), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    origem: Mapped[str] = mapped_column(String, nullable=False)
    observacao: Mapped[str | None] = mapped_column(String)
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
