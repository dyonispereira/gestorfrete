from __future__ import annotations

import uuid

from geoalchemy2 import Geography
from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class GeofenceModel(Base):
    """Mapeamento de `cercas_eletronicas` (D122/D289) — configuração, não histórico. `centro`/
    `poligono` via `geoalchemy2.Geography` (D404). `filial_id` sem FK física (D403, mesma natureza
    de D355 — `Filial` ainda não implementada)."""

    __tablename__ = "cercas_eletronicas"
    __table_args__ = (
        UniqueConstraint("tenant_id", "nome", name="uq_cercas_eletronicas_tenant_id_nome"),
        CheckConstraint(
            "(tipo_geometria = 'CIRCULO' AND centro IS NOT NULL AND raio_metros IS NOT NULL) "
            "OR (tipo_geometria = 'POLIGONO' AND poligono IS NOT NULL)",
            name="ck_cercas_eletronicas_geometria",
        ),
        Index("idx_cercas_eletronicas_centro", "centro", postgresql_using="gist", postgresql_where=text("centro IS NOT NULL")),
        Index("idx_cercas_eletronicas_poligono", "poligono", postgresql_using="gist", postgresql_where=text("poligono IS NOT NULL")),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    tipo_geometria: Mapped[str] = mapped_column(String, nullable=False)
    centro: Mapped[str | None] = mapped_column(Geography(geometry_type="POINT", srid=4326, spatial_index=False))
    raio_metros: Mapped[float | None] = mapped_column(Numeric(10, 2))
    poligono: Mapped[str | None] = mapped_column(Geography(geometry_type="POLYGON", srid=4326, spatial_index=False))
    cliente_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("clientes.id"))
    filial_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(String, nullable=False, default="ATIVA")
