from __future__ import annotations

import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import DateTime, ForeignKey, Index, Numeric, SmallInteger
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class VehiclePositionModel(Base):
    """Mapeamento de `posicoes_veiculo` (D191) — Time Series particionada por `capturado_em` (SQL
    bruto na migration, mesmo padrão de `eventos_fiscais`/`logs_auditoria`). PK composta
    `(id, capturado_em)` — Postgres exige a coluna de partição na PK. `localizacao` via
    `geoalchemy2.Geography` (D404); leitura sempre via `ST_X`/`ST_Y` explícitos no repositório,
    nunca desserialização de WKB em Python. Sem FK física em `veiculo_tracionador_id`/
    `equipamento_rastreamento_id` — mesma exceção de tabela particionada de `AUDIT_MODEL.md`."""

    __tablename__ = "posicoes_veiculo"
    __table_args__ = (
        Index("idx_posicoes_veiculo_veiculo_id_capturado_em", "veiculo_tracionador_id", "capturado_em"),
        Index("idx_posicoes_veiculo_localizacao", "localizacao", postgresql_using="gist"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    veiculo_tracionador_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    equipamento_rastreamento_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    localizacao: Mapped[str] = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=False), nullable=False
    )
    origem_localizacao_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("origens_localizacao.id"), nullable=False
    )
    precisao_metros: Mapped[float | None] = mapped_column(Numeric(6, 2))
    numero_satelites: Mapped[int | None] = mapped_column(SmallInteger)
    hdop: Mapped[float | None] = mapped_column(Numeric(4, 2))
    nivel_confianca: Mapped[float | None] = mapped_column(Numeric(5, 2))
    capturado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True, nullable=False)
    recebido_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
