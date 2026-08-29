"""frota_veiculo_impedimentos

Revision ID: b1e4c9d27f83
Revises: 9c3e5f7a1b02
Create Date: 2026-08-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'b1e4c9d27f83'
down_revision: Union[str, None] = '9c3e5f7a1b02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ledger interno que sustenta `disponibilidade_veiculo` (D081/D247) como projeção de
    # impedimentos ativos, em vez de um status sobrescrito pelo último evento — fecha o gap de
    # "OS A + OS B abertas no mesmo veículo, fechar A libera indevidamente enquanto B segue ativa".
    # `disponibilidade_veiculo` em si não muda de forma (mesmas 6 colunas, mesmo D247) — só a
    # lógica que a escreve passa a consultar este ledger.
    op.create_table('veiculo_impedimentos',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('veiculo_tracionador_id', sa.UUID(), nullable=False),
    sa.Column('tipo', sa.String(), nullable=False),
    # Sem FK física — aponta para `viagens` ou `ordens_servico` dependendo de `tipo` (referência
    # polimórfica, mesmo padrão de `ordens_servico.origem_abertura`).
    sa.Column('referencia_id', sa.UUID(), nullable=False),
    sa.Column('motorista_id', sa.UUID(), nullable=True),
    sa.Column('implemento_id', sa.UUID(), nullable=True),
    sa.Column('iniciado_em', sa.DateTime(timezone=True), nullable=False),
    sa.Column('encerrado_em', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['implemento_id'], ['implementos.id'], ),
    sa.ForeignKeyConstraint(['motorista_id'], ['motoristas.id'], ),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
    sa.ForeignKeyConstraint(['veiculo_tracionador_id'], ['veiculos_tracionadores.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        'idx_veiculo_impedimentos_veiculo_ativo', 'veiculo_impedimentos',
        ['veiculo_tracionador_id', 'encerrado_em'], unique=False,
    )


def downgrade() -> None:
    op.drop_index('idx_veiculo_impedimentos_veiculo_ativo', table_name='veiculo_impedimentos')
    op.drop_table('veiculo_impedimentos')
