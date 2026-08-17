from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class AddressModel(Base):
    """Mapeamento de `enderecos` (`docs/database/relational/002-cadastros.md`) — `entidade_tipo`/
    `tipo_endereco` mapeados como `String`, não `Enum` nativo do Postgres, mesma convenção já
    estabelecida para todo status/enum deste backend desde o Lote 2 (`TenantModel.status`,
    `UserModel.status`, etc.) — validação de vocabulário fica no Domain (`OwnerType`/
    `AddressType`), nunca duplicada como `CHECK`/`ENUM` físico."""

    __tablename__ = "enderecos"
    __table_args__ = (
        Index("idx_enderecos_entidade_tipo_entidade_id", "entidade_tipo", "entidade_id"),
        Index(
            "uq_enderecos_entidade_principal",
            "entidade_tipo",
            "entidade_id",
            unique=True,
            postgresql_where=text("tipo_endereco = 'PRINCIPAL' AND excluido_em IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    entidade_tipo: Mapped[str] = mapped_column(String, nullable=False)
    entidade_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    tipo_endereco: Mapped[str] = mapped_column(String, nullable=False, default="PRINCIPAL")
    logradouro: Mapped[str] = mapped_column(String, nullable=False)
    numero: Mapped[str | None] = mapped_column(String)
    complemento: Mapped[str | None] = mapped_column(String)
    bairro: Mapped[str] = mapped_column(String, nullable=False)
    cidade: Mapped[str] = mapped_column(String, nullable=False)
    uf: Mapped[str] = mapped_column(String, nullable=False)
    cep: Mapped[str] = mapped_column(String, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    criado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    atualizado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    excluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    excluido_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
