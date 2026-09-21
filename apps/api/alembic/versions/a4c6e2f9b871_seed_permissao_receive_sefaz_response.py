"""seed_permissao_receive_sefaz_response

Revision ID: a4c6e2f9b871
Revises: f28a4d9e6c17
Create Date: 2026-09-21 00:00:00.000001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a4c6e2f9b871'
down_revision: Union[str, None] = 'f28a4d9e6c17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# D397, fechado (Lote Fiscal, Parte 2.2) — POST /ctes/{id}/commands/receive-sefaz-response é o
# único jeito HTTP de simular a resposta da SEFAZ (via SandboxSefazGateway) e levar um CT-e de
# TRANSMITIDO a AUTORIZADO/DENEGADO. Mesmo padrão/tabela de c1a7f9e2b3d4.
PERMISSOES = [
    {
        'id': '2eae1a88-0914-4d84-899c-35d808343c4b', 'codigo': 'documents.cte.receive_sefaz_response',
        'nome': 'Simular resposta da SEFAZ para CT-e (sandbox)', 'modulo': 'documents',
    },
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
