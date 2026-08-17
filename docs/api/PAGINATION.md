# PAGINATION.md — Paginação

## Duas estratégias, escolhidas por natureza da tabela — nunca decidido endpoint a endpoint

A escolha usa exatamente a mesma distinção já fixada em
[`../database/TABLES.md`](../database/TABLES.md) coluna **Categoria Física** — não uma nova
classificação inventada aqui:

| Categoria Física | Estratégia | Motivo |
|---|---|---|
| Master Data, Transactional, Configuration, Security, Core, Analytics, AI | **Offset** (`page`/`limit`) | Volume moderado, tela administrativa típica — usuário quer "ir para a página 5", contagem total é útil e barata de calcular |
| **Time Series**, **History** | **Cursor** | Volume "Alto"/"Muito Alto" (`HIGH_VOLUME_ENTITIES.md`) — `COUNT(*)` fica caro, e o padrão de consulta real nunca é "página 47", é sempre "próximos N a partir daqui" |
| Read Model | Depende do read model — `posicoes_caixa`/`disponibilidade_veiculo` são naturalmente pequenos (1 linha por tenant/entidade), não paginam de verdade; `indicadores_consolidados` segue Offset | Read models não têm volume próprio — herdam a estratégia do que representam |
| Integration | Cursor quando o endpoint expõe fila (`filas_sincronizacao`); Offset quando é configuração (`webhooks`) | Mistura de natureza dentro da categoria — decidido pela tabela específica, não pela categoria inteira |

## Offset — formato

```
GET /api/v1/viagens?page=1&limit=50
```

```json
{
  "data": [ "..." ],
  "meta": {
    "pagination": {
      "page": 1,
      "limit": 50,
      "total_items": 1834,
      "total_pages": 37
    }
  }
}
```

- `limit` máximo por requisição: **100** (valor de partida — ajustável por medição real de carga,
  mesmo espírito de `RATE_LIMITING.md` não fixar número definitivo sem dado de produção).
- `page` começa em `1`, nunca `0` (evita ambiguidade "página 0 é a primeira ou não existe?").
- `total_items`/`total_pages` sempre presentes — se o custo de `COUNT(*)` se mostrar alto para uma
  tabela específica em produção, essa tabela migra para Cursor (decisão registrada quando
  acontecer), nunca vira `total_items` aproximado silenciosamente.

## Cursor — formato

```
GET /api/v1/posicoes-veiculo?cursor=eyJjYXB0dXJhZG9fZW0iOiIyMDI2LTA3LTMwVDEyOjAwOjAwWiJ9&limit=100
```

```json
{
  "data": [ "..." ],
  "meta": {
    "pagination": {
      "next_cursor": "eyJjYXB0dXJhZG9fZW0iOiIyMDI2LTA3LTMwVDEyOjEwOjAwWiJ9",
      "has_more": true
    }
  }
}
```

- Cursor é opaco ao cliente (Base64 de um payload interno — normalmente `{coluna_de_ordenação:
  valor, id: valor}` da última linha da página anterior) — nunca um número de offset disfarçado.
- Coluna de corte é sempre a mesma usada no índice Time Series/History já existente
  (`(entidade_id, capturado_em)` D191, `(entidade_id, data_hora)`) — paginação por cursor sem
  reaproveitar o índice já catalogado em `INDEXES.md` não é aceito.
- Sem `total_items` — pedir contagem total de uma tabela Time Series contradiz o motivo de ter
  escolhido cursor.
- `has_more: false` quando não há próxima página — cliente para de pedir, não infere pelo tamanho
  da página retornada (a última página pode coincidentemente ter `limit` itens cheios).

## O que nunca muda por endpoint

- Nome dos parâmetros (`page`/`limit` ou `cursor`/`limit`) é sempre o mesmo em toda API — nenhum
  endpoint usa `per_page`/`size`/`offset` como sinônimo.
- `meta.pagination` sempre dentro do mesmo envelope de coleção (`OPENAPI_ARCHITECTURE.md` seção 3),
  nunca espalhado em headers customizados (`X-Total-Count` etc. não são usados aqui).

## Como este documento cresce

Estável. Se uma tabela crescer de volume o suficiente para trocar de estratégia (Offset→Cursor), é
uma mudança de contrato potencialmente incompatível — passa por `VERSIONING.md` (nova versão) se
algum cliente já depender de `total_items` daquele endpoint especificamente.
