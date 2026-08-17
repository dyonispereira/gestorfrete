# 050 — Heartbeats

Bounded context proprietário: `tracking` (D215). `heartbeats` — Time Series técnico (D105), não de
negócio. Única exceção documentada ao esqueleto padrão D191: particionada por `recebido_em`, não
`capturado_em` (heartbeat pode não informar captura).

## D293 — RBAC não existia, corrigido na origem

`RBAC_MATRIX.md` §7.16 não tinha nenhum código para Heartbeat. Corrigido: `tracking.heartbeat.view`
adicionado antes de escrever este documento.

## Consulta técnica, nunca notificação/status automático

**Heartbeats não são eventos de negócio** (pedido explícito) — não devem virar notificações ou
status operacionais automaticamente por si só. A ausência de heartbeat além de um limite gera
`PerdaDeSinalDetectada` (já em `EVENT_MAP.md`, publicado por `documents`... na verdade por
`tracking`/consumidor interno) — **esse** é o evento de negócio, exposto via `051-tracking-
events.md`, nunca este endpoint técnico diretamente.

## `GET /api/v1/tracking/equipment/{id}/heartbeats`

**Cursor pagination obrigatória** (D287).

**Segurança**: `bearerAuth` + `tracking.heartbeat.view`.

**Query parameters**: `cursor`/`limit`, `received_at__gte`/`__lte` (`recebido_em`).

**Responses**: `200` (coleção cursor-paginada de `Heartbeat`, `tracking-schemas.md`), `401`, `403`,
`404` (Equipamento não existe), `500`.

## Sem `POST`/`PATCH`/`DELETE`

Mesmo padrão de `048`/`049` (D286) — heartbeat é 100% originado da integração, nunca de um comando
de usuário.

## Como este documento cresce

Se `PerdaDeSinalDetectada` precisar de um endpoint de consulta dedicado (hoje só existe via
`051-tracking-events.md`, filtrando por tipo), isso é aditivo — este endpoint continua sendo a fonte
técnica bruta, nunca reescrito para "parecer" um evento de negócio.
