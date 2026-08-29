from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base


class OrdemServicoModel(Base):
    """Mapeamento de `ordens_servico` (`relational/005-manutencao.md`). Sem soft delete cablado
    nesta Lote — `excluido_em` existe na DDL congelada mas nenhum comando a define (não existe
    `maintenance.work_order.delete` na matriz RBAC)."""

    __tablename__ = "ordens_servico"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_ordens_servico_tenant_id_codigo"),
        Index("idx_ordens_servico_tenant_id_veiculo_id", "tenant_id", "veiculo_tracionador_id"),
        Index("idx_ordens_servico_tenant_id_status", "tenant_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String, nullable=False)
    veiculo_tracionador_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("veiculos_tracionadores.id"), nullable=False
    )
    composicao_veicular_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("composicoes_veiculares.id")
    )
    fornecedor_executor_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("fornecedores.id"))
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    origem_abertura: Mapped[str] = mapped_column(String, nullable=False, default="MANUAL")
    descricao_problema: Mapped[str] = mapped_column(String, nullable=False)
    causa: Mapped[str | None] = mapped_column(String)
    causa_raiz: Mapped[str | None] = mapped_column(String)
    diagnostico_tecnico: Mapped[str | None] = mapped_column(String)
    mecanico_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id"))
    custo_previsto: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    custo_realizado: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    necessita_aprovacao: Mapped[bool] = mapped_column(nullable=False, default=False)
    evidencia_conclusao_exigida: Mapped[bool] = mapped_column(nullable=False, default=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ABERTA")
    data_inicio_execucao: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    data_conclusao: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    criado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    atualizado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    excluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OrdemServicoStatusHistoryModel(Base):
    """Mapeamento de `ordens_servico_status_history` (D017/D018)."""

    __tablename__ = "ordens_servico_status_history"
    __table_args__ = (Index("idx_ordens_servico_status_history_os_id", "ordem_servico_id", "data_hora"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    ordem_servico_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ordens_servico.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String, nullable=False)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    origem: Mapped[str] = mapped_column(String, nullable=False)
    observacao: Mapped[str | None] = mapped_column(String)
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
