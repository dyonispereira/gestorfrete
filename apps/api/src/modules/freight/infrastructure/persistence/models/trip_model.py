from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, Computed, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class TripModel(Base):
    """Mapeamento de `viagens` (`relational/003-operacao.md`) — o agregado mais rico do sistema.
    `encerrada`/`margem_prevista` são colunas `GENERATED ALWAYS AS (...) STORED` no Postgres
    (D019/D185), já criadas via SQL bruto na migration — mapeadas aqui com `Computed(...)` só para
    o ORM saber que nunca deve incluí-las em `INSERT`/`UPDATE` (sem isso, SQLAlchemy tenta gravar
    o valor Python-side em toda escrita e o Postgres rejeita com `GeneratedAlwaysError`, achado
    rodando a suíte de integração pela primeira vez). `tabela_preco_aplicada_snapshot_id` sem FK
    física — `tabelas_preco` fora de escopo (D370)."""

    __tablename__ = "viagens"
    __table_args__ = (
        Index("idx_viagens_tenant_id_status_operacional", "tenant_id", "status_operacional"),
        Index("idx_viagens_tenant_id_motorista_id", "tenant_id", "motorista_id"),
        Index("idx_viagens_tenant_id_veiculo_id", "tenant_id", "veiculo_tracionador_id"),
        Index("idx_viagens_tenant_id_data_programada", "tenant_id", "data_programada"),
        Index("idx_viagens_tenant_id_cliente_id", "tenant_id", "cliente_id"),
        Index(
            "idx_viagens_tenant_id_encerrada", "tenant_id", "encerrada", postgresql_where=text("excluido_em IS NULL")
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String, nullable=False)
    versao: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    cliente_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False)
    motorista_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("motoristas.id"))
    veiculo_tracionador_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("veiculos_tracionadores.id")
    )

    data_programada: Mapped[date | None] = mapped_column(Date)
    janela_programada: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    status_operacional: Mapped[str] = mapped_column(String, nullable=False, default="RASCUNHO")
    status_fiscal: Mapped[str] = mapped_column(String, nullable=False, default="PENDENTE")
    status_financeiro: Mapped[str] = mapped_column(String, nullable=False, default="AGUARDANDO_FATURAMENTO")
    encerrada: Mapped[bool] = mapped_column(
        Boolean,
        Computed(
            "status_operacional = 'FINALIZADA' AND status_fiscal = 'MDFE_ENCERRADO' "
            "AND status_financeiro = 'RECEBIDA'"
        ),
        nullable=False,
    )

    nome_motorista_snapshot: Mapped[str | None] = mapped_column(String)
    placa_veiculo_snapshot: Mapped[str | None] = mapped_column(String)
    cliente_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    receita_prevista_snapshot: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    tabela_preco_aplicada_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))

    custo_previsto: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    custo_realizado: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    receita_realizada: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    margem_prevista: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2), Computed("receita_prevista_snapshot - custo_previsto")
    )
    margem_realizada: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    desvio_financeiro: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))

    km_rodado: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    criado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    atualizado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    excluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    excluido_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
