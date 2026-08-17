# FILTERING_SORTING.md — Filtros e Ordenação

Sintaxe única para toda a API — nenhum endpoint inventa a própria (mesmo princípio de
`NAMING_CONVENTION.md`).

## Filtros — igualdade simples

```
GET /api/v1/viagens?status=EM_ANDAMENTO
GET /api/v1/viagens?tenant_id=...          -- nunca aceito (D208) — tenant nunca é filtro de query
GET /api/v1/contas-receber?data_vencimento=2026-07-30
```

Nome do parâmetro = nome da coluna (`snake_case`, `NAMING_CONVENTION.md` seção 4). Filtro por FK
usa o nome da coluna FK, não o nome do recurso relacionado:

```
GET /api/v1/canhotos?entrega_id={id}      -- correto
GET /api/v1/canhotos?entrega={id}          -- não usado
```

## Operadores (sufixo `__operador`)

| Operador | Sufixo | Exemplo |
|---|---|---|
| Igual (padrão, sem sufixo) | `eq` | `?status=ATIVO` |
| Diferente | `__neq` | `?status__neq=CANCELADA` |
| Maior que | `__gt` | `?valor__gt=1000` |
| Maior ou igual | `__gte` | `?data_programada__gte=2026-07-01` |
| Menor que | `__lt` | `?valor__lt=5000` |
| Menor ou igual | `__lte` | `?data_programada__lte=2026-07-31` |
| Em uma lista | `__in` | `?status__in=ATIVO,PENDENTE` |
| Contém (texto) | `__contains` | `?razao_social__contains=Transportes` |
| Intervalo | `__between` | `?data_programada__between=2026-07-01,2026-07-31` |

Range de data (padrão frequente o bastante para ter atalho próprio, em vez de forçar sempre
`__gte`/`__lte` combinados):

```
GET /api/v1/viagens?data_inicio=2026-07-01&data_fim=2026-07-31
```

`data_inicio`/`data_fim` como nomes de parâmetro fixos (não `data_programada__gte`/`__lte`) são
aceitos como atalho **só quando o endpoint documenta explicitamente essa dupla** — nunca inferido
implicitamente a partir do nome de uma coluna qualquer terminada em "data".

## Nem todo operador está disponível em todo campo

- `__contains` só em colunas de texto livre (nunca em `UUID`/enum — usar `eq`/`in`).
- `__gt`/`__gte`/`__lt`/`__lte`/`__between` só em colunas numéricas/data/timestamp.
- `__in` disponível em qualquer campo filtrável.

O OpenAPI de cada endpoint (Lote 2 em diante) declara exatamente quais operadores cada campo aceita
— nunca um comportamento "tente e veja se funciona".

## Ordenação

```
GET /api/v1/viagens?sort=-criado_em
GET /api/v1/viagens?sort=data_programada,-valor_servico
```

- Prefixo `-` = decrescente; ausência de prefixo = crescente.
- Múltiplos campos separados por vírgula, aplicados na ordem informada.
- Campo de ordenação precisa ser um dos já indexados para aquele recurso (`INDEXES.md` categoria
  4, "Busca operacional") — ordenar por uma coluna sem índice de suporte é uma decisão explícita do
  endpoint (documentada no OpenAPI), não um comportamento implícito de "funciona mas é lento".

## Combinação com Paginação

Filtro e ordenação sempre compõem com `PAGINATION.md` sem regra especial — a paginação (Offset ou
Cursor) se aplica ao resultado já filtrado/ordenado, nunca ao contrário.

## Como este documento cresce

Estável. Novo operador (`__isnull`, `__starts_with`, etc.) é adicionado aqui primeiro, antes de
qualquer endpoint passar a aceitá-lo — nunca um endpoint especifica sua própria sintaxe de filtro.
