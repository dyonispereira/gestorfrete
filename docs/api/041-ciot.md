# 041 — CIOT (Código Identificador da Operação de Transporte)

Bounded context proprietário: `documents` (D215). Aplicável só quando a Viagem envolve motorista
autônomo (TAC) — `ciots.motorista_id` exige `TIPO_VINCULO = AUTONOMO` (validação de aplicação).
**CIOT nunca é um atributo simples da Viagem** — entidade própria, com `protocolo_antt` e
`eventos_fiscais` (`documento_tipo = CIOT`) distintos do fluxo SEFAZ de CT-e/MDF-e.

## `GET /api/v1/ciots`

**Segurança**: `bearerAuth` + `documents.ciot.view`.

**Query parameters**: `page`/`limit`, `trip_id` (`viagem_id`), `driver_id` (`motorista_id`),
`status`.

**Responses**: `200` (`Pagination` de `CIOT`, `fiscal-schemas.md`), `401`, `403`, `500`.

## `GET /api/v1/ciots/{id}`

**Responses**: `200` (`CIOT`), `401`, `403`, `404`, `500`.

## `POST /api/v1/ciots`

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          trip_id: { $ref: "components/schemas.md#/UUID" }
          driver_id: { $ref: "components/schemas.md#/UUID" }
        required: [trip_id, driver_id]
```

`status` nasce `PENDENTE`. `driver_id` deve referenciar Motorista com vínculo `AUTONOMO` — `422`
caso contrário (`FISCAL_CIOT_DRIVER_NOT_AUTONOMOUS`).

**Segurança**: `documents.ciot.register` — `RBAC_MATRIX.md` §7.17 não tem `documents.ciot.create`
dedicado; `.register` cobre criação+registro como uma responsabilidade única (mesmo raciocínio de
`documents.cte.issue`/D240-precedente — o ciclo de CIOT é simples o bastante para não separar
"criar" de "registrar" em códigos distintos).

**Responses**: `201` (`CIOT`), `400`, `401`, `403`, `404` (Viagem/Motorista não existe), `422` —
`FISCAL_CIOT_DRIVER_NOT_AUTONOMOUS`, `500`.

## `commands/register`

`PENDENTE → REGISTRADO`. Submete à ANTT — atribui `ciot_code`/`antt_protocol`.

**Segurança**: `documents.ciot.register`. **Idempotency-Key**: obrigatório (D211/D275 — `protocolo_
antt` é a segunda camada de idempotência, `uq_ciots_protocolo_antt`).

**Responses**: `200` (`CIOT`, D238), `401`, `403`, `404`, `409` — `FISCAL_CIOT_INVALID_TRANSITION`,
`500`, `502` — `FISCAL_ANTT_UNAVAILABLE`.

## `commands/cancel`

`PENDENTE`/`REGISTRADO → CANCELADO`. Só antes do início da Viagem (`009-FISCAL.md`: "CANCELADO como
exceção antes do início da viagem") — `409` se a Viagem já estiver `EM_DESLOCAMENTO` ou posterior.

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          notes: { type: string }
        required: [notes]
```

**Segurança**: `documents.ciot.cancel`. **Idempotency-Key**: obrigatório.

**Responses**: `200`, `400`, `401`, `403`, `404`, `409` — `FISCAL_CIOT_INVALID_TRANSITION` /
`FISCAL_CIOT_TRIP_ALREADY_STARTED`, `500`.

## `GET /api/v1/ciots/{id}/status-history`

Mesmo padrão de `039`/`040` — leitura pura, cursor-paginada, D281 (D284 já garante os mesmos campos
de `CTeStatusHistoryEntry`/`MDFeStatusHistoryEntry`).

**Segurança**: `documents.ciot.view`.

**Responses**: `200` (coleção cursor-paginada de `CIOTStatusHistoryEntry`), `401`, `403`, `404`,
`500`. **Sem `POST`/`PATCH`/`DELETE`**.

## Fora de escopo, não esquecido

- **XML/payload do CIOT**: `ciots` não tem `xml_arquivo_id` na DDL atual (ao contrário de CT-e/
  MDF-e) — a integração com ANTT usa outro formato de payload, capturado em `eventos_fiscais`
  (`documento_tipo = CIOT`, `044-eventos-fiscais.md`), não um XML fiscal próprio como SEFAZ.

## Como este documento cresce

Se a ANTT exigir XML/payload estruturado próprio no futuro, `xml_arquivo_id` seria adicionado a
`ciots` na origem (DDL) antes de qualquer mudança aqui — nunca simulado no contrato de API sem a
coluna física existir.
