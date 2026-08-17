from __future__ import annotations

import uuid

from sqlalchemy import Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class LocationOriginModel(Base):
    """Mapeamento de `origens_localizacao` — Platform Reference Data (D046), sem `tenant_id`."""

    __tablename__ = "origens_localizacao"
    __table_args__ = (UniqueConstraint("nome", name="uq_origens_localizacao_nome"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    precisao_tipica_metros: Mapped[float | None] = mapped_column(Numeric(6, 2))
