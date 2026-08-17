# 055 — Driver Trips (Viagens do Motorista)

Bounded context proprietário: `freight` (D215) — **não** `mobile`. Este documento é a superfície
mobile-facing de `014-trips.md`/`018-trip-status.md`; D297/D303: nenhuma máquina de estados nova,
nenhum comando novo — os mesmos estados/transições/eventos já documentados em `002-VIAGEM.md`.

## D295 — identidade vem da sessão, nunca do corpo

**Nunca confiar em `{ "motorista_id": "..." }` enviado pelo aparelho** — todo endpoint deste
documento deriva o Motorista da Sessão Mobile autenticada (`054-driver-authentication.md`), mesmo
princípio de D208 aplicado ao Motorista em vez do Tenant.

## `GET /api/v1/mobile/trips`

Lista **só** as viagens atribuídas ao Motorista da sessão — nunca todas as viagens do tenant.

**Segurança**: `bearerAuth` + `freight.trip.view_own`.

**Query parameters**: `page`/`limit`, `status` (Status Operacional).

**Responses**: `200` (`Pagination` de `Trip`, reaproveitado de `components/trip-schemas.md` — sem
schema mobile-específico, D303), `401`, `403`, `500`.

## `GET /api/v1/mobile/trips/{id}`

**Segurança**: `freight.trip.view_own` — `403` se a Viagem não pertence ao Motorista da sessão
(nunca `404`, para não vazar existência de viagens de outros motoristas — mesmo princípio de
enumeration-safety já usado em endpoints `_own` anteriores).

**Responses**: `200` (`Trip`), `401`, `403`, `500`.

## Comandos — só os que o Domain sustenta para o Motorista

D297: cruzado literalmente contra `018-trip-status.md` (Lote 4) — nenhum comando novo, nenhum nome
diferente. `RBAC_MATRIX.md` §7.12 confirma quais comandos têm o Motorista no escopo real (D304):

| Comando pedido no kickoff | Nome real (`018-trip-status.md`) | Transição | RBAC |
|---|---|---|---|
| `accept` | `commands/accept` | `PLANEJADA → PLANEJADA` (D129, evento sem mudança de status) | `freight.trip.edit` (D240, App ● desde D304) |
| `start` | `commands/start` | `LIBERADA → EM_TRANSITO` | `freight.trip.start` (App ●) |
| `pause` | `commands/interromper` | `EM_TRANSITO → INTERROMPIDA` | `freight.trip.edit` (D240, App ● desde D304) |
| `resume` | `commands/retomar` | `INTERROMPIDA → EM_TRANSITO` | `freight.trip.edit` (D240, App ● desde D304) |
| `finish` | `commands/finish` | `EM_TRANSITO → FINALIZADA` | `freight.trip.finish` (App ●) |

Os nomes de comando do pedido (`accept`/`start`/`pause`/`resume`/`finish`) eram ilustrativos —
`interromper`/`retomar` são os nomes reais já estabelecidos em `018-trip-status.md`, mantidos aqui
por D216 (nunca inventar nome novo quando o real já existe).

### `POST /api/v1/mobile/trips/{id}/commands/accept`

**Responses**: `200` (`Trip`, D238), `401`, `403`, `409` — `FREIGHT_TRIP_INVALID_TRANSITION`, `500`.

### `POST /api/v1/mobile/trips/{id}/commands/start`

Precondição real: `AGUARDANDO_CHECKLIST → LIBERADA` deve já ter ocorrido — **externa a este
documento** (`018-trip-status.md` já marca essa transição como dependente de Checklist, ainda sem
API, `056-driver-checklists.md`). Tentar iniciar antes de `LIBERADA` retorna `409`.

**Responses**: `200`, `401`, `403`, `409`, `500`.

### `POST /api/v1/mobile/trips/{id}/commands/interromper`

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

**Responses**: `200`, `400`, `401`, `403`, `409`, `500`.

### `POST /api/v1/mobile/trips/{id}/commands/retomar`

**Responses**: `200`, `401`, `403`, `409`, `500`.

### `POST /api/v1/mobile/trips/{id}/commands/finish`

Precondição real (`018-trip-status.md`): todas as Entregas em estado terminal. **Responses**: `200`,
`401`, `403`, `409` — `FREIGHT_TRIP_DELIVERIES_PENDING`, `500`.

## D303 — mesmo endpoint administrativo, caminho mobile

Estes cinco comandos **são** `POST /viagens/{id}/commands/X` (`018-trip-status.md`), expostos aqui
sob `/mobile/trips/{id}/commands/X` só pela conveniência de escopo (`view_own` implícito no path,
melhor cabimento em resposta offline-friendly) — nunca uma segunda implementação. O Backend
resolve os dois caminhos para a mesma Application Service (detalhe de implementação, não deste
contrato).

## Relação com `060-driver-sync.md`

Quando o Motorista está online, o app **pode** chamar estes endpoints diretamente para feedback
imediato. Quando offline, o mesmo comando lógico (`tipo_comando = ACCEPT_TRIP`/`START_TRIP`/etc.)
é enfileirado via `POST /mobile/sync` e processado depois, na ordem de `sequencia_local` — os dois
caminhos convergem para a mesma validação de domínio (D303), nunca regras diferentes por canal.

## Fora de escopo, não esquecido

- **`freight.trip.edit`/`.dispatch`/`.cancel`/`.reassign`/`.edit_cost`**: fora do Perfil Motorista
  (RBAC §13) — nenhum desses comandos é exposto aqui.
- **Alocação de recursos, Ocorrências gerais, Financeiro/Fiscal da viagem**: cobertos por outros
  documentos (`016`/`017`/`038`), não duplicados aqui.

## Como este documento cresce

Se `018-trip-status.md` ganhar um comando novo no futuro (ex: quando Coleta/Romaneio forem
convertidos em API), este documento só ganha uma linha na tabela acima **se** o RBAC confirmar o
Motorista no escopo — nunca antecipado.
