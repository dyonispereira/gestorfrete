# 082 — Global Search (Busca Global)

Bounded context proprietário: nenhum próprio — busca é um agregador de leitura sobre múltiplos
bounded contexts, cada resultado permanece de propriedade do seu módulo de origem (D215 aplicado ao
nível de cada item do resultado, não ao endpoint).

## D317 — busca nunca é uma segunda superfície de autorização

**Nenhum código RBAC próprio existe para busca.** Cada tipo de resultado é filtrado exatamente pela
mesma permissão `.view`/`.view_own` que o recurso original já exige — pedido explícito do usuário
("nunca retornar resultado de uma entidade que o usuário não poderia consultar diretamente"). Isso
significa, na prática: a implementação consulta cada bounded context habilitado apenas com os
filtros de permissão do chamador já aplicados (mesmo pipeline Auth→Tenant→RBAC→Domínio de
`OPENAPI_ARCHITECTURE.md`, uma vez por tipo de entidade), nunca uma tabela de índice único que
ignore RBAC por tipo.

## `GET /api/v1/search`

**Segurança**: `bearerAuth` — sem permissão própria; a resposta é a interseção do que `q` encontra
com o que o chamador já pode ver.

**Query parameters**:

| Parâmetro | Obrigatório | Observação |
|---|---|---|
| `q` | Sim | Termo de busca — mínimo 2 caracteres |
| `types` | Não | Lista de tipos a incluir (ex.: `viagem,cliente,veiculo`) — default: todos os tipos habilitados para busca (tabela abaixo) |
| `page`/`limit` | Não | Paginação por tipo, não global (ver `meta` abaixo) |

**Responses**: `200` — resultados agrupados por tipo:

```yaml
schema:
  type: object
  properties:
    query: { type: string }
    results:
      type: array
      items:
        type: object
        properties:
          entity_type: { type: string }
          total_matches: { type: integer }
          items:
            type: array
            items:
              type: object
              properties:
                id: { $ref: "#/components/schemas/UUID" }
                label: { type: string, description: "Projeção mínima — ex.: código da Viagem, nome do Cliente. Nunca o registro completo (isso é GET no endpoint original)." }
                entity_type: { type: string }
```

`400`, `401`, `500` — **nunca `403`** (um tipo sem permissão simplesmente não aparece no
agrupamento, mesmo espírito de D294's filtragem silenciosa por subconjunto de linhas, aplicado
agora por tipo de entidade inteiro).

## Tipos habilitados nesta preparação

| Tipo | Campo buscado | Permissão aplicada |
|---|---|---|
| `viagem` | `codigo` | `freight.trip.view` / `.view_own` |
| `cliente` | `razao_social`/`cnpj` | `crm.client.view` |
| `veiculo` | `placa` | `fleet.vehicle.view` / `.view_own` |
| `motorista` | `nome`/`cpf` | `drivers.driver.view` |
| `cte` | `numero`/`chave_acesso` | `documents.cte.view` |
| `ordem_servico` | `codigo` | `maintenance.work_order.view` |

Vocabulário extensível (D120-style) — novo tipo entra aqui quando o produto pedir, nunca inferido
silenciosamente de uma tabela nova.

## Implementação — deliberadamente não normatizada

Full-text search nativo do PostgreSQL (`tsvector`/`GIN`, já usado como categoria de índice em
`INDEXES.md`) vs. um motor de busca externo (Elasticsearch/Meilisearch/Typesense) é decisão de
Backend, nunca fixada neste contrato — mesmo princípio de domínio-agnosticismo já aplicado a
`AnalyticsCube` (Lote 11) e `078-storage.md`.

## Como este documento cresce

Novo tipo de entidade buscável adiciona uma linha à tabela acima, nunca um novo endpoint —
`GET /search` permanece único e estável.
