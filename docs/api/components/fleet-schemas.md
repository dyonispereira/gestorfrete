# components/fleet-schemas.md — Schemas de Frota

Bounded context `fleet` (D215). Schemas compartilhados por `020` a `025` — mesmo motivo de
`trip-schemas.md` existir separado de `components/schemas.md` (agregado grande o bastante para
merecer arquivo próprio).

## `VehicleIdentity`, `VehicleTechnicalSheet`, `VehicleOperational` — nunca misturados

Espelha a separação já pedida (Identidade/Técnico/Operacional) e a separação física real entre
`veiculos_tracionadores` (identidade + parte do técnico) e `fichas_tecnicas_veiculo` (o resto do
técnico, tabela própria, com RBAC próprio — `fleet.vehicle_technical_sheet.*`).

```yaml
VehicleIdentity:
  type: object
  properties:
    codigo: { type: string, example: "VEI-000045" }
    plate: { type: string, description: "`placa` — Atributo Crítico (D077), trocar é evento raro e auditado." }
    renavam: { type: string }
  required: [codigo, plate, renavam]

VehicleTechnicalSheet:
  type: object
  description: "Sub-recurso próprio (`fleet.vehicle_technical_sheet.view`/`.edit`, RBAC dedicado) —
    GET/PATCH /veiculos/{id}/technical-sheet, nunca embutido diretamente no PATCH de Veículo."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    manufacturer: { type: string, description: "`fabricante` (vive em veiculos_tracionadores, exposto aqui por coesão de leitura)." }
    model: { type: string, description: "`modelo`." }
    manufacture_year: { type: integer, description: "`ano_fabricacao`." }
    category_id: { $ref: "../components/schemas.md#/UUID", description: "`categoria_veiculo_id`." }
    chassis: { type: string, description: "`chassi` — único na plataforma." }
    engine: { type: string, nullable: true, description: "`motor`." }
    axles: { type: integer, description: "`eixos`." }
    tare_weight: { type: string, description: "`tara`." }
    load_capacity: { type: string, description: "`capacidade_carga`." }
    gross_vehicle_weight: { type: string, description: "`pbt`." }
    owner_rntrc: { type: string, nullable: true, description: "`rntrc_proprietario`." }
    fuel_type: { type: string, enum: [DIESEL_S10, DIESEL_S500, GNV, ELETRICO], description: "`combustivel`." }
  required: [id, manufacturer, model, manufacture_year, category_id, chassis, axles, tare_weight, load_capacity, gross_vehicle_weight, fuel_type]
```

`manufacturer`/`model`/`manufacture_year`/`category_id` fisicamente vivem em
`veiculos_tracionadores`, não em `fichas_tecnicas_veiculo` — expostos juntos aqui porque o Lote 5
pediu a separação por **conceito** (Identidade/Técnico/Operacional), não por tabela; o sub-recurso
`technical-sheet` já lê das duas tabelas e apresenta uma visão coesa. `PATCH` nesse sub-recurso
grava em cada tabela física de origem, decisão de implementação, nunca visível ao cliente.

```yaml
VehicleOperational:
  type: object
  description: Nunca escrito diretamente — reflete `disponibilidade_veiculo` (Read Model, D081,
    025-vehicle-availability.md). Todo campo é readOnly.
  properties:
    status: { type: string, enum: [DISPONIVEL, EM_VIAGEM, EM_MANUTENCAO, INATIVO], readOnly: true }
    current_driver_id: { $ref: "../components/schemas.md#/UUID", nullable: true, readOnly: true }
    current_implement_id: { $ref: "../components/schemas.md#/UUID", nullable: true, readOnly: true }
    updated_at: { $ref: "../components/schemas.md#/Timestamp", readOnly: true }
```

## `Vehicle`

```yaml
Vehicle:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    identity: { $ref: "#/VehicleIdentity" }
    status: { type: string, enum: [ATIVO, INATIVO], description: "`veiculos_tracionadores.status` — status de cadastro, distinto de `operational.status` (disponibilidade operacional)." }
    branch_id: { $ref: "../components/schemas.md#/UUID", nullable: true, description: "`filial_id`." }
    operational: { $ref: "#/VehicleOperational" }
    tracking_reference:
      type: object
      nullable: true
      readOnly: true
      description: "D250 — só referência/ponteiro para consulta em `tracking` (posição atual,
        último sinal), nunca dado GPS embutido aqui. Fica nulo neste lote enquanto a API de
        Rastreamento não existir; formato exato (provavelmente `{ tracking_api_url }` ou similar) a
        definir quando esse lote for escrito."
    audit: { $ref: "../components/schemas.md#/AuditMetadata" }
  required: [id, identity, status, operational, audit]
```

`Vehicle` **não** inclui `VehicleTechnicalSheet` embutido — é um sub-recurso à parte (RBAC
dedicado, acima). `GET /veiculos/{id}` sozinho não retorna chassi/motor/eixos/etc.; o cliente busca
`GET /veiculos/{id}/technical-sheet` quando precisar.

## `Implement`

```yaml
Implement:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    codigo: { type: string, example: "IMP-000012" }
    plate: { type: string, description: "`placa`." }
    renavam: { type: string }
    body_type: { type: string, enum: [CARRETA, TANQUE, BAU, GRANELEIRO, PRANCHA, FRIGORIFICO, GAIOLA], description: "`tipo_carroceria`." }
    category_id: { $ref: "../components/schemas.md#/UUID", description: "`categoria_veiculo_id`." }
    load_capacity: { type: string, description: "`capacidade_carga`." }
    availability_status: { type: string, enum: [DISPONIVEL, EM_USO, INATIVO], description: "`status_disponibilidade`." }
    audit: { $ref: "../components/schemas.md#/AuditMetadata" }
  required: [id, codigo, plate, renavam, body_type, category_id, load_capacity, availability_status, audit]
```

`body_type` (carroceria) e `combination_type` de `VehicleComposition` (abaixo) são dimensões
diferentes, nunca confundidas (já reconciliado no Modelo Relacional, preservado aqui).

## `VehicleComposition`

```yaml
VehicleComposition:
  type: object
  description: "D248/D249 — pacote físico com vigência, nunca editado in-place. `implements` é uma
    lista ordenada (suporta bitrem/rodotrem, N:N com Implemento)."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    tractor_unit_id: { $ref: "../components/schemas.md#/UUID" }
    combination_type: { type: string, enum: [SIMPLES, BITREM, RODOTREM], description: "`tipo_combinacao`." }
    total_axles: { type: integer, description: "`eixos_total`." }
    status: { type: string, enum: [VALIDA, INVALIDA], readOnly: true }
    implements:
      type: array
      items:
        type: object
        properties:
          implement_id: { $ref: "../components/schemas.md#/UUID" }
          order: { type: integer, minimum: 1, description: "`ordem`." }
        required: [implement_id, order]
    starts_at: { type: string, format: date-time, readOnly: true, description: "`data_inicio_vigencia`." }
    ends_at: { type: string, format: date-time, nullable: true, readOnly: true, description: "`data_fim_vigencia` — nulo = vigente." }
  required: [id, tractor_unit_id, combination_type, total_axles, status, implements, starts_at]
```

## `OdometerReading`

```yaml
OdometerReading:
  type: object
  description: D191/D246 — imutável, nunca editável/excluível.
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    value_km: { type: string, description: "`valor_km`." }
    origin: { type: string, enum: [ABASTECIMENTO, CHECKLIST, MANUAL, TELEMETRIA], description: "`origem`." }
    trip_id: { $ref: "../components/schemas.md#/UUID", nullable: true, description: "`viagem_id`." }
    captured_at: { type: string, format: date-time, description: "`data_hora`." }
  required: [id, value_km, origin, captured_at]
```

## `VehicleAvailability`

```yaml
VehicleAvailability:
  type: object
  description: D247 — Read Model puro, todo campo readOnly, nunca escrito via API.
  properties:
    vehicle_id: { $ref: "../components/schemas.md#/UUID", readOnly: true }
    status: { type: string, enum: [DISPONIVEL, EM_VIAGEM, EM_MANUTENCAO, INATIVO], readOnly: true }
    current_driver_id: { $ref: "../components/schemas.md#/UUID", nullable: true, readOnly: true }
    current_implement_id: { $ref: "../components/schemas.md#/UUID", nullable: true, readOnly: true }
    updated_at: { $ref: "../components/schemas.md#/Timestamp", readOnly: true }
  required: [vehicle_id, status, updated_at]
```

## `VehicleDocument`

```yaml
VehicleDocument:
  type: object
  description: "D251 — `file_id` é sempre uma referência ao Storage, nunca o binário."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    type: { type: string, description: "`tipo` — vocabulário extensível (D120-style), ex.: CRLV." }
    number: { type: string, description: "`numero`." }
    expires_at: { type: string, format: date, description: "`data_validade`." }
    status: { type: string, enum: [VALIDO, VENCIDO], readOnly: true }
    file_id: { $ref: "../components/schemas.md#/UUID", nullable: true, description: "`arquivo_id`." }
  required: [id, type, number, expires_at, status]
```

## Como este documento cresce

Ficha Técnica/Documento/Composição/Hodômetro/Disponibilidade não crescem além do que já existe
fisicamente — `Seguradora`/`Apólice de Seguro`/`Licenciamento` **não** têm schema aqui (fora de
escopo deste lote, ver `020-vehicles.md` seção "Fora de escopo").
