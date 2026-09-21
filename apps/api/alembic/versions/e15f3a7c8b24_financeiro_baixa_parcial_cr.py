"""financeiro_baixa_parcial_cr

Revision ID: e15f3a7c8b24
Revises: d84b2c6a9f13
Create Date: 2026-09-21 00:00:00.000001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'e15f3a7c8b24'
down_revision: Union[str, None] = 'd84b2c6a9f13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Reconciliação (Lote Financeiro, Parte 2.1, ver docs/domain/006-financeiro.md e
    # docs/database/relational/006-financeiro.md). `status` continua sa.String() — sem enum nativo
    # do Postgres nesta tabela, então PARCIALMENTE_RECEBIDO (novo valor do Enum Python) não exige
    # migração própria, só esta coluna.
    op.add_column(
        'contas_receber',
        sa.Column('valor_recebido', sa.Numeric(14, 2), nullable=False, server_default='0'),
    )
    op.alter_column('contas_receber', 'valor_recebido', server_default=None)
    op.create_check_constraint(
        'ck_contas_receber_valor_recebido', 'contas_receber', 'valor_recebido >= 0 AND valor_recebido <= valor',
    )


def downgrade() -> None:
    op.drop_constraint('ck_contas_receber_valor_recebido', 'contas_receber', type_='check')
    op.drop_column('contas_receber', 'valor_recebido')
