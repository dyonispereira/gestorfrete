from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class MdfeModel(Base):
    """Mapeamento de `mdfes` (`relational/007-fiscal.md`). D109 — nunca excluído fisicamente. D400
    — sem `audit` (DDL congelada não tem nenhuma coluna de timestamp)."""

    __tablename__ = "mdfes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "serie", "numero", name="uq_mdfes_tenant_id_serie_numero"),
        UniqueConstraint("chave_acesso", name="uq_mdfes_chave_acesso"),
        Index("idx_mdfes_viagem_id", "viagem_id"),
        Index("uq_mdfes_protocolo_sefaz", "protocolo_sefaz", unique=True, postgresql_where=text("protocolo_sefaz IS NOT NULL")),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    viagem_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("viagens.id"), nullable=False)
    numero: Mapped[str] = mapped_column(String, nullable=False)
    serie: Mapped[str] = mapped_column(String, nullable=False)
    chave_acesso: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, nullable=False, default="PENDENTE")
    xml_arquivo_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    protocolo_sefaz: Mapped[str | None] = mapped_column(String)
    data_hora_encerramento: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MdfeCteModel(Base):
    """Mapeamento de `mdfes_ctes` (N:N) — um MDF-e consolida um ou mais CT-e."""

    __tablename__ = "mdfes_ctes"

    mdfe_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("mdfes.id"), primary_key=True)
    cte_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("ctes.id"), primary_key=True)


class MdfeStatusHistoryModel(Base):
    """Mapeamento de `mdfes_status_history` (D017/D018/D284)."""

    __tablename__ = "mdfes_status_history"
    __table_args__ = (Index("idx_mdfes_status_history_tenant_id", "tenant_id"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    mdfe_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("mdfes.id"), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    origem: Mapped[str] = mapped_column(String, nullable=False)
    observacao: Mapped[str | None] = mapped_column(String)
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
