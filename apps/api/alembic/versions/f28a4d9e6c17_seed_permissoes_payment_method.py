"""seed_permissoes_payment_method

Revision ID: f28a4d9e6c17
Revises: e15f3a7c8b24
Create Date: 2026-09-21 00:00:00.000001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'f28a4d9e6c17'
down_revision: Union[str, None] = 'e15f3a7c8b24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# D386, fechado (Lote Financeiro, Parte 2.1) — Forma de Pagamento nunca teve permissões próprias
# (nem endpoint HTTP, seed direto via Repository). Mesmo padrão/tabela de c1a7f9e2b3d4.
PERMISSOES = [
    {'id': 'd795e767-e011-4240-8833-d6c2761d4707', 'codigo': 'financial.payment_method.view', 'nome': 'Visualizar forma de pagamento', 'modulo': 'financial'},
    {'id': '6f97b88f-956c-46b5-b7aa-d83960dc2f29', 'codigo': 'financial.payment_method.create', 'nome': 'Criar forma de pagamento', 'modulo': 'financial'},
    {'id': 'a7135d28-8718-49af-a3ba-b3dae9204fc4', 'codigo': 'financial.payment_method.edit', 'nome': 'Editar forma de pagamento', 'modulo': 'financial'},
]

permissoes_table = sa.table(
    "permissoes",
    sa.column("id", postgresql.UUID(as_uuid=False)),
    sa.column("codigo", sa.String),
    sa.column("nome", sa.String),
    sa.column("modulo", sa.String),
    sa.column("criado_em", sa.DateTime(timezone=True)),
)


def upgrade() -> None:
    insert_stmt = postgresql.insert(permissoes_table)
    for row in PERMISSOES:
        op.execute(
            insert_stmt.values(
                id=row["id"], codigo=row["codigo"], nome=row["nome"], modulo=row["modulo"], criado_em=sa.func.now()
            ).on_conflict_do_nothing(index_elements=["codigo"])
        )


def downgrade() -> None:
    codes = [row["codigo"] for row in PERMISSOES]
    op.execute(permissoes_table.delete().where(permissoes_table.c.codigo.in_(codes)))
