# 072 — AI Inferences (Inferências de IA)

Bounded context proprietário: `ai` (D215). `inferencias_ia` — log técnico de execução (mesmo padrão
de `eventos_fiscais`, Lote 8), Time Series/Alto volume, particionada mensalmente.

## D310 — recurso técnico, distinto de Sugestão

Inferência é **o registro técnico da execução do modelo** (entrada/saída/duração/custo/status) —
nunca confundida com Sugestão (`073`), que é o produto derivado (recomendação/justificativa/
decisão do usuário). Uma Inferência pode originar zero, uma ou várias Sugestões/Predições/
Classificações/Anomalias/Leituras de Visão Computacional (todas referenciam `inference_id`, nunca
o contrário).

## `GET /api/v1/ai/inferences`

Consulta técnica — **exposição parcial conforme RBAC** (pedido explícito, confirmado):

| Campo | Permissão exigida |
|---|---|
| `input`/`output`/`confidence_level`/`model_id`/`model_version`/`duration_ms`/`status`/`origin`/`attempt_number` | `ai.inference.view` |
| `cost` | `ai.inference.view_cost` (D267-style, autorização por campo — terceira ocorrência nesta API após `maintenance.work_order.view_cost`/Lote 6 e `financial.trip_*_value.view`/Lote 7) |

Sem `ai.inference.view_cost`, `cost` retorna `null` — mesmo tratamento de todo campo sensível já
estabelecido nesta API, nunca omitido silenciosamente do schema.

**Segurança**: `bearerAuth` + `ai.inference.view`.

**Query parameters**: `page`/`limit`, `model_id`, `status`, `origin`, `started_at__gte`/`__lte`.
Cursor pagination — `inferencias_ia` é Categoria Física Time Series/Alto volume (mesmo critério de
`044-eventos-fiscais.md`).

**Responses**: `200` (coleção cursor-paginada de `AIInference`, `ai-schemas.md`), `401`, `403`,
`500`.

## `GET /api/v1/ai/inferences/{id}`

**Responses**: `200` (`AIInference`), `401`, `403`, `404`, `500`.

## Sem `POST`/`PATCH`/`DELETE`

Toda Inferência nasce do processamento interno de `ai` (chamada real ao modelo, via adapter de
infraestrutura) — nunca de uma escrita direta do cliente HTTP, mesmo padrão de `eventos_fiscais`
(Lote 8) e `eventos_rastreamento` (Lote 9). `RBAC_MATRIX.md` confirma: só `.view`/`.view_cost`
existem, nenhum verbo de escrita.

## D167 — evidência sempre consultável

Toda Sugestão/Predição/Classificação/Anomalia/Leitura de Visão Computacional referencia sua
`inference_id` — este endpoint é o ponto único onde o usuário acessa os dados brutos (`input`/
`output`) que originaram qualquer saída de IA, nunca uma recomendação "opaca" sem acesso à
evidência.

## Como este documento cresce

Se um fluxo de IA multi-etapa (uma Inferência encadeando outra) for necessário no futuro,
`correlation_id` seria adicionado na origem (DDL) primeiro — deliberadamente não incluído nesta
rodada (`relational/012-ia.md` já registra essa decisão explicitamente).
