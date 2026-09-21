"""manutencao_os_centro_custo_plano_contas

Revision ID: c2f7a91b4e58
Revises: b1e4c9d27f83
Create Date: 2026-08-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'c2f7a91b4e58'
down_revision: Union[str, None] = 'b1e4c9d27f83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Reconciliação (Lote Financeiro, Parte 1, ver docs/database/relational/005-manutencao.md) —
    # ambos opcionais; junto com fornecedor_executor_id, habilitam a Conta a Pagar automática no
    # fechamento da OS (006-financeiro.md).
    op.add_column('ordens_servico', sa.Column('centro_custo_id', sa.UUID(), nullable=True))
    op.add_column('ordens_servico', sa.Column('plano_contas_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'ordens_servico_centro_custo_id_fkey', 'ordens_servico', 'centros_custo', ['centro_custo_id'], ['id']
    )
    op.create_foreign_key(
        'ordens_servico_plano_contas_id_fkey', 'ordens_servico', 'plano_contas', ['plano_contas_id'], ['id']
    )


def downgrade() -> None:
    op.drop_constraint('ordens_servico_plano_contas_id_fkey', 'ordens_servico', type_='foreignkey')
    op.drop_constraint('ordens_servico_centro_custo_id_fkey', 'ordens_servico', type_='foreignkey')
    op.drop_column('ordens_servico', 'plano_contas_id')
    op.drop_column('ordens_servico', 'centro_custo_id')
