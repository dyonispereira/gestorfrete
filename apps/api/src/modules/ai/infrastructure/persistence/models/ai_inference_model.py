from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Computed, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class AIInferenceModel(Base):
    """Mapeamento de `inferencias_ia` (`relational/012-ia.md`) — particionada por
    `data_hora_inicio` (D201, Alto volume), criada via SQL bruto na migration com uma partição
    `DEFAULT` (mesmo padrão de `eventos_fiscais`/`heartbeats`). PK composta `(id,
    data_hora_inicio)` — Postgres exige a coluna de partição em toda chave primária. `duracao_ms` é
    `GENERATED ALWAYS AS (...) STORED` — `sqlalchemy.Computed(...)`, nunca calculado em Python
    (D382). D202-style: a DDL congelada declara `sugestoes_ia`/`predicoes_ia`/`classificacoes_ia`/
    `anomalias_detectadas`/`leituras_visao_computacional.inferencia_ia_id` como `REFERENCES
    inferencias_ia(id)`, mas Postgres exige que TODA constraint `UNIQUE` (não só a PK) de uma
    tabela particionada inclua a coluna de partição — um `UNIQUE(id)` isolado é fisicamente
    impossível aqui (testado: `FeatureNotSupportedError` real). Resolvido removendo a FK física das
    5 tabelas dependentes (`inferencia_ia_id` continua a mesma coluna UUID, sem `REFERENCES`) —
    integridade garantida pela aplicação (`AIInferenceEngine` sempre cria a Inferência antes da
    saída, na mesma transação), nunca pelo banco."""

    __tablename__ = "inferencias_ia"
    __table_args__ = (
        Index("idx_inferencias_ia_modelo_id_criado_em", "modelo_ia_id", "data_hora_inicio"),
        Index("idx_inferencias_ia_status", "tenant_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    modelo_ia_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("modelos_ia.id"), nullable=False)
    modelo_ia_versao: Mapped[str] = mapped_column(String, nullable=False)
    entrada: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    saida: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    nivel_confianca: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    data_hora_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True, nullable=False)
    data_hora_fim: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duracao_ms: Mapped[int | None] = mapped_column(
        Integer, Computed("EXTRACT(EPOCH FROM (data_hora_fim - data_hora_inicio)) * 1000"),
    )
    custo: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    numero_tentativa: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    origem: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="SUCESSO")
