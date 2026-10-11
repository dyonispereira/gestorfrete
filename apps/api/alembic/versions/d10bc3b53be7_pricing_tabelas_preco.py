"""pricing_tabelas_preco

Revision ID: d10bc3b53be7
Revises: 61bb63affb03
Create Date: 2026-10-11 00:00:00.000000

Lote 2 (Viagens/Fretes/Fiscal/Faturamento/Acerto de Transportadores, Parte 1) — primeira
implementação real de `modules/pricing`, até agora um esqueleto vazio. O desenho físico original
de `tabelas_preco`/`itens_tabela_preco` (`docs/database/relational/003-operacao.md`) usava
`condicao TEXT` livre; aqui os itens ganham critérios estruturados (unidade de cálculo, categoria
de veículo, faixa de distância, ajustes) porque o cálculo determinístico do Lote 2 exige campos
reais, não texto livre interpretado por humano. `direcao` (VENDA/COMPRA) é novo — o desenho
original não previa compra (frete pago a transportador), que só passou a fazer sentido com o
Acerto de Transportadores (Lote 7, GESTORFRETE — PROMPT MESTRE).

`versao` em `tabelas_preco` (mesmo padrão de `tenants.versao`) — incrementada a cada mutação pós-
criação (ativação/expiração), para que o snapshot de aplicação (migration seguinte) grave
precisamente qual versão estava vigente no momento, mesmo que só o status da tabela mude depois
(os itens em si são imutáveis assim que a tabela sai de RASCUNHO).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'd10bc3b53be7'
down_revision: Union[str, None] = '61bb63affb03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tabelas_preco',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('nome', sa.String(), nullable=False),
        sa.Column('direcao', sa.String(), nullable=False),
        sa.Column('versao', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('vigencia_inicio', sa.Date(), nullable=False),
        sa.Column('vigencia_fim', sa.Date(), nullable=True),
        sa.Column('cliente_id', sa.UUID(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='RASCUNHO'),
        sa.Column('criado_em', sa.DateTime(timezone=True), nullable=False),
        sa.Column('criado_por', sa.UUID(), nullable=True),
        sa.Column('atualizado_em', sa.DateTime(timezone=True), nullable=False),
        sa.Column('atualizado_por', sa.UUID(), nullable=True),
        sa.CheckConstraint("direcao IN ('VENDA', 'COMPRA')", name='ck_tabelas_preco_direcao'),
        sa.CheckConstraint("status IN ('RASCUNHO', 'VIGENTE', 'EXPIRADA')", name='ck_tabelas_preco_status'),
        sa.CheckConstraint(
            'vigencia_fim IS NULL OR vigencia_fim > vigencia_inicio', name='ck_tabelas_preco_vigencia'
        ),
        sa.CheckConstraint(
            "direcao = 'VENDA' OR cliente_id IS NULL", name='ck_tabelas_preco_cliente_so_venda'
        ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['cliente_id'], ['clientes.id']),
        sa.ForeignKeyConstraint(['criado_por'], ['usuarios.id']),
        sa.ForeignKeyConstraint(['atualizado_por'], ['usuarios.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_tabelas_preco_tenant_id', 'tabelas_preco', ['tenant_id'], unique=False)
    op.create_index(
        'idx_tabelas_preco_tenant_id_direcao_status', 'tabelas_preco', ['tenant_id', 'direcao', 'status'],
        unique=False,
    )

    op.create_table(
        'itens_tabela_preco',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('tabela_preco_id', sa.UUID(), nullable=False),
        sa.Column('unidade_calculo', sa.String(), nullable=False),
        sa.Column('categoria_veiculo_id', sa.UUID(), nullable=True),
        sa.Column('origem_uf', sa.String(length=2), nullable=True),
        sa.Column('destino_uf', sa.String(length=2), nullable=True),
        sa.Column('faixa_distancia_min_km', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('faixa_distancia_max_km', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('faixa_modo', sa.String(), nullable=True),
        sa.Column('valor', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('valor_minimo', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('adicional_fixo', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('desconto_fixo', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('adicional_percentual', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('desconto_percentual', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('base_percentual_descricao', sa.String(), nullable=True),
        sa.Column('criado_em', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "unidade_calculo IN ('VIAGEM', 'KM', 'TONELADA', 'KG', 'FAIXA_DISTANCIA', 'PERCENTUAL')",
            name='ck_itens_tabela_preco_unidade',
        ),
        sa.CheckConstraint('valor > 0', name='ck_itens_tabela_preco_valor_positivo'),
        sa.CheckConstraint(
            'valor_minimo IS NULL OR valor_minimo > 0', name='ck_itens_tabela_preco_valor_minimo_positivo'
        ),
        sa.CheckConstraint(
            "unidade_calculo != 'FAIXA_DISTANCIA' OR (faixa_distancia_min_km IS NOT NULL "
            "AND faixa_distancia_max_km IS NOT NULL AND faixa_distancia_max_km > faixa_distancia_min_km "
            "AND faixa_modo IN ('TARIFA_POR_KM', 'VALOR_FIXO'))",
            name='ck_itens_tabela_preco_faixa_distancia_completa',
        ),
        sa.CheckConstraint(
            "unidade_calculo != 'PERCENTUAL' OR base_percentual_descricao IS NOT NULL",
            name='ck_itens_tabela_preco_percentual_exige_base',
        ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['tabela_preco_id'], ['tabelas_preco.id']),
        sa.ForeignKeyConstraint(['categoria_veiculo_id'], ['categorias_veiculo.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_itens_tabela_preco_tenant_id', 'itens_tabela_preco', ['tenant_id'], unique=False)
    op.create_index(
        'idx_itens_tabela_preco_tabela_preco_id', 'itens_tabela_preco', ['tabela_preco_id'], unique=False
    )


def downgrade() -> None:
    op.drop_index('idx_itens_tabela_preco_tabela_preco_id', table_name='itens_tabela_preco')
    op.drop_index('idx_itens_tabela_preco_tenant_id', table_name='itens_tabela_preco')
    op.drop_table('itens_tabela_preco')
    op.drop_index('idx_tabelas_preco_tenant_id_direcao_status', table_name='tabelas_preco')
    op.drop_index('idx_tabelas_preco_tenant_id', table_name='tabelas_preco')
    op.drop_table('tabelas_preco')
