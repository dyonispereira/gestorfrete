# 053 — Tracking History (Histórico de Rastreamento)

Bounded context proprietário: `tracking` (D215). **D290 — Read Model composto, nenhuma tabela
nova**: esta consulta agrega `posicoes_veiculo` + `leituras_telemetria` + `eventos_rastreamento` em
tempo de leitura — mesmo princípio de `019-trip-timeline.md` (Lote 4, D187), aplicado aqui pela
segunda vez a um agregador multi-fonte.

## `GET /api/v1/vehicles/{vehicleId}/tracking/history`

**Cursor pagination obrigatória** (D287) — as três fontes somadas superam qualquer volume individual
já visto nesta API.

**Segurança**: `bearerAuth` + `tracking.position.view` como permissão base (mesmo padrão de
`019-trip-timeline.md` reaproveitando `freight.trip.view`) — **filtragem por linha** (D294-style):
uma entrada com `source = TELEMETRIA` só aparece se o chamador também tem `tracking.telemetry.view`;
uma entrada com `source = EVENTO` só aparece se o chamador tem a permissão da categoria
correspondente (tabela de `051-tracking-events.md`). Nenhuma entrada é omitida silenciosamente sem
motivo — a ausência é sempre por falta de permissão, nunca por erro.

**Query parameters obrigatórios**: `period_start`/`period_end` (mapeiam para o intervalo de
`captured_at`/`occurred_at` conforme a fonte) — **período é exigido, não opcional**, dado o volume
de `posicoes_veiculo` (consulta sem limite de período é proibida por esta API, `422` se ausente).

**Demais parâmetros**: `cursor`/`limit`, `source` (`POSICAO`/`TELEMETRIA`/`EVENTO`, filtra a
composição para só uma fonte).

**Responses**: `200` (coleção cursor-paginada de `TrackingHistoryEntry`, `tracking-schemas.md`),
`401`, `403`, `404` (Veículo não existe), `422` — `TRACKING_HISTORY_PERIOD_REQUIRED`, `500`.

## Honestidade sobre o que está incluído

Mesmo princípio de `019-trip-timeline.md`: cada fonte listada acima já tem endpoint próprio e
plenamente funcional (`048`/`049`/`051`) — esta consulta é conveniência de leitura agregada, nunca a
única forma de acessar o dado. Se uma fonte nova de Time Series for adicionada ao módulo no futuro
(ex: um novo tipo de leitura IoT), este endpoint só a inclui depois de explicitamente atualizado —
nunca promete cobertura que ainda não implementa (D241 aplicado aqui, fora do contexto de Viagem
pela primeira vez).

## Sem `POST`/`PATCH`/`DELETE`

Read Model — mesmo padrão de `025-vehicle-availability.md`/`019-trip-timeline.md`.

## Como este documento cresce

Novo `source` (ex: `HEARTBEAT`, se o produto decidir incluir sinais técnicos na visão de histórico)
é aditivo — hoje deliberadamente fora (D290 nota: heartbeat é técnico, não uma leitura de
negócio/observação de veículo, mesmo raciocínio de `050-heartbeats.md`).
