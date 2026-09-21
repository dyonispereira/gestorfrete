"""financeiro_competencia_dimensoes_cp

Revision ID: d84b2c6a9f13
Revises: c2f7a91b4e58
Create Date: 2026-08-30 00:00:00.000001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'd84b2c6a9f13'
down_revision: Union[str, None] = 'c2f7a91b4e58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Reconciliação (Lote Financeiro, Parte 1, ver docs/database/relational/006-financeiro.md).
    # NOT NULL direto — tabelas vazias em todo ambiente que já rodou a suíte de testes até aqui,
    # nenhum backfill necessário.
    op.add_column('contas_pagar', sa.Column('competencia', sa.Date(), nullable=False))
    op.add_column('contas_pagar', sa.Column('veiculo_tracionador_id', sa.UUID(), nullable=True))
    op.add_column('contas_pagar', sa.Column('motorista_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'contas_pagar_veiculo_tracionador_id_fkey', 'contas_pagar', 'veiculos_tracionadores',
        ['veiculo_tracionador_id'], ['id'],
    )
    op.create_foreign_key('contas_pagar_motorista_id_fkey', 'contas_pagar', 'motoristas', ['motorista_id'], ['id'])

    op.add_column('contas_receber', sa.Column('competencia', sa.Date(), nullable=False))


def downgrade() -> None:
    op.drop_column('contas_receber', 'competencia')

    op.drop_constraint('contas_pagar_motorista_id_fkey', 'contas_pagar', type_='foreignkey')
    op.drop_constraint('contas_pagar_veiculo_tracionador_id_fkey', 'contas_pagar', type_='foreignkey')
    op.drop_column('contas_pagar', 'motorista_id')
    op.drop_column('contas_pagar', 'veiculo_tracionador_id')
    op.drop_column('contas_pagar', 'competencia')
