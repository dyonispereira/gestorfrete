"""seed_permissoes_pricing

Revision ID: e4cf03506398
Revises: 18bc06f9bb5a
Create Date: 2026-10-11 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'e4cf03506398'
down_revision: Union[str, None] = '18bc06f9bb5a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Lote 2 (`GESTORFRETE — PROMPT MESTRE`) — só `view`/`create`/`edit`. Sem `.delete`: não existe
# endpoint de exclusão de `PriceTable` nesta fase (expirar é o caminho normal, D109-consistent);
# exclusão de item usa `.edit` (mesma permissão de quem já pode mexer na tabela, sem granularidade
# extra sem separação de responsabilidade real — mesmo raciocínio de GAP P1/
# documents.fiscal_config.edit). `freight.trip.edit` (já existente) é reaproveitada para aplicar/
# remover tabela numa Viagem — nenhuma permissão nova ali.
PERMISSOES = [
    {'id': '1d9a3ec1-b5a7-496b-8a67-8e235a5b2950', 'codigo': 'pricing.price_table.view', 'nome': 'Visualizar tabela de frete', 'modulo': 'pricing'},
    {'id': '000f365a-519e-4e64-8756-ddf2d6f3c477', 'codigo': 'pricing.price_table.create', 'nome': 'Criar tabela de frete', 'modulo': 'pricing'},
    {'id': '6a3fe163-8ed5-4a1e-8e08-134e81dea1f7', 'codigo': 'pricing.price_table.edit', 'nome': 'Editar tabela de frete', 'modulo': 'pricing'},
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
