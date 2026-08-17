# 073 — AI Suggestions (Sugestões de IA)

Bounded context proprietário: `ai` (D215). `sugestoes_ia` — Transactional, D310: produto derivado
da Inferência (`072`), nunca fundido com ela.

## Campos sempre separados (pedido explícito)

`recomendacao`/`justificativa`/`nivel_confianca`/`decisao_usuario` são colunas físicas distintas
desde a DDL (`sugestoes_ia`) — nunca misturadas num único blob, já refletido literalmente em
`AISuggestion` (`ai-schemas.md`): `recommendation`/`justification`/`confidence_level`/`status`+
`decision_user_id` são propriedades separadas.

## `GET /api/v1/ai/suggestions`

**Segurança**: `bearerAuth` + `ai.suggestion.view`.

**Query parameters**: `page`/`limit`, `category`, `target_entity_type`, `target_entity_id`,
`status`.

**Responses**: `200` (`Pagination` de `AISuggestion`, `ai-schemas.md`), `401`, `403`, `500`.

## `GET /api/v1/ai/suggestions/{id}`

**Responses**: `200` (`AISuggestion`), `401`, `403`, `404`, `500`.

## Decisão do usuário — só os estados reais do Domain

`sugestoes_ia_status_enum` = `PENDENTE`/`ACEITA`/`REJEITADA`/`IGNORADA`/`EXPIRADA` — os três
comandos pedidos (`ACEITAR`/`REJEITAR`/`IGNORAR`) existem literalmente como transições reais a
partir de `PENDENTE`. `EXPIRADA` é derivada (automática, quando a Sugestão ultrapassa validade
implícita — sem comando, mesmo padrão de `PENDENTE → VENCIDA` em `033-accounts-receivable.md`).

### `POST /api/v1/ai/suggestions/{id}/commands/accept`

**D311 — nunca executa o comando operacional diretamente**: aceitar uma Sugestão registra a
decisão (`status = ACEITA`, `decision_user_id`, `decided_at`) — a execução real (ex: abrir uma OS a
partir de uma sugestão de manutenção preventiva) é sempre uma chamada separada e explícita ao
comando do bounded context responsável (`POST /ordens-servico`, `026-maintenance-orders.md`), feita
pelo cliente ou por uma orquestração de Backend que **chama o comando real**, nunca a API de IA
alterando a entidade de destino por conta própria.

**Segurança**: `ai.suggestion.decide`. **Idempotency-Key**: recomendado.

**Responses**: `200` (`AISuggestion`, D238), `401`, `403`, `404`, `409` —
`AI_SUGGESTION_INVALID_TRANSITION` (já decidida ou expirada), `500`.

### `POST /api/v1/ai/suggestions/{id}/commands/reject`

```yaml
requestBody:
  required: false
  content:
    application/json:
      schema:
        type: object
        properties:
          justification: { type: string }
```

**Segurança**: `ai.suggestion.decide`. **Responses**: `200`, `401`, `403`, `404`, `409`, `500`.

### `POST /api/v1/ai/suggestions/{id}/commands/ignore`

**Segurança**: `ai.suggestion.decide`. **Responses**: `200`, `401`, `403`, `404`, `409`, `500`.

## Evento de decisão — lacuna registrada, não inventada

`EVENT_MAP.md` não tem nenhum evento para a decisão de Sugestão (ex: `SugestaoIAAceita`) — diferente
da família de gaps D239/D259/.../D284 (onde um fluxo canônico nomeia um evento que o catálogo não
tem), aqui **nenhum fluxo jamais nomeou** esse evento, porque IA não tem um `flows/0NN-IA.md`
dedicado. Não inventado aqui — registrado como lacuna de produto a considerar quando/se um fluxo de
IA for formalizado (D313).

## Sem `PATCH`/`DELETE`

Sugestão nunca é editada diretamente — só transiciona via os três comandos acima; excluir uma
Sugestão apagaria a rastreabilidade da decisão (D001/D167).

## Como este documento cresce

Se `ai.suggestion.decide` precisar de granularidade por comando (`.accept`/`.reject`/`.ignore`
separados), isso segue o mesmo processo de D271/D283/D293/D304/D313 — corrigir a matriz primeiro,
nunca inventar aqui.
