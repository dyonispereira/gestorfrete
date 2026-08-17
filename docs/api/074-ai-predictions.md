# 074 — AI Predictions (Predições de IA)

Bounded context proprietário: `ai` (D215). `predicoes_ia` — Transactional, D163: toda predição
possui período de validade.

## `GET /api/v1/ai/predictions`

**Segurança**: `bearerAuth` + `ai.prediction.view`.

**Query parameters**: `page`/`limit`, `category`, `target_entity_type`, `target_entity_id`,
`status` (`ATUAL`/`EXPIRADA`).

**Responses**: `200` (`Pagination` de `AIPrediction`, `ai-schemas.md`), `401`, `403`, `500`.

## `GET /api/v1/ai/predictions/{id}`

**Responses**: `200` (`AIPrediction`), `401`, `403`, `404`, `500`.

## D312 — validade temporal nunca omitida silenciosamente

`valid_until` (`data_hora_validade_fim`) está sempre presente na resposta — quando o momento atual
já passou desse horizonte, `status = EXPIRADA` é retornado explicitamente (recalculado pela
aplicação na leitura ou por job periódico, detalhe de implementação). **Nunca**: omitir a predição
vencida da listagem por padrão, nem tratá-la silenciosamente como se ainda fosse atual — o cliente
sempre recebe o registro com seu status real, decidindo o que fazer com uma predição expirada.

**Query parameter `include_expired`**: `false` por padrão (lista só `ATUAL`) — `true` inclui
`EXPIRADA` explicitamente, nunca o contrário (default seguro: não confundir o usuário com dado
vencido sem pedir).

## Sem `POST`/`PATCH`/`DELETE`

Toda Predição nasce de uma Inferência (`072`) — nunca escrita direta do cliente. `resultado_real`
**não é campo desta entidade** — é registrado separadamente em `AIFeedback.actual_result`
(`077-ai-feedback.md`, D192): a Predição em si nunca é "corrigida" com o que de fato aconteceu, o
Feedback é quem captura essa comparação para fins de avaliação/retreinamento.

## Como este documento cresce

Nenhuma mudança estrutural prevista — o padrão horizonte+validade (D163) é estável por definição.
