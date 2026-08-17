# components/tracking-schemas.md — Schemas de Rastreamento

Bounded context `tracking` (D215). Schemas compartilhados por `046` a `053`.

## `GeoPoint` — coordenada

Reutilizado em toda entidade com `GEOGRAPHY(Point, 4326)` — nunca WKT/PostGIS bruto exposto.

```yaml
GeoPoint:
  type: object
  properties:
    latitude: { type: number, format: double }
    longitude: { type: number, format: double }
  required: [latitude, longitude]
```

## `TrackingProvider` — Provedor de Rastreamento

```yaml
TrackingProvider:
  type: object
  description: "D291 — cadastro puro; nenhuma integração específica por fornecedor é modelada aqui."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    name: { type: string, description: "`nome` — único por tenant." }
    status: { type: string, enum: [ATIVO, INATIVO] }
    audit: { $ref: "../components/schemas.md#/AuditMetadata" }
  required: [id, name, status, audit]
```

## `TrackingEquipment` — Equipamento de Rastreamento

```yaml
TrackingEquipment:
  type: object
  description: "D128 — múltiplos equipamentos por veículo; no máximo um PRINCIPAL vigente por vez."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    provider_id: { $ref: "../components/schemas.md#/UUID", description: "`provedor_rastreamento_id`." }
    serial_identifier: { type: string, description: "`identificador_serial` — único na plataforma." }
    equipment_type: { type: string, enum: [PRINCIPAL, BACKUP, CAMERA, SENSOR_TEMPERATURA, TPMS, OUTRO], description: "`tipo_equipamento`." }
    vehicle_id: { $ref: "../components/schemas.md#/UUID", description: "`veiculo_tracionador_id`." }
    starts_at: { type: string, format: date-time, description: "`data_inicio_vigencia`." }
    ends_at: { type: string, format: date-time, description: "`data_fim_vigencia` — nulo = vigente." }
    status: { type: string, enum: [ATIVO, INATIVO, REMOVIDO] }
    audit: { $ref: "../components/schemas.md#/AuditMetadata" }
  required: [id, provider_id, serial_identifier, equipment_type, status, audit]
```

## `VehiclePosition` — Time Series (D191)

```yaml
VehiclePosition:
  type: object
  description: "D286 — imutável, só leitura pela API de negócio. D124/D125/D292 — três timestamps distintos."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    vehicle_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`veiculo_tracionador_id`." }
    equipment_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`equipamento_rastreamento_id`." }
    location: { $ref: "#/GeoPoint" }
    origin: { type: string, readOnly: true, description: "`origem_localizacao_id` resolvido — D117." }
    precision_meters: { type: number, readOnly: true, description: "`precisao_metros` — D118, opcional." }
    satellite_count: { type: integer, readOnly: true, description: "`numero_satelites` — D118, opcional." }
    hdop: { type: number, readOnly: true, description: "D118, opcional." }
    confidence_level: { type: number, readOnly: true, description: "`nivel_confianca` — D118, opcional." }
    captured_at: { type: string, format: date-time, readOnly: true, description: "`capturado_em` — D124/D125." }
    received_at: { type: string, format: date-time, readOnly: true, description: "`recebido_em`." }
    processed_at: { type: string, format: date-time, readOnly: true, description: "`processado_em`." }
  required: [id, vehicle_id, equipment_id, location, origin, captured_at, received_at, processed_at]
```

## `TelemetryReading` — Time Series EAV (D120)

```yaml
TelemetryReading:
  type: object
  description: "D120 — EAV, nunca uma coluna por sensor. D286 — imutável, só leitura."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    vehicle_id: { $ref: "../components/schemas.md#/UUID", readOnly: true }
    equipment_id: { $ref: "../components/schemas.md#/UUID", readOnly: true }
    position_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`posicao_veiculo_id` — quando o mesmo pacote trouxe posição junto." }
    sensor_type: { type: string, enum: [IGNICAO, VELOCIDADE, BATERIA, TENSAO, ODOMETRO, HORIMETRO, RPM, TEMPERATURA, COMBUSTIVEL, ACELERACAO, FRENAGEM], readOnly: true, description: "`tipo_sensor` — vocabulário extensível (D120)." }
    value: { type: string, readOnly: true, description: "`valor`." }
    unit: { type: string, readOnly: true, description: "`unidade`." }
    captured_at: { type: string, format: date-time, readOnly: true }
    received_at: { type: string, format: date-time, readOnly: true }
    processed_at: { type: string, format: date-time, readOnly: true }
  required: [id, vehicle_id, equipment_id, sensor_type, value, unit, captured_at, received_at, processed_at]
```

## `Heartbeat` — Time Series técnico (D105)

```yaml
Heartbeat:
  type: object
  description: "Sinal técnico, não de negócio. Particionada por recebido_em, não capturado_em (exceção documentada ao padrão D191 — heartbeat pode não informar captura)."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    equipment_id: { $ref: "../components/schemas.md#/UUID", readOnly: true }
    external_protocol: { type: string, readOnly: true, description: "`protocolo_externo` — D111, quando o provedor oferece." }
    captured_at: { type: string, format: date-time, readOnly: true, description: "Pode ser ausente." }
    received_at: { type: string, format: date-time, readOnly: true }
    processed_at: { type: string, format: date-time, readOnly: true }
  required: [id, equipment_id, received_at, processed_at]
```

## `TrackingEvent` — derivado (D119/D288)

```yaml
TrackingEvent:
  type: object
  description: "D119/D288 — derivado de leituras brutas, nunca as substitui. D127 — sempre tem severidade."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    vehicle_id: { $ref: "../components/schemas.md#/UUID", readOnly: true }
    type: { type: string, enum: [PARADA_DETECTADA, DESVIO_DE_ROTA_DETECTADO, EXCESSO_DE_VELOCIDADE, ENTROU_GEOFENCE, SAIU_GEOFENCE, IGNICAO_LIGADA, IGNICAO_DESLIGADA], readOnly: true, description: "`tipo`." }
    position_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`posicao_veiculo_id` — referência à origem (D288), nunca cópia." }
    geofence_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`cerca_eletronica_id` — presente em ENTROU_GEOFENCE/SAIU_GEOFENCE." }
    speed_limit_config_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`configuracao_limite_velocidade_id` — presente em EXCESSO_DE_VELOCIDADE." }
    detected_value: { type: string, readOnly: true, description: "`valor_detectado`." }
    severity: { type: string, enum: [INFORMACAO, ATENCAO, ALERTA, CRITICO], readOnly: true, description: "`severidade` — D127." }
    occurred_at: { type: string, format: date-time, readOnly: true, description: "`data_hora` — evento derivado, um único timestamp basta." }
  required: [id, vehicle_id, type, severity, occurred_at]
```

## `Geofence` — Cerca Eletrônica (Configuração, D122/D289)

```yaml
Geofence:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    name: { type: string, description: "`nome` — único por tenant." }
    geometry_type: { type: string, enum: [CIRCULO, POLIGONO], description: "`tipo_geometria`." }
    center: { $ref: "#/GeoPoint", description: "Obrigatório quando geometry_type = CIRCULO." }
    radius_meters: { type: number, description: "`raio_metros` — obrigatório quando geometry_type = CIRCULO." }
    polygon:
      type: array
      items: { $ref: "#/GeoPoint" }
      description: "`poligono` — obrigatório quando geometry_type = POLIGONO."
    client_id: { $ref: "../components/schemas.md#/UUID", description: "`cliente_id` — opcional." }
    branch_id: { $ref: "../components/schemas.md#/UUID", description: "`filial_id` — opcional." }
    status: { type: string, enum: [ATIVA, INATIVA] }
    audit: { $ref: "../components/schemas.md#/AuditMetadata" }
  required: [id, name, geometry_type, status, audit]
```

## `SpeedLimitConfig` — Configuração de Limite de Velocidade

```yaml
SpeedLimitConfig:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    vehicle_category_id: { $ref: "../components/schemas.md#/UUID", description: "`categoria_veiculo_id` — opcional, ausente = padrão do tenant." }
    limit_kmh: { type: string, description: "`limite_kmh`." }
    status: { type: string, enum: [ATIVA, INATIVA] }
  required: [id, limit_kmh, status]
```

## `LocationOrigin` — Origem de Localização (Platform Reference Data)

```yaml
LocationOrigin:
  type: object
  description: "D046 — Platform Reference Data, sem tenant_id. Ex.: GPS/GSM/Satélite/Wi-Fi/BLE/Manual/API Externa."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    name: { type: string, readOnly: true, description: "`nome`." }
    typical_precision_meters: { type: number, readOnly: true, description: "`precisao_tipica_metros`." }
  required: [id, name]
```

## `TrackingHistoryEntry` — Read Model composto (D290)

```yaml
TrackingHistoryEntry:
  type: object
  description: "D290 — projeção composta a partir de Posição/Telemetria/Evento, nunca uma tabela própria."
  properties:
    occurred_at: { type: string, format: date-time }
    source: { type: string, enum: [POSICAO, TELEMETRIA, EVENTO], description: "Qual tabela física originou esta linha." }
    summary: { type: string }
    reference_id: { $ref: "../components/schemas.md#/UUID", description: "ID na tabela de origem — o cliente busca o detalhe completo em `048`/`049`/`051` quando precisar." }
  required: [occurred_at, source, summary, reference_id]
```

## Como este documento cresce

Adiantamento de sensores IoT (D120, "Requisitos futuros") não exige mudança de schema —
`sensor_type` já é um Enum extensível (`ALTER TYPE ... ADD VALUE`), consumido diretamente por
`TelemetryReading.sensor_type` sem nova propriedade.
