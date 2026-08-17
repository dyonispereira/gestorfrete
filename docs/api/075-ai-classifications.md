# 075 — AI Classifications (Classificações e Anomalias de IA)

Bounded context proprietário: `ai` (D215). `classificacoes_ia` — Transactional, Enum fechado
(`RISCO`/`PRIORIDADE`/`GRAVIDADE`). Cobre também `anomalias_detectadas` — entidade estruturalmente
distinta (ver Reconciliação abaixo), sem arquivo próprio no pedido do kickoff; agrupada aqui por ser
o documento onde a distinção entre as duas já precisa ser explicada.

## D076 — reconciliação já feita no Domain, preservada aqui

`relational/012-ia.md` já resolveu explicitamente: Classificação de IA rotula uma entidade
existente sob demanda (Risco/Prioridade/Gravidade); Anomalia Detectada é um evento detectado num
fluxo contínuo de leituras — estruturalmente diferente (referencia leitura de origem, não uma
entidade de negócio arbitrária). `classificacoes_ia.tipo_classificacao` **não inclui** `ANOMALIA` —
preservado literalmente aqui, nenhuma tentativa de unificar os dois conceitos num só endpoint.

## `GET /api/v1/ai/classifications`

**Segurança**: `bearerAuth` + `ai.classification.view`.

**Query parameters**: `page`/`limit`, `classification_type` (`RISCO`/`PRIORIDADE`/`GRAVIDADE`),
`target_entity_type`, `target_entity_id`.

**Responses**: `200` (`Pagination` de `AIClassification`, `ai-schemas.md`), `401`, `403`, `500`.

## `GET /api/v1/ai/classifications/{id}`

**Responses**: `200` (`AIClassification`), `401`, `403`, `404`, `500`.

## Exposição sem virar regra operacional automática

Pedido explícito: "expor a classificação sem transformar a classificação em regra operacional
automática" — este endpoint é **só leitura**, a classificação nunca dispara, por si só, uma ação em
outro bounded context (D161/D311 aplicados aqui) — se um Gestor decidir agir com base numa
Classificação de `RISCO = ALTO`, a ação é sempre um comando explícito no módulo correspondente
(ex: `commands/cancel` de uma Viagem), nunca uma automação silenciosa disparada pela leitura da
Classificação.

## Sem `POST`/`PATCH`/`DELETE` (Classificação)

Toda Classificação nasce de uma Inferência (`072`) — nunca escrita direta do cliente.

## Anomalias Detectadas

`anomalias_detectadas` — referencia `leitura_origem_tipo`/`leitura_origem_id`
(`POSICAO_VEICULO`/`LEITURA_TELEMETRIA`/`MEDICAO_PNEU`), nunca uma entidade de negócio arbitrária
como a Classificação.

### `GET /api/v1/ai/anomalies`

**Segurança**: `ai.anomaly.view`. **Query parameters**: `page`/`limit`, `source_reading_type`,
`status` (`ABERTA`/`INVESTIGADA`/`DESCARTADA`).

**Responses**: `200` (`Pagination` de `AIAnomaly`, `ai-schemas.md`), `401`, `403`, `500`.

### `GET /api/v1/ai/anomalies/{id}`

**Responses**: `200` (`AIAnomaly`), `401`, `403`, `404`, `500`.

### `POST /api/v1/ai/anomalies/{id}/commands/review`

`ABERTA → INVESTIGADA` ou `ABERTA → DESCARTADA` — única transição real do domínio (a DDL não
descreve um fluxo mais granular que isso).

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          resolution: { type: string, enum: [INVESTIGADA, DESCARTADA] }
          notes: { type: string }
        required: [resolution]
```

**Segurança**: `ai.anomaly.review`. **Responses**: `200` (`AIAnomaly`), `400`, `401`, `403`, `404`,
`409` — `AI_ANOMALY_INVALID_TRANSITION` (já revisada), `500`.

## Como este documento cresce

Se um novo `tipo_classificacao` for necessário, entra pelo Domain primeiro (D101) — o Enum físico
muda lá, este contrato só reflete o valor novo.
