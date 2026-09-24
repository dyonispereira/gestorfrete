# 014 — Trips

Bounded context proprietário: `freight` (D215). Primeiro Aggregate Root complexo do contrato —
Viagem é o core domain do GestorFrete ([`../flows/002-VIAGEM.md`](../flows/002-VIAGEM.md), a
referência canônica desta máquina de estados; este documento nunca a redefine, só traduz para
HTTP).

## Viagem não é CRUD simples

`POST` cria a Viagem em `RASCUNHO`. `PATCH` altera **só os campos que fazem sentido editar fora de
uma transição de estado** (D233 — status nunca muda por `PATCH`). Toda mudança de estado é um
comando explícito, documentado por completo em
[`018-trip-status.md`](./018-trip-status.md) — este documento cobre CRUD, referências vs.
snapshots, e a lista dos comandos (sem repetir a tabela completa de transições, D069).

## `GET /api/v1/viagens`

**Segurança**: `bearerAuth` + `freight.trip.view` (ou `freight.trip.view_own` — Escopo "Próprio
usuário", quando o ator é um Motorista consultando só suas próprias viagens, resolvido pelo mesmo
mecanismo de `drivers.driver.view_own`/`009-drivers.md`).

**Query parameters** (D226 — todos correspondem a colunas reais de `viagens`):

| Parâmetro | Coluna física |
|---|---|
| `page`, `limit` | Offset (Master Data — Transactional, não Time Series; `PAGINATION.md`) |
| `status_operacional` | `status_operacional` |
| `status_fiscal` | `status_fiscal` |
| `status_financeiro` | `status_financeiro` |
| `motorista_id` | `motorista_id` |
| `veiculo_id` | `veiculo_tracionador_id` |
| `cliente_id` | `cliente_id` |
| `data_programada` (+ `__gte`/`__lte`, `FILTERING_SORTING.md`) | `data_programada` |
| `codigo` | `codigo` |

**Sem filtro `origem`/`destino`** — pedidos no exemplo original, mas `viagens` não tem colunas de
origem/destino próprias (isso vive em `pontos_parada_viagem.localizacao`, `GEOGRAPHY`, uma tabela
separada) — filtrar Viagem por origem/destino exigiria um `JOIN` que este lote não cobre (fora de
escopo, não inventado — mesma disciplina de `?branch=` em `003-users.md`).

**Responses**: `200` (`Pagination` de `Trip`), `401`, `403`, `500`.

## `GET /api/v1/viagens/{id}`

**Segurança**: `freight.trip.view`/`.view_own`. **Responses**: `200` (`Trip`), `401`, `403`, `404`
(`FREIGHT_TRIP_NOT_FOUND`), `500`.

## `POST /api/v1/viagens`

**Segurança**: `freight.trip.create`. **`Idempotency-Key`**: aceita e com enforcement real
(Reconciliado, V1 Operational Hardening Parte 6, `core/idempotency/` — primeira prioridade da
lista pedida pelo usuário; "obrigatória" era documentado desde D211/seção 15 do pedido original
mas nunca de fato aplicado antes desta rodada, D418). Aceita, não exigida — clientes que ainda não
enviam o header continuam funcionando; quando enviado, a mesma chave + mesmo corpo nunca cria uma
segunda Viagem.

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          cliente_id: { $ref: "components/schemas.md#/UUID" }
          data_programada: { type: string, format: date }
          janela_programada: { type: string, format: date-time }
        required: [cliente_id]
```

Nasce em `RASCUNHO`. Nenhum campo de `status`/`snapshots`/`financials` aceito — todos `readOnly`
(`trip-schemas.md`). Alocação de recursos (Motorista/Veículo/Implemento) **não** acontece neste
`POST` — é um passo separado, [`016-trip-resources.md`](./016-trip-resources.md), consistente com
D188 (pacote atômico com seu próprio contrato) e com D232 (sub-recurso só quando o dono controla o
ciclo de vida — a alocação tem ciclo de vida e regras próprias, D188, mesmo dentro do agregado
Viagem).

**Responses**: `201` (`Trip`), `400`, `401`, `403`, `409` (D230/D211 — chave de idempotência
reusada com payload diferente), `500`.

## `PATCH /api/v1/viagens/{id}`

**Segurança**: `freight.trip.edit`. D229 — só campos enviados.

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          data_programada: { type: string, format: date }
          janela_programada: { type: string, format: date-time }
```

**Nunca aceito neste `PATCH`** (D233/D237 — nada aqui muda por edição direta, só por comando ou
por sub-recurso com regra própria):

| Campo | Como muda de verdade |
|---|---|
| `status.*` | Comandos, `018-trip-status.md` |
| `references.*` (motorista/veículo) | `016-trip-resources.md`, comando de realocação |
| `snapshots.*` | Nunca — gerado pela Application no momento da transição relevante |
| `financials.*` | Calculado por `financial`/consumo de evento, nunca `PATCH` direto |

**Responses**: `200` (`Trip`), `400`, `401`, `403`, `404`, `422` (ex.: tentar editar
`data_programada` de uma Viagem já `FINALIZADA`), `500`.

## `DELETE /api/v1/viagens/{id}`

**D219 — soft delete.** Só é permitido a partir dos estados iniciais (`RASCUNHO`/`PLANEJADA`) —
uma Viagem já despachada nunca é "excluída", só `CANCELADA` (comando, `018-trip-status.md`).

**Segurança**: `freight.trip.edit` (não há `.delete` dedicado em `RBAC_MATRIX.md` 7.12 — a
exclusão de Viagem em `RASCUNHO` é tratada como uma edição/descarte, não uma ação de criticidade
própria; diferente de `.cancel`, que é a ação de negócio real para viagem já em curso).

**Responses**: `204`, `401`, `403`, `404`, `422` — `FREIGHT_TRIP_CANNOT_DELETE_STARTED`
(estado operacional além de `PLANEJADA` — use `commands/cancelar`), `500`.

## Referências vs. Snapshots — nunca confundidos (D038/D071/D073)

```json
{
  "references": { "client_id": "...", "driver_id": "...", "tractor_unit_id": "..." },
  "snapshots": {
    "driver_name_snapshot": "João Silva",
    "tractor_unit_plate_snapshot": "ABC1D23",
    "client_snapshot": { "razao_social": "Cliente Exemplo LTDA" },
    "predicted_revenue_snapshot": "4500.00",
    "applied_price_table_id": "..."
  }
}
```

- `references` aponta para o estado **atual** de Cliente/Motorista/Veículo — se o Motorista mudar
  de telefone amanhã, `GET /viagens/{id}` não reflete isso (a API precisaria buscar
  `GET /drivers/{driver_id}` separadamente para o dado atual).
- `snapshots` é o que a Viagem **congelou** no momento relevante (D073) — nunca ressincronizado,
  mesmo que a entidade de origem mude ou seja excluída depois.
- **O cliente nunca escreve em `snapshots`** — todo campo é `readOnly` no schema `TripSnapshots`
  (`trip-schemas.md`). Um `PATCH`/`POST` que tentar enviar `snapshots` é ignorado silenciosamente
  pela validação de schema (campos `readOnly` fora do corpo de request no OpenAPI), nunca aceito
  como se fosse um valor real.

## Comandos — visão geral (detalhe completo em `018-trip-status.md`)

```
POST /viagens/{id}/commands/accept
POST /viagens/{id}/commands/dispatch
POST /viagens/{id}/commands/start
POST /viagens/{id}/commands/finish
POST /viagens/{id}/commands/interromper
POST /viagens/{id}/commands/retomar
POST /viagens/{id}/commands/cancelar
POST /viagens/{id}/commands/close-administrative
POST /viagens/{id}/commands/reallocate-resources   -- 016-trip-resources.md
```

Nenhum comando aqui foi inventado sem uma transição correspondente em
[`../flows/002-VIAGEM.md`](../flows/002-VIAGEM.md) — cada um está listado, com estado-origem/
estado-destino/RBAC/pré-condições/eventos, em `018-trip-status.md`. Alguns comandos usam
`freight.trip.edit` como aproximação de RBAC (D240) — a granularidade exata fica registrada como
lacuna, nunca uma permissão nova inventada aqui.

**`PATCH /viagens/{id} {"status": "EM_TRANSITO"}` nunca é aceito** — nem sintaticamente (o schema
de `PATCH` não tem um campo `status` no nível raiz, D233).

## Como este documento cresce

`015` a `019` detalham cada sub-recurso/comando/consulta — este documento nunca duplica o que eles
já cobrem (D069).
