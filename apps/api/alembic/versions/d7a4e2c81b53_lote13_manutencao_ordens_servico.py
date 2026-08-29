"""lote13_manutencao_ordens_servico

Revision ID: d7a4e2c81b53
Revises: f2b8c4a19d67
Create Date: 2026-08-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'd7a4e2c81b53'
down_revision: Union[str, None] = 'f2b8c4a19d67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('ordens_servico',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('codigo', sa.String(), nullable=False),
    sa.Column('veiculo_tracionador_id', sa.UUID(), nullable=False),
    sa.Column('composicao_veicular_id', sa.UUID(), nullable=True),
    sa.Column('fornecedor_executor_id', sa.UUID(), nullable=True),
    sa.Column('tipo', sa.String(), nullable=False),
    sa.Column('origem_abertura', sa.String(), nullable=False),
    sa.Column('descricao_problema', sa.String(), nullable=False),
    sa.Column('causa', sa.String(), nullable=True),
    sa.Column('causa_raiz', sa.String(), nullable=True),
    sa.Column('diagnostico_tecnico', sa.String(), nullable=True),
    sa.Column('mecanico_id', sa.UUID(), nullable=True),
    sa.Column('custo_previsto', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('custo_realizado', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('necessita_aprovacao', sa.Boolean(), nullable=False),
    sa.Column('evidencia_conclusao_exigida', sa.Boolean(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('data_inicio_execucao', sa.DateTime(timezone=True), nullable=True),
    sa.Column('data_conclusao', sa.DateTime(timezone=True), nullable=True),
    sa.Column('criado_em', sa.DateTime(timezone=True), nullable=False),
    sa.Column('criado_por', sa.UUID(), nullable=True),
    sa.Column('atualizado_em', sa.DateTime(timezone=True), nullable=False),
    sa.Column('atualizado_por', sa.UUID(), nullable=True),
    sa.Column('excluido_em', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['composicao_veicular_id'], ['composicoes_veiculares.id'], ),
    sa.ForeignKeyConstraint(['fornecedor_executor_id'], ['fornecedores.id'], ),
    sa.ForeignKeyConstraint(['mecanico_id'], ['usuarios.id'], ),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
    sa.ForeignKeyConstraint(['veiculo_tracionador_id'], ['veiculos_tracionadores.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'codigo', name='uq_ordens_servico_tenant_id_codigo')
    )
    op.create_index('idx_ordens_servico_tenant_id_veiculo_id', 'ordens_servico', ['tenant_id', 'veiculo_tracionador_id'], unique=False)
    op.create_index('idx_ordens_servico_tenant_id_status', 'ordens_servico', ['tenant_id', 'status'], unique=False)

    op.create_table('ordens_servico_status_history',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('ordem_servico_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('usuario_id', sa.UUID(), nullable=True),
    sa.Column('origem', sa.String(), nullable=False),
    sa.Column('observacao', sa.String(), nullable=True),
    sa.Column('data_hora', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['ordem_servico_id'], ['ordens_servico.id'], ),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ordens_servico_status_history_os_id', 'ordens_servico_status_history', ['ordem_servico_id', 'data_hora'], unique=False)

    op.create_table('itens_ordem_servico',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('ordem_servico_id', sa.UUID(), nullable=False),
    sa.Column('categoria_custo', sa.String(), nullable=False),
    sa.Column('descricao', sa.String(), nullable=False),
    # `peca_estoque_id` nasce sem FK física — `pecas_estoque` ainda não existe (D387-style, mesmo
    # padrão de `contas_pagar.ordem_servico_id` antes desta Lote).
    sa.Column('peca_estoque_id', sa.UUID(), nullable=True),
    sa.Column('quantidade', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('valor_unitario', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.ForeignKeyConstraint(['ordem_servico_id'], ['ordens_servico.id'], ),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_itens_ordem_servico_ordem_servico_id', 'itens_ordem_servico', ['ordem_servico_id'], unique=False)

    op.create_table('aprovacoes_custo',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('ordem_servico_id', sa.UUID(), nullable=False),
    sa.Column('nivel', sa.Integer(), nullable=False),
    sa.Column('decisao', sa.String(), nullable=False),
    sa.Column('justificativa', sa.String(), nullable=True),
    sa.Column('ator_id', sa.UUID(), nullable=False),
    sa.Column('data_hora', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['ator_id'], ['usuarios.id'], ),
    sa.ForeignKeyConstraint(['ordem_servico_id'], ['ordens_servico.id'], ),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_aprovacoes_custo_ordem_servico_id', 'aprovacoes_custo', ['ordem_servico_id', 'nivel'], unique=False)

    # D387 fechado: `contas_pagar.ordem_servico_id` nasceu sem FK física (`636bcd8e696f`) porque
    # `ordens_servico` não existia ainda — a DDL congelada já declarava a FK, só faltava a tabela.
    op.create_foreign_key(
        'contas_pagar_ordem_servico_id_fkey', 'contas_pagar', 'ordens_servico', ['ordem_servico_id'], ['id']
    )


def downgrade() -> None:
    op.drop_constraint('contas_pagar_ordem_servico_id_fkey', 'contas_pagar', type_='foreignkey')
    op.drop_index('idx_aprovacoes_custo_ordem_servico_id', table_name='aprovacoes_custo')
    op.drop_table('aprovacoes_custo')
    op.drop_index('idx_itens_ordem_servico_ordem_servico_id', table_name='itens_ordem_servico')
    op.drop_table('itens_ordem_servico')
    op.drop_index('idx_ordens_servico_status_history_os_id', table_name='ordens_servico_status_history')
    op.drop_table('ordens_servico_status_history')
    op.drop_index('idx_ordens_servico_tenant_id_status', table_name='ordens_servico')
    op.drop_index('idx_ordens_servico_tenant_id_veiculo_id', table_name='ordens_servico')
    op.drop_table('ordens_servico')
