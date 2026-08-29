"""lote13_manutencao_checklist

Revision ID: f2b8c4a19d67
Revises: c1a7f9e2b3d4
Create Date: 2026-08-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'f2b8c4a19d67'
down_revision: Union[str, None] = 'c1a7f9e2b3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('checklists',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('codigo', sa.String(), nullable=False),
    sa.Column('tipo', sa.String(), nullable=False),
    sa.Column('referencia_tipo', sa.String(), nullable=False),
    sa.Column('referencia_id', sa.UUID(), nullable=False),
    sa.Column('veiculo_tracionador_id', sa.UUID(), nullable=False),
    sa.Column('motorista_id', sa.UUID(), nullable=True),
    sa.Column('itens', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('checklist_reprovado_id', sa.UUID(), nullable=True),
    sa.Column('criado_em', sa.DateTime(timezone=True), nullable=False),
    sa.Column('atualizado_em', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['checklist_reprovado_id'], ['checklists.id'], ),
    sa.ForeignKeyConstraint(['motorista_id'], ['motoristas.id'], ),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
    sa.ForeignKeyConstraint(['veiculo_tracionador_id'], ['veiculos_tracionadores.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'codigo', name='uq_checklists_tenant_id_codigo')
    )
    op.create_index('idx_checklists_tenant_id_referencia', 'checklists', ['tenant_id', 'referencia_tipo', 'referencia_id'], unique=False)
    op.create_index('idx_checklists_tenant_id_status', 'checklists', ['tenant_id', 'status'], unique=False)

    op.create_table('checklists_status_history',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('checklist_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('usuario_id', sa.UUID(), nullable=True),
    sa.Column('origem', sa.String(), nullable=False),
    sa.Column('observacao', sa.String(), nullable=True),
    sa.Column('data_hora', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['checklist_id'], ['checklists.id'], ),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_checklists_status_history_tenant_id', 'checklists_status_history', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_checklists_status_history_tenant_id', table_name='checklists_status_history')
    op.drop_table('checklists_status_history')
    op.drop_index('idx_checklists_tenant_id_status', table_name='checklists')
    op.drop_index('idx_checklists_tenant_id_referencia', table_name='checklists')
    op.drop_table('checklists')
