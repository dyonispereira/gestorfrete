# 044 — Eventos Fiscais

Bounded context proprietário: `documents` (D215). Endpoint técnico do módulo — `eventos_fiscais` é
log técnico bruto (D105), **distinto** dos `*StatusHistory` de negócio (`039`/`040`/`041`, D281):
Evento Fiscal registra a comunicação técnica (requisição/resposta) com SEFAZ/ANTT; StatusHistory
registra a decisão de negócio resultante.

## D277 — somente leitura para usuários

**Nenhum endpoint permite ao cliente publicar diretamente um Evento Fiscal** — nasce sempre da
integração (`documents` → Application → Integration → SEFAZ/ANTT, D278). Todo campo de
`FiscalEvent` é `readOnly`.

## `GET /api/v1/fiscal/events`

**Segurança**: `bearerAuth` + `documents.sefaz_status.view` — RBAC não tem um código dedicado a
"eventos fiscais" per se; `.sefaz_status.view` é o mais próximo semanticamente (visualizar o
resultado técnico da comunicação com a SEFAZ), reaproveitado com a lacuna documentada.

**Query parameters** (pedidos explicitamente no kickoff):

| Parâmetro | Mapeia para |
|---|---|
| `document_type` | `documento_tipo` (`CTE`/`MDFE`/`CIOT`) |
| `document_id` | `documento_id` |
| `external_protocol` | `protocolo_externo` |
| `started_at__gte`/`__lte` | `data_hora_inicio` (período) |
| `result` | `resultado` (`SUCESSO`/`FALHA`/`TIMEOUT`) |
| `origin` | `origem` |
| `attempt_number` | `numero_tentativa` |

Cursor-paginado — `eventos_fiscais` é Categoria Física Time Series/Alto volume, particionada
mensalmente (D179), mesma regra de `PAGINATION.md` já aplicada a toda tabela dessa categoria.

**Responses**: `200` (coleção cursor-paginada de `FiscalEvent`, `fiscal-schemas.md`), `401`, `403`,
`500`.

## `GET /api/v1/fiscal/events/{id}`

**Responses**: `200` (`FiscalEvent`), `401`, `403`, `404`, `500`.

## Sem `POST`/`PATCH`/`DELETE`

Reforça D277 — mesmo padrão de `030-maintenance-history.md`/`024-odometer-readings.md`. Toda linha
nasce como efeito colateral de `commands/transmit`/`commands/sign`/`commands/register` (`039`/
`041`) executando a chamada real à integração, nunca de uma escrita direta neste caminho.

## D275 — idempotência em nível de domínio, não só HTTP

`uq_eventos_fiscais_documento_protocolo` garante que a mesma combinação `documento_tipo` +
`documento_id` + `protocolo_externo` nunca duplica um Evento Fiscal — reprocessar a mesma resposta
da SEFAZ/ANTT (reentrega, timeout seguido de retry) é fisicamente impedido de criar um segundo
registro, independente do `Idempotency-Key` HTTP do comando que originou a chamada.

## Fora de escopo, não esquecido

- **Reenvio manual de um Evento Fiscal específico** (`origem = usuário`, retry): `009-FISCAL.md`
  menciona "reenvio manual" como um valor possível de `origem`, mas não há comando explícito de
  "reenviar este evento" neste lote — o reenvio acontece via `commands/transmit`/`commands/register`
  do documento pai (`039`/`041`), nunca por um endpoint dedicado a `eventos_fiscais`.

## Como este documento cresce

Se filtros adicionais forem pedidos (ex: por SLA de tempo de resposta, `duration_ms__gte`), são
aditivos — a estrutura cursor-paginada já suporta qualquer filtro sobre coluna física real (D226).
