# 090 — Resultado Gerencial

Lote 4. Bounded context proprietário: `analytics` (D090/D149 — lê `freight`/`financial`/
`maintenance`/`fleet`/`drivers`/`crm` diretamente, nunca escreve neles). Nenhuma entidade nova —
todo endpoint aqui é uma projeção/agregação calculada na hora sobre fatos já existentes (ver
`docs/domain/012-resultado-gerencial.md` para as fórmulas exatas e os gaps registrados). Prefixo
`/analytics/resultado-gerencial/*`.

Todo endpoint desta seção aceita os mesmos dois parâmetros de período opcionais:

- `data_programada__gte` (date) — início do período, inclusive.
- `data_programada__lte` (date) — fim do período, inclusive.

Filtram sempre sobre `viagens.data_programada`; o custo fora de Viagem (Manutenção/Outros Custos)
filtra pelo mesmo período sobre `contas_pagar.competencia` (Ordem de Serviço prevista filtra por
`ordens_servico.criado_em`). Omitir os dois parâmetros retorna todo o histórico do tenant. Uma
Viagem `CANCELADA` nunca entra em nenhuma soma, com ou sem período.

## `GET /api/v1/analytics/resultado-gerencial/visao-geral`

Topo do painel — totais do tenant inteiro (não filtrado por Cliente/Veículo/Motorista).

**Segurança**: `bearerAuth` + `analytics.executive_dashboard.view`.

**Responses**: `200` (`OverviewResult`), `401`, `403`, `500`.

```yaml
OverviewResult:
  type: object
  properties:
    totals: { $ref: '#/components/schemas/ResultTotals' }
    maintenance_cost_realized: { type: string }
    other_costs_realized:
      type: string
      description: >
        Soma única (não a soma de "Outros Custos por Veículo" + "custo vinculado por Motorista" —
        essas duas visões podem compartilhar a mesma Conta a Pagar; somadas em separado aqui
        contariam o mesmo real duas vezes).
```

## `GET /api/v1/analytics/resultado-gerencial/viagens`

Dimensão Viagem — os mesmos campos já usados na aba Financeiro da Viagem (`GET /viagens/{id}`),
paginados e agregáveis por período/Cliente/Veículo/Motorista.

**Segurança**: `bearerAuth` + `analytics.freight_report.view`.

**Query parameters** (além do período): `client_id`, `vehicle_id`, `driver_id`, `page`, `limit`.

**Responses**: `200` (coleção paginada de `TripResult`), `401`, `403`, `500`.

## `GET /api/v1/analytics/resultado-gerencial/veiculos`

Dimensão Veículo — ranking (sem paginação, frota cabe inteira), ordenado por
`totals.realized_margin` decrescente (Resultado Total, não só o operacional — o pior caso, com
Manutenção incluída, aparece primeiro).

**Segurança**: `bearerAuth` + `analytics.maintenance_report.view`.

**Responses**: `200` (array de `VehicleResult`), `401`, `403`, `500`.

```yaml
VehicleResult:
  type: object
  properties:
    vehicle_id: { $ref: '#/components/schemas/UUID' }
    plate: { type: string }
    model: { type: string }
    trip_cost_realized: { type: string, description: "Só o custo das Viagens (`viagens.custo_realizado`)." }
    maintenance_cost_predicted: { type: string }
    maintenance_cost_realized: { type: string }
    other_costs_realized: { type: string }
    operational_result:
      type: string
      description: "Resultado Operacional de Viagens = Receita Realizada − `trip_cost_realized`, sem Manutenção/Outros Custos."
    operational_margin_pct: { type: string, nullable: true }
    totals:
      allOf:
        - $ref: '#/components/schemas/ResultTotals'
        - description: "`realized_cost`/`realized_margin` aqui são o Resultado TOTAL — inclui Manutenção + Outros Custos."
```

## `GET /api/v1/analytics/resultado-gerencial/veiculos/{vehicle_id}`

Drill-down: "Veículo → resultado → viagens → custos → OS/CP de origem".

**Segurança**: `bearerAuth` + `analytics.maintenance_report.view`.

**Responses**: `200` (`VehicleResultDetail` — `result` + `trips: TripResult[]` + `cost_origins:
VehicleCostOrigin[]`, cada item de `cost_origins` aponta a Conta a Pagar exata, e a Ordem de Serviço
quando `origin=ORDEM_SERVICO`), `401`, `403`, `404`, `500`.

## `GET /api/v1/analytics/resultado-gerencial/clientes`

Dimensão Cliente — ranking por `totals.realized_revenue` decrescente. `totals.realized_cost` aqui é
só o custo operacional de Viagem do Cliente — nunca inclui Manutenção/frota (gap registrado,
`docs/domain/012-resultado-gerencial.md`).

**Segurança**: `bearerAuth` + `analytics.financial_report.view`.

**Responses**: `200` (array de `ClientResult`), `401`, `403`, `500`.

## `GET /api/v1/analytics/resultado-gerencial/clientes/{client_id}`

Drill-down: "Cliente → resultado → Faturas → Viagens → CT-es". `invoices` aponta as mesmas Faturas de
`GET /faturas?client_id=` (Lote Financeiro, Parte 3) — sem duplicar dado, só resume o essencial para
o ranking e permite navegar de volta à tela de origem.

**Segurança**: `bearerAuth` + `analytics.financial_report.view`.

**Responses**: `200` (`ClientResultDetail` — `result` + `trips: TripResult[]` + `invoices:
ClientInvoiceSummary[]`), `401`, `403`, `404`, `500`.

## `GET /api/v1/analytics/resultado-gerencial/motoristas`

Dimensão Motorista — ranking por `totals.realized_margin` decrescente. `linked_cost_realized` é
sempre custo **explicitamente vinculado** ao Motorista (`contas_pagar.motorista_id`, qualquer
`origem` exceto `VIAGEM`) — nunca herdado do Veículo (regra explícita do usuário, ver
`docs/domain/012-resultado-gerencial.md`).

**Segurança**: `bearerAuth` + `analytics.driver_report.view`.

**Responses**: `200` (array de `DriverResult`), `401`, `403`, `500`.

## `GET /api/v1/analytics/resultado-gerencial/motoristas/{driver_id}`

Drill-down do Motorista — `trips` (as Viagens que compõem `trip_cost_realized`) e `linked_costs` (as
Contas a Pagar que compõem `linked_cost_realized`), nunca confundidos entre si.

**Segurança**: `bearerAuth` + `analytics.driver_report.view`.

**Responses**: `200` (`DriverResultDetail`), `401`, `403`, `404`, `500`.

## `ResultTotals` (schema compartilhado)

```yaml
ResultTotals:
  type: object
  properties:
    trips: { type: integer }
    predicted_revenue: { type: string }
    realized_revenue: { type: string }
    predicted_cost: { type: string }
    realized_cost: { type: string }
    realized_margin: { type: string }
    predicted_margin: { type: string }
    realized_margin_pct: { type: string, nullable: true, description: "`null` quando `realized_revenue` é zero." }
    km: { type: string, nullable: true, description: "`null` — gap registrado, nunca aproximado (D-km-012)." }
    revenue_per_km: { type: string, nullable: true }
    cost_per_km: { type: string, nullable: true }
    margin_per_km: { type: string, nullable: true }
```
