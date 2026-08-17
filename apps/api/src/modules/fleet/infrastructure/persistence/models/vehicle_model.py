from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class VehicleModel(Base):
    """Mapeamento de `veiculos_tracionadores` (`docs/database/relational/004-frota.md`). `filial_id`
    sem `ForeignKey` física — `Filial`/`tenancy` ainda não implementada (mesmo padrão de D355)."""

    __tablename__ = "veiculos_tracionadores"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_veiculos_tracionadores_tenant_id_codigo"),
        UniqueConstraint("tenant_id", "placa", name="uq_veiculos_tracionadores_tenant_id_placa"),
        UniqueConstraint("tenant_id", "renavam", name="uq_veiculos_tracionadores_tenant_id_renavam"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String, nullable=False)
    versao: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    placa: Mapped[str] = mapped_column(String, nullable=False)
    renavam: Mapped[str] = mapped_column(String, nullable=False)
    fabricante: Mapped[str] = mapped_column(String, nullable=False)
    modelo: Mapped[str] = mapped_column(String, nullable=False)
    ano_fabricacao: Mapped[int] = mapped_column(Integer, nullable=False)
    categoria_veiculo_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("categorias_veiculo.id"), nullable=False
    )
    filial_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(String, nullable=False, default="ATIVO")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    criado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    atualizado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    excluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    excluido_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
