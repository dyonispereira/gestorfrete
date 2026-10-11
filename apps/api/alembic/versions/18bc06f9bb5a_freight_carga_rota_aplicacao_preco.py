"""freight_carga_rota_aplicacao_preco

Revision ID: 18bc06f9bb5a
Revises: d10bc3b53be7
Create Date: 2026-10-11 00:05:00.000000

Lote 2, Parte 2 — evolui `viagens` com dados operacionais de carga/percurso (origem, destino,
distância prevista, peso, tipo de carga) hoje inexistentes em qualquer entidade (investigado antes
de desenhar: `itens_carga`/`romaneios` só existem a partir da Coleta real, D005/D006 — tarde demais
para o cálculo de frete PREVISTO na programação; estes campos novos são o par PREVISTO de
`itens_carga`, nunca um duplicado — mesmo padrão já usado para custo/receita previsto×realizado).

`toneladas_carga` é `GENERATED ALWAYS AS (peso_carga_kg / 1000) STORED` (mesmo padrão de
`margem_prevista`/`encerrada`, D019/D185) — nunca dessincroniza de `peso_carga_kg`.

`aplicacoes_tabela_preco_viagem` é uma entidade filha append-only (nunca UPDATE, nunca DELETE
físico — mesmo princípio D109 já usado para documentos fiscais/financeiros): cada aplicação de
Tabela de Frete numa Viagem gera uma linha nova com o snapshot completo da negociação (tabela,
item, versão, unidade, quantidade usada, tarifa, mínimo, ajustes, valor final). Remover uma
aplicação marca `removido_em`/`removido_por` na própria linha — nunca apaga a evidência.
`viagens.aplicacao_tabela_preco_atual_id` aponta para a linha ativa (ou NULL); a coluna já
existente `viagens.tabela_preco_aplicada_snapshot_id` continua apontando direto para
`tabelas_preco.id`, inalterada — mantém o contrato já documentado (D370), só ganha um dado
companheiro mais rico.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '18bc06f9bb5a'
down_revision: Union[str, None] = 'd10bc3b53be7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('viagens', sa.Column('origem_cidade', sa.String(), nullable=True))
    op.add_column('viagens', sa.Column('origem_uf', sa.String(length=2), nullable=True))
    op.add_column('viagens', sa.Column('destino_cidade', sa.String(), nullable=True))
    op.add_column('viagens', sa.Column('destino_uf', sa.String(length=2), nullable=True))
    op.add_column('viagens', sa.Column('distancia_prevista_km', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('viagens', sa.Column('peso_carga_kg', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('viagens', sa.Column('tipo_carga', sa.String(), nullable=True))
    op.add_column('viagens', sa.Column('quantidade_carga', sa.Integer(), nullable=True))
    op.add_column('viagens', sa.Column('unidade_quantidade_carga', sa.String(), nullable=True))
    op.add_column('viagens', sa.Column('aplicacao_tabela_preco_atual_id', sa.UUID(), nullable=True))

    op.create_check_constraint(
        'ck_viagens_distancia_prevista_positiva', 'viagens',
        'distancia_prevista_km IS NULL OR distancia_prevista_km > 0',
    )
    op.create_check_constraint(
        'ck_viagens_peso_carga_positivo', 'viagens', 'peso_carga_kg IS NULL OR peso_carga_kg > 0'
    )
    op.create_check_constraint(
        'ck_viagens_quantidade_carga_positiva', 'viagens',
        'quantidade_carga IS NULL OR quantidade_carga > 0',
    )

    # `toneladas_carga` — mesmo padrão de `margem_prevista`/`encerrada`: coluna GERADA, fora da
    # lista de colunas do SQLAlchemy declarativo (que não expressa GENERATED), criada via SQL bruto.
    op.execute(
        """
        ALTER TABLE viagens ADD COLUMN toneladas_carga NUMERIC(12, 3) GENERATED ALWAYS AS (
            peso_carga_kg / 1000
        ) STORED
        """
    )

    op.create_table(
        'aplicacoes_tabela_preco_viagem',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('viagem_id', sa.UUID(), nullable=False),
        sa.Column('tabela_preco_id', sa.UUID(), nullable=False),
        sa.Column('item_tabela_preco_id', sa.UUID(), nullable=False),
        sa.Column('tabela_preco_versao', sa.Integer(), nullable=False),
        sa.Column('direcao', sa.String(), nullable=False),
        sa.Column('unidade_calculo', sa.String(), nullable=False),
        sa.Column('quantidade_utilizada', sa.Numeric(precision=14, scale=3), nullable=True),
        sa.Column('base_percentual_valor', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('tarifa_aplicada', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('valor_minimo_aplicado', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('adicional_fixo_aplicado', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('desconto_fixo_aplicado', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('adicional_percentual_aplicado', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('desconto_percentual_aplicado', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('valor_calculado_bruto', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('valor_final', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('aplicado_em', sa.DateTime(timezone=True), nullable=False),
        sa.Column('aplicado_por', sa.UUID(), nullable=False),
        sa.Column('removido_em', sa.DateTime(timezone=True), nullable=True),
        sa.Column('removido_por', sa.UUID(), nullable=True),
        sa.CheckConstraint("direcao IN ('VENDA', 'COMPRA')", name='ck_aplicacoes_tabela_preco_direcao'),
        sa.CheckConstraint('valor_final >= 0', name='ck_aplicacoes_tabela_preco_valor_final_nao_negativo'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['viagem_id'], ['viagens.id']),
        sa.ForeignKeyConstraint(['tabela_preco_id'], ['tabelas_preco.id']),
        sa.ForeignKeyConstraint(['item_tabela_preco_id'], ['itens_tabela_preco.id']),
        sa.ForeignKeyConstraint(['aplicado_por'], ['usuarios.id']),
        sa.ForeignKeyConstraint(['removido_por'], ['usuarios.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'idx_aplicacoes_tabela_preco_viagem_viagem_id', 'aplicacoes_tabela_preco_viagem', ['viagem_id'],
        unique=False,
    )
    op.create_index(
        'idx_aplicacoes_tabela_preco_viagem_tenant_id', 'aplicacoes_tabela_preco_viagem', ['tenant_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('idx_aplicacoes_tabela_preco_viagem_tenant_id', table_name='aplicacoes_tabela_preco_viagem')
    op.drop_index('idx_aplicacoes_tabela_preco_viagem_viagem_id', table_name='aplicacoes_tabela_preco_viagem')
    op.drop_table('aplicacoes_tabela_preco_viagem')

    op.execute('ALTER TABLE viagens DROP COLUMN toneladas_carga')
    op.drop_constraint('ck_viagens_quantidade_carga_positiva', 'viagens')
    op.drop_constraint('ck_viagens_peso_carga_positivo', 'viagens')
    op.drop_constraint('ck_viagens_distancia_prevista_positiva', 'viagens')

    op.drop_column('viagens', 'aplicacao_tabela_preco_atual_id')
    op.drop_column('viagens', 'unidade_quantidade_carga')
    op.drop_column('viagens', 'quantidade_carga')
    op.drop_column('viagens', 'tipo_carga')
    op.drop_column('viagens', 'peso_carga_kg')
    op.drop_column('viagens', 'distancia_prevista_km')
    op.drop_column('viagens', 'destino_uf')
    op.drop_column('viagens', 'destino_cidade')
    op.drop_column('viagens', 'origem_uf')
    op.drop_column('viagens', 'origem_cidade')
