# SOFT_DELETE_MODEL.md — Modelo Físico de Exclusão Lógica

Implementação física de D001 (nenhuma entidade excluída fisicamente — decisão de fundação do
projeto) e D177.

## Regra (D177)

Toda tabela de negócio tem:

```sql
excluido_em    TIMESTAMPTZ,
excluido_por    UUID REFERENCES usuarios(id)
```

Ambas nuláveis — `NULL` significa "não baixado", qualquer valor em `excluido_em` significa "baixado
logicamente nesta data/hora, por este usuário". A aplicação **nunca** executa `DELETE FROM` em
tabela de negócio — apenas `UPDATE ... SET excluido_em = now(), excluido_por = :usuario`.

## Soft delete não é o mesmo que Status

Distinção importante, para não confundir os dois mecanismos:

| Mecanismo | Responde | Exemplo |
|---|---|---|
| `STATUS` (Enum da própria entidade) | "Qual a situação de negócio atual?" | Veículo `Ativo`/`Inativo` (ainda existe, só não opera mais) |
| `excluido_em`/`excluido_por` | "Este registro foi removido do sistema?" | Um cadastro criado por engano, removido antes de qualquer uso real |

Exemplo do próprio pedido original desta sprint — veículo vendido:

```
Antes:  status = 'ATIVO',   excluido_em = NULL
Depois: status = 'INATIVO', excluido_em = NULL   -- continua existindo, só não está mais em uso
```

`excluido_em` só deixa de ser `NULL` quando o registro em si precisa sair de circulação (ex:
duplicidade de cadastro, erro de digitação corrigido por remoção do registro errado) — nunca como
sinônimo de "parou de operar". Confundir os dois geraria o problema clássico que D001 existe para
evitar: perder o histórico de algo que só mudou de status, achando que foi "excluído".

## Toda consulta filtra por `excluido_em IS NULL`

Assim como toda consulta filtra por `tenant_id` (D005/D006,
[`TENANCY_MODEL.md`](./TENANCY_MODEL.md)), toda consulta de listagem/detalhe também filtra
`WHERE excluido_em IS NULL` por padrão — exceção explícita apenas em telas de auditoria/suporte que
precisam enxergar registros baixados.

## Exceções (tabelas sem soft delete)

Duas categorias não têm `excluido_em`/`excluido_por`, por motivos opostos:

1. **Nunca podem ser removidas, nem logicamente** — `logs_auditoria` (ver
   [`AUDIT_MODEL.md`](./AUDIT_MODEL.md)): soft delete implicaria a possibilidade de "esconder" um
   registro de auditoria, o que já é proibido por D109 de forma mais rígida que o soft delete comum.
2. **Entidades Históricas append-only** (D037) — ex: `posicoes_veiculo`, `leituras_telemetria`,
   `medicoes_pneu`: uma leitura de sensor não é "baixada", ela simplesmente é um fato que aconteceu;
   não existe conceito de negócio para "remover" uma leitura passada.

Nenhuma outra tabela de negócio fica de fora desta regra — se uma nova exceção for identificada
durante o Modelo Relacional, ela é registrada explicitamente no arquivo `relational/NNN-
categoria.md` correspondente, com justificativa, mesmo padrão de D104 (todo gap gera decisão).

## Índice

Toda tabela de negócio tem um índice parcial cobrindo o caso comum:

```sql
CREATE INDEX idx_motoristas_tenant_id_ativo
    ON motoristas (tenant_id)
    WHERE excluido_em IS NULL;
```

Índices parciais (`WHERE excluido_em IS NULL`) são preferidos a incluir `excluido_em` como coluna do
índice composto — a grande maioria das consultas só quer registros ativos, então o índice parcial é
menor e mais rápido que um índice completo filtrado depois.

## Como este documento cresce

Regra estável. Exceções (Time Series/auditoria) já listadas acima cobrem o que se conhece hoje;
novas exceções só entram aqui com justificativa registrada.
