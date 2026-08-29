"""lote13_manutencao_os_hodometro

Revision ID: 9c3e5f7a1b02
Revises: d7a4e2c81b53
Create Date: 2026-08-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '9c3e5f7a1b02'
down_revision: Union[str, None] = 'd7a4e2c81b53'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Reconciliação (ver docs/database/relational/005-manutencao.md) — denormalização de exibição;
    # a leitura real e imutável, quando informada, vive em `leituras_hodometro` (fleet), com
    # `origem = 'ORDEM_SERVICO'` (nenhuma migração necessária lá — `origem` é `String`, não ENUM
    # nativo). Não há migração de `disponibilidade_veiculo`/`fleet` — o projetor que a escreve já
    # existia, só passou a ser chamado.
    op.add_column('ordens_servico', sa.Column('hodometro_abertura_km', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('ordens_servico', sa.Column('hodometro_conclusao_km', sa.Numeric(precision=10, scale=2), nullable=True))


def downgrade() -> None:
    op.drop_column('ordens_servico', 'hodometro_conclusao_km')
    op.drop_column('ordens_servico', 'hodometro_abertura_km')
