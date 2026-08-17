from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class DriverModel(Base):
    """Mapeamento de `motoristas` (`docs/database/relational/002-cadastros.md`)."""

    __tablename__ = "motoristas"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_motoristas_tenant_id_codigo"),
        UniqueConstraint("tenant_id", "cpf", name="uq_motoristas_tenant_id_cpf"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String, nullable=False)
    versao: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    cpf: Mapped[str] = mapped_column(String, nullable=False)
    telefone: Mapped[str | None] = mapped_column(String)
    email: Mapped[str | None] = mapped_column(String)
    tipo_vinculo: Mapped[str] = mapped_column(String, nullable=False)
    status_aptidao: Mapped[str] = mapped_column(String, nullable=False, default="APTO")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    criado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    atualizado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    excluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    excluido_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))


class DriverDocumentModel(Base):
    """Mapeamento de `documentos_motorista` (D183) — **sem** `excluido_em`: a DDL física não
    suporta soft delete para esta tabela (nenhuma coluna existe), então `DELETE` é um `DELETE` real
    de linha (`DRIVER_IMPLEMENTATION.md`), exceção deliberada ao padrão geral (D343), não um
    esquecimento."""

    __tablename__ = "documentos_motorista"
    __table_args__ = (
        CheckConstraint(
            "categoria_cnh IS NULL OR tipo_documento = 'CNH'",
            name="ck_documentos_motorista_categoria_so_cnh",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    motorista_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("motoristas.id"), nullable=False)
    tipo_documento: Mapped[str] = mapped_column(String, nullable=False)
    numero: Mapped[str] = mapped_column(String, nullable=False)
    categoria_cnh: Mapped[str | None] = mapped_column(String)
    data_validade: Mapped[date | None] = mapped_column(Date)
    arquivo_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(String, nullable=False, default="VALIDO")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    criado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    atualizado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
