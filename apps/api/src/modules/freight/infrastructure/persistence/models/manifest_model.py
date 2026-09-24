from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class ManifestModel(Base):
    """Mapeamento de `romaneios` (`relational/003-operacao.md`)."""

    __tablename__ = "romaneios"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    viagem_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("viagens.id"), nullable=False)
    numero_documento: Mapped[str | None] = mapped_column(String)


class CargoItemModel(Base):
    """Mapeamento de `itens_carga` (`relational/003-operacao.md`) — nunca existe fora de um
    Romaneio."""

    __tablename__ = "itens_carga"
    __table_args__ = (
        Index("idx_itens_carga_tenant_id", "tenant_id"),
        Index("idx_itens_carga_romaneio_id", "romaneio_id"),
        CheckConstraint("peso > 0", name="ck_itens_carga_peso_positivo"),
        CheckConstraint("quantidade > 0", name="ck_itens_carga_quantidade_positiva"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    romaneio_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("romaneios.id"), nullable=False)
    descricao: Mapped[str] = mapped_column(String, nullable=False)
    peso: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)
