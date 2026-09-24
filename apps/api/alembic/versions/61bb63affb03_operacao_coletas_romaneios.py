"""operacao_coletas_romaneios

Revision ID: 61bb63affb03
Revises: b7d3f8a1c290
Create Date: 2026-09-23 00:00:00.000000

V1 Operational Hardening, Parte 2/3 — `coletas` e `romaneios`/`itens_carga` já estavam
documentadas em `docs/domain/002-operacao.md` e com DDL congelado em
`docs/database/relational/003-operacao.md` desde o lote de Operação/Viagens; só nunca haviam
ganhado migration própria porque as transições que dependem delas (`EM_DESLOCAMENTO → CARREGANDO`,
`CARREGANDO → EM_TRANSITO`) estavam deliberadamente fora de escopo (`018-trip-status.md`,
`015-trip-deliveries.md`, seção "Fora de escopo"). Nenhuma tabela/coluna nova em relação ao DDL já
congelado.
"""
from typing import Sequence, Union

from alembic import op
import geoalchemy2
import sqlalchemy as sa

revision: str = '61bb63affb03'
down_revision: Union[str, None] = 'b7d3f8a1c290'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('coletas',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('viagem_id', sa.UUID(), nullable=False),
    sa.Column('data_hora', sa.DateTime(timezone=True), nullable=False),
    sa.Column('local', geoalchemy2.types.Geography(geometry_type='POINT', srid=4326, spatial_index=False, from_text='ST_GeogFromText', name='geography'), nullable=True),
    sa.Column('conferencia_ok', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
    sa.ForeignKeyConstraint(['viagem_id'], ['viagens.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_coletas_viagem_id', 'coletas', ['viagem_id'], unique=False)

    op.create_table('romaneios',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('viagem_id', sa.UUID(), nullable=False),
    sa.Column('numero_documento', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
    sa.ForeignKeyConstraint(['viagem_id'], ['viagens.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    op.create_table('itens_carga',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('tenant_id', sa.UUID(), nullable=False),
    sa.Column('romaneio_id', sa.UUID(), nullable=False),
    sa.Column('descricao', sa.String(), nullable=False),
    sa.Column('peso', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('quantidade', sa.Integer(), nullable=False),
    sa.CheckConstraint('peso > 0', name='ck_itens_carga_peso_positivo'),
    sa.CheckConstraint('quantidade > 0', name='ck_itens_carga_quantidade_positiva'),
    sa.ForeignKeyConstraint(['romaneio_id'], ['romaneios.id'], ),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_itens_carga_tenant_id', 'itens_carga', ['tenant_id'], unique=False)
    op.create_index('idx_itens_carga_romaneio_id', 'itens_carga', ['romaneio_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_itens_carga_romaneio_id', table_name='itens_carga')
    op.drop_index('idx_itens_carga_tenant_id', table_name='itens_carga')
    op.drop_table('itens_carga')
    op.drop_table('romaneios')
    op.drop_index('idx_coletas_viagem_id', table_name='coletas')
    op.drop_table('coletas')
