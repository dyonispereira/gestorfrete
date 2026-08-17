# components/parameters.md — Parâmetros Reutilizáveis

Todo parâmetro comum a múltiplos endpoints — path, query, header — vive aqui, referenciado por
`$ref`, nunca redefinido inline (mesmo princípio de `schemas.md`/`responses.md`).

## Path

### `IdPathParam`

```yaml
IdPathParam:
  name: id
  in: path
  required: true
  schema:
    $ref: "#/components/schemas/UUID"
  description: Identificador técnico do recurso (D175) — chave primária, nunca exibida como
    "principal" na UI, mas é o identificador de endereçamento REST.
```

## Query — paginação (Offset, `PAGINATION.md`)

Todo recurso deste lote é Master Data/Configuration (Categoria Física, `TABLES.md`) — Offset é a
estratégia usada em toda listagem, nunca Cursor (reservado a Time Series/History, nenhum presente
aqui).

### `PageParam`

```yaml
PageParam:
  name: page
  in: query
  required: false
  schema: { type: integer, minimum: 1, default: 1 }
```

### `LimitParam`

```yaml
LimitParam:
  name: limit
  in: query
  required: false
  schema: { type: integer, minimum: 1, maximum: 100, default: 50 }
```

## Query — filtros específicos deste lote (`FILTERING_SORTING.md`)

### `StatusFilterParam`

```yaml
StatusFilterParam:
  name: status
  in: query
  required: false
  schema: { type: string }
  description: Filtro de igualdade — valores válidos dependem do enum do recurso (documentado em
    cada endpoint).
```

### `SearchParam`

```yaml
SearchParam:
  name: search
  in: query
  required: false
  schema: { type: string }
  description: Busca textual livre (equivalente a `__contains` em múltiplos campos relevantes do
    recurso — nome/e-mail/código). Implementação exata (quais campos) documentada por endpoint.
```

### `SortParam`

```yaml
SortParam:
  name: sort
  in: query
  required: false
  schema: { type: string }
  example: "-created_at"
  description: "FILTERING_SORTING.md — prefixo `-` para decrescente, múltiplos campos separados
    por vírgula."
```

### `ExpandParam`

```yaml
ExpandParam:
  name: expand
  in: query
  required: false
  schema:
    type: array
    items: { type: string }
  description: Expande referências que normalmente vêm só como ID (ex.: `?expand=roles` em
    GET /users/{id} devolve RoleSummary em vez de só o array de IDs). Lista de valores aceitos
    documentada por endpoint — nunca um "expand tudo" implícito.
```

## Headers

### `IdempotencyKeyHeader`

```yaml
IdempotencyKeyHeader:
  name: Idempotency-Key
  in: header
  required: false
  schema: { type: string, format: uuid }
  description: "IDEMPOTENCY.md — obrigatório nos endpoints marcados como tal em cada documento de
    módulo (nenhum comando crítico neste lote de Identidade exige, mas o parâmetro é declarado
    aqui para reuso a partir do Lote 3)."
```

### `CorrelationIdHeader`

```yaml
CorrelationIdHeader:
  name: X-Correlation-Id
  in: header
  required: false
  schema: { type: string, format: uuid }
  description: "OPENAPI_ARCHITECTURE.md seção 4 — se ausente, o Backend gera um novo e devolve na
    resposta."
```

## Como este documento cresce

Novo filtro/parâmetro (Lote 3 em diante) só é definido inline num endpoint quando é genuinamente
específico daquele recurso (ex.: `?data_inicio`/`?data_fim` de Viagem) — qualquer parâmetro usado
por 2+ endpoints migra para cá.
