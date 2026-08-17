from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database.orm_base import Base

# Junções N:N puras (relational/001-core.md) — nunca Aggregate Roots próprios, nunca soft delete
# (revogar é um DELETE real na linha de junção; o histórico vive em logs_auditoria, D344).

usuarios_papeis = Table(
    "usuarios_papeis",
    Base.metadata,
    Column("usuario_id", PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), primary_key=True),
    Column("papel_id", PG_UUID(as_uuid=True), ForeignKey("papeis.id"), primary_key=True),
    Column("criado_em", DateTime(timezone=True), nullable=False),
    Column("criado_por", PG_UUID(as_uuid=True)),
)

papel_permissao = Table(
    "papel_permissao",
    Base.metadata,
    Column("papel_id", PG_UUID(as_uuid=True), ForeignKey("papeis.id"), primary_key=True),
    Column("permissao_id", PG_UUID(as_uuid=True), ForeignKey("permissoes.id"), primary_key=True),
    Column("criado_em", DateTime(timezone=True), nullable=False),
    Column("criado_por", PG_UUID(as_uuid=True)),
)


class UserModel(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_usuarios_tenant_id_codigo"),
        UniqueConstraint("tenant_id", "email", name="uq_usuarios_tenant_id_email"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String, nullable=False)
    versao: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ATIVO")
    motorista_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    funcionario_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    criado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    atualizado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    excluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    excluido_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))


class RoleModel(Base):
    __tablename__ = "papeis"
    __table_args__ = (UniqueConstraint("tenant_id", "nome", name="uq_papeis_tenant_id_nome"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String, nullable=False)
    versao: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    descricao: Mapped[str | None] = mapped_column(String)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    criado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    atualizado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    excluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    excluido_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))


class PermissionModel(Base):
    """Platform Reference Data — sem `tenant_id` (D046)."""

    __tablename__ = "permissoes"
    __table_args__ = (UniqueConstraint("codigo", name="uq_permissoes_codigo"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    codigo: Mapped[str] = mapped_column(String, nullable=False)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    modulo: Mapped[str] = mapped_column(String, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SessionModel(Base):
    __tablename__ = "sessoes_acesso"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    usuario_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    data_hora_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data_hora_expiracao_prevista: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    motivo_encerramento: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ATIVA")


class EmployeeModel(Base):
    """Mapeamento de `funcionarios` (D196, `relational/002-cadastros.md`) — sem coluna
    `usuario_id`: o vínculo Funcionário↔Usuário vive inteiramente do lado de
    `usuarios.funcionario_id` (`EMPLOYEE_IMPLEMENTATION.md`)."""

    __tablename__ = "funcionarios"
    __table_args__ = (UniqueConstraint("tenant_id", "codigo", name="uq_funcionarios_tenant_id_codigo"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String, nullable=False)
    versao: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    cargo: Mapped[str] = mapped_column(String, nullable=False)
    data_admissao: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ATIVO")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    criado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    atualizado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    excluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    excluido_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
