# 077 — AI Feedback (Feedback de IA)

Bounded context proprietário: `ai` (D215). `feedbacks_ia` — Transactional, D165: matéria-prima para
evolução futura dos modelos, sem que `ai` altere a decisão original do usuário.

## Polimórfico — cobre qualquer saída de IA

`saida_ia_tipo` (`SUGESTAO`/`PREDICAO`/`CLASSIFICACAO`/`ANOMALIA`/`LEITURA_VISAO_COMPUTACIONAL`) +
`saida_ia_id` referenciam qualquer uma das cinco saídas já documentadas (`072`–`076`) — um único
endpoint de Feedback, nunca cinco endpoints duplicados por tipo de saída.

## `GET /api/v1/ai/feedback`

**Segurança**: `bearerAuth` + `ai.feedback.view`.

**Query parameters**: `page`/`limit`, `output_type` (`saida_ia_tipo`), `output_id`, `result`
(`ACEITO`/`REJEITADO`/`IGNORADO`).

**Responses**: `200` (`Pagination` de `AIFeedback`, `ai-schemas.md`), `401`, `403`, `500`.

## `GET /api/v1/ai/feedback/{id}`

**Responses**: `200` (`AIFeedback`), `401`, `403`, `404`, `500`.

## `POST /api/v1/ai/feedback`

Permite aceitar/rejeitar/comentar/registrar resultado real (pedido explícito) — os quatro cabem no
mesmo schema, já que `feedbacks_ia` é uma única tabela com colunas para todos:

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          output_type: { type: string, enum: [SUGESTAO, PREDICAO, CLASSIFICACAO, ANOMALIA, LEITURA_VISAO_COMPUTACIONAL] }
          output_id: { $ref: "components/schemas.md#/UUID" }
          result: { type: string, enum: [ACEITO, REJEITADO, IGNORADO] }
          justification: { type: string }
          actual_result: { type: string, description: "D192 — o que de fato aconteceu depois; pode ser enviado depois, via PATCH, quando só se souber mais tarde (ex: predição de quebra em 72h — o resultado real só é conhecido dias depois)." }
        required: [output_type, output_id, result]
```

**Segurança**: `ai.feedback.create` (App ● — Motorista pode dar feedback em Sugestões/Leituras de
Visão Computacional que o afetam diretamente, ex.: confirmar que uma leitura de avaria estava
correta).

**Responses**: `201` (`AIFeedback`), `400`, `401`, `403`, `404` (saída referenciada não existe),
`500`.

## `PATCH /api/v1/ai/feedback/{id}`

**Único campo editável**: `actual_result` — permite registrar o resultado real depois, quando ele
só se torna conhecido após o feedback inicial (`result`/`justification` são a decisão pontual do
momento, imutável; `actual_result` é observação tardia, D192).

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          actual_result: { type: string }
        required: [actual_result]
```

**Segurança**: `ai.feedback.create` (mesma responsabilidade — sem `.edit` dedicado, RBAC não
distingue; reaproveitado, gap documentado, mesmo padrão de D240 aplicado pela última vez nesta
sprint de BI+IA).

**Responses**: `200` (`AIFeedback`), `400`, `401`, `403`, `404`, `500`.

## D165 — Feedback nunca altera a decisão original

Registrar Feedback sobre uma Sugestão **não** reabre ou modifica `AISuggestion.status`/
`decision_user_id` (`073`) — são registros independentes; o Feedback é sempre um dado adicional
sobre a saída de IA, nunca uma correção retroativa da decisão já tomada.

## Sem `DELETE`

`RBAC_MATRIX.md` não tem `ai.feedback.delete` — Feedback é matéria-prima de retreinamento (D165),
nunca removido.

## Como este documento cresce

Se o produto pedir feedback estruturado (ex: rating numérico além de Aceito/Rejeitado/Ignorado),
isso é decisão de Domain/DDL primeiro — hoje `resultado` é um Enum fechado de 3 valores.
