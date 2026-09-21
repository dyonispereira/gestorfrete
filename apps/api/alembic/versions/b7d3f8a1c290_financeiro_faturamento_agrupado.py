"""financeiro_faturamento_agrupado

Revision ID: b7d3f8a1c290
Revises: a4c6e2f9b871
Create Date: 2026-09-22 00:00:00.000001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

revision: str = 'b7d3f8a1c290'
down_revision: Union[str, None] = 'a4c6e2f9b871'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Reconciliação (Lote Financeiro, Parte 3 — Faturamento Agrupado, ver
    # docs/domain/006-financeiro.md e docs/database/relational/006-financeiro.md). Substitui
    # `faturas.viagem_id` (1 Fatura → 1 Viagem) por `fatura_viagens` (1 Fatura → N Viagens).
    op.create_table(
        'fatura_viagens',
        sa.Column('id', PG_UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', PG_UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('fatura_id', PG_UUID(as_uuid=True), sa.ForeignKey('faturas.id'), nullable=False),
        sa.Column('viagem_id', PG_UUID(as_uuid=True), sa.ForeignKey('viagens.id'), nullable=False),
        sa.Column('valor', sa.Numeric(14, 2), nullable=False),
        sa.Column('criado_em', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('fatura_id', 'viagem_id', name='uq_fatura_viagens_fatura_id_viagem_id'),
        sa.CheckConstraint('valor > 0', name='ck_fatura_viagens_valor_positivo'),
    )
    op.create_index('idx_fatura_viagens_tenant_id_viagem_id', 'fatura_viagens', ['tenant_id', 'viagem_id'])
    op.create_index('idx_fatura_viagens_fatura_id', 'fatura_viagens', ['fatura_id'])

    op.add_column('faturas', sa.Column('valor_bruto', sa.Numeric(14, 2), nullable=True))
    op.add_column('faturas', sa.Column('valor_ajuste', sa.Numeric(14, 2), nullable=False, server_default='0'))
    op.add_column('faturas', sa.Column('motivo_ajuste', sa.String(), nullable=True))
    op.alter_column('faturas', 'valor_ajuste', server_default=None)

    # Backfill: qualquer Fatura por viagem já existente vira uma fatura_viagens (o próprio
    # valor_total, já que não havia itemização antes); valor_bruto = valor_total nesses casos.
    # Ambiente de desenvolvimento — sem dado real conhecido, mas o backfill é correto de qualquer forma.
    op.execute(
        """
        INSERT INTO fatura_viagens (id, tenant_id, fatura_id, viagem_id, valor, criado_em)
        SELECT gen_random_uuid(), tenant_id, id, viagem_id, valor_total, criado_em
        FROM faturas WHERE viagem_id IS NOT NULL
        """
    )
    op.execute("UPDATE faturas SET valor_bruto = valor_total WHERE viagem_id IS NOT NULL")
    op.execute("UPDATE faturas SET valor_bruto = valor_total WHERE viagem_id IS NULL")
    op.alter_column('faturas', 'valor_bruto', nullable=False)

    op.drop_constraint('ck_faturas_origem', 'faturas', type_='check')
    op.drop_column('faturas', 'viagem_id')


def downgrade() -> None:
    op.add_column('faturas', sa.Column('viagem_id', PG_UUID(as_uuid=True), sa.ForeignKey('viagens.id'), nullable=True))
    op.execute(
        """
        UPDATE faturas SET viagem_id = fv.viagem_id
        FROM (SELECT DISTINCT ON (fatura_id) fatura_id, viagem_id FROM fatura_viagens ORDER BY fatura_id, criado_em) fv
        WHERE faturas.id = fv.fatura_id
        """
    )
    op.create_check_constraint('ck_faturas_origem', 'faturas', 'viagem_id IS NOT NULL OR entrega_id IS NOT NULL')
    op.drop_column('faturas', 'motivo_ajuste')
    op.drop_column('faturas', 'valor_ajuste')
    op.drop_column('faturas', 'valor_bruto')
    op.drop_index('idx_fatura_viagens_fatura_id', table_name='fatura_viagens')
    op.drop_index('idx_fatura_viagens_tenant_id_viagem_id', table_name='fatura_viagens')
    op.drop_table('fatura_viagens')
