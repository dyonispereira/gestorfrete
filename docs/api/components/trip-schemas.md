# components/trip-schemas.md — Schemas do Agregado Viagem

Schemas compartilhados por todo o Lote 4 (`014` a `019`) — Viagem é o primeiro Aggregate Root
complexo do contrato (bounded context `freight`, D215), então seus schemas ficam num arquivo
próprio em vez de inchar `components/schemas.md` (que continua servindo os schemas genéricos e das
entidades mais simples dos Lotes 2/3).

## `TripStatus`

As três dimensões (D019/D020) — nunca colapsadas em um único campo `status`.

```yaml
TripStatus:
  type: object
  description: Espelha viagens.status_operacional/status_fiscal/status_financeiro/encerrada. Todo
    o objeto é readOnly — nenhuma dimensão é editável por CRUD (D233), só por comando
    (018-trip-status.md).
  properties:
    operational:
      type: string
      enum: [RASCUNHO, PLANEJADA, AGUARDANDO_CHECKLIST, LIBERADA, EM_DESLOCAMENTO, CARREGANDO, EM_TRANSITO, EM_ENTREGA, FINALIZADA, INTERROMPIDA, CANCELADA]
      readOnly: true
    fiscal:
      type: string
      enum: [PENDENTE, CTE_EMITIDO, MDFE_EMITIDO, MDFE_ENCERRADO, CTE_CANCELADO]
      readOnly: true
    financial:
      type: string
      enum: [AGUARDANDO_FATURAMENTO, FATURADA, AGUARDANDO_RECEBIMENTO, RECEBIDA]
      readOnly: true
    closed:
      type: boolean
      readOnly: true
      description: "`encerrada` — GENERATED no banco (D019/D020), verdadeiro só quando as três
        dimensões atingem seu estado terminal simultaneamente. Nunca aceito em nenhum request,
        em nenhum endpoint, para nenhum perfil (nem Administrador SaaS — 018-trip-status.md)."
  required: [operational, fiscal, financial, closed]
```

## `TripReferences` vs. `TripSnapshots` — nunca confundidos

```yaml
TripReferences:
  type: object
  description: Referências vivas (D033/D034) — sempre o estado *atual* da entidade referenciada.
    Mudam de valor se o Cliente for renomeado, o Motorista trocar de telefone, etc.
  properties:
    client_id: { $ref: "../components/schemas.md#/UUID" }
    driver_id: { $ref: "../components/schemas.md#/UUID", nullable: true }
    tractor_unit_id: { $ref: "../components/schemas.md#/UUID", nullable: true }
  required: [client_id]

TripSnapshots:
  type: object
  description: >-
    Capturados uma única vez (D038/D071/D073) — congelados no momento relevante, nunca
    ressincronizados mesmo que a entidade de origem mude depois. Todo campo aqui é `readOnly`;
    nenhum é aceito em `POST`/`PATCH` (o snapshot é gerado pela Application a partir das
    referências no momento da transição, nunca escrito pelo cliente).
  properties:
    driver_name_snapshot: { type: string, nullable: true, readOnly: true }
    tractor_unit_plate_snapshot: { type: string, nullable: true, readOnly: true }
    client_snapshot:
      type: object
      readOnly: true
      nullable: true
      description: "`cliente_snapshot` (JSONB) — dados do Cliente congelados no momento da
        criação/despacho, formato interno não normatizado neste contrato (passthrough)."
    predicted_revenue_snapshot: { type: string, nullable: true, readOnly: true }
    applied_price_table_id:
      $ref: "../components/schemas.md#/UUID"
      nullable: true
  required: []
```

## `TripFinancials`

```yaml
TripFinancials:
  type: object
  description: Pares Previsto/Realizado (D086/D098) — nenhum substitui o outro. Todo campo é
    readOnly (calculado pela Application/Domain, nunca escrito diretamente pela API — mudar o
    Custo Realizado, por exemplo, é responsabilidade do módulo financial/manutenção que gera a
    despesa, não um PATCH direto em Viagem).
  properties:
    predicted_cost: { type: string, nullable: true, readOnly: true }
    actual_cost: { type: string, nullable: true, readOnly: true }
    actual_revenue: { type: string, nullable: true, readOnly: true }
    predicted_margin:
      type: string
      nullable: true
      readOnly: true
      description: "`margem_prevista` — GENERATED (receita_prevista_snapshot - custo_previsto)."
    actual_margin:
      type: string
      nullable: true
      readOnly: true
      description: "`margem_realizada` — NÃO gerada no banco; só definitiva quando `status.closed
        = true` (D019). Antes disso é uma estimativa provisória recalculada pela aplicação a cada
        atualização de custo/receita realizado — o contrato não distingue 'provisório' de
        'definitivo' com um campo à parte neste lote; ler junto com `status.closed`."
    financial_deviation: { type: string, nullable: true, readOnly: true }
  required: []
```

## `Trip`

```yaml
Trip:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    codigo: { type: string, example: "VG-2026-000123" }
    scheduled_date: { type: string, format: date, nullable: true, description: "`data_programada`." }
    scheduled_window: { type: string, format: date-time, nullable: true, description: "`janela_programada`." }
    references: { $ref: "#/TripReferences" }
    snapshots: { $ref: "#/TripSnapshots" }
    status: { $ref: "#/TripStatus" }
    financials: { $ref: "#/TripFinancials" }
    distance_traveled_km:
      type: string
      nullable: true
      readOnly: true
      description: "`km_rodado` — projeção derivada de `tracking` (D081), não é fonte de verdade;
        nunca aceito em request."
    audit: { $ref: "../components/schemas.md#/AuditMetadata" }
  required: [id, codigo, references, status, audit]
```

## `TripAllocation`

Ver [`016-trip-resources.md`](../016-trip-resources.md) para o contrato completo — schema aqui
para reuso por `Trip` quando expandido.

```yaml
TripAllocation:
  type: object
  description: "`alocacoes_recurso_viagem` — pacote atômico (D188), nunca Motorista/Veículo/
    Implemento como recursos independentes."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    driver_id: { $ref: "../components/schemas.md#/UUID" }
    tractor_unit_id: { $ref: "../components/schemas.md#/UUID" }
    implement_id: { $ref: "../components/schemas.md#/UUID", nullable: true }
    status: { type: string, enum: [VIGENTE, SUBSTITUIDA], readOnly: true }
    replacement_reason: { type: string, nullable: true, description: "`motivo_troca`." }
    created_at: { $ref: "../components/schemas.md#/Timestamp" }
  required: [id, driver_id, tractor_unit_id, status, created_at]
```

## `Delivery`

```yaml
Delivery:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    order: { type: integer, minimum: 1, description: "`ordem` — único por Viagem (`uq_entregas_viagem_id_ordem`)." }
    recipient: { type: string, description: "`destinatario`." }
    delivery_address: { type: object, description: "`endereco_entrega` (JSONB), passthrough." }
    status: { type: string, enum: [PENDENTE, CONCLUIDA, RECUSADA, DEVOLVIDA, CANCELADA] }
    completed_at: { type: string, format: date-time, nullable: true, readOnly: true, description: "`data_hora_conclusao`." }
    rejection_reason: { type: string, nullable: true, description: "`motivo_recusa` — obrigatório quando `status = RECUSADA`." }
    window:
      type: object
      nullable: true
      description: "`janelas_entrega` (1:1, opcional) — presente só quando a Entrega tem janela definida."
      properties:
        starts_at: { type: string, format: date-time }
        ends_at: { type: string, format: date-time }
      required: [starts_at, ends_at]
    audit: { $ref: "../components/schemas.md#/AuditMetadata" }
  required: [id, order, recipient, delivery_address, status, audit]
```

## `ProofOfDelivery` (Canhoto)

```yaml
ProofOfDelivery:
  type: object
  description: "1:1 com Delivery (`uq_canhotos_entrega_id`) — fotos adicionais usam o sistema
    compartilhado de Anexos (`entidade_tipo = CANHOTO`), nunca binário embutido aqui."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    status: { type: string, enum: [PENDENTE, REGISTRADO] }
    registered_at: { type: string, format: date-time, nullable: true, readOnly: true, description: "`data_hora_registro`." }
    signature_file_id:
      $ref: "../components/schemas.md#/UUID"
      nullable: true
      description: "`assinatura_arquivo_id` — referência lógica ao Storage (D107), nunca o binário
        inline."
  required: [id, status]
```

## `Occurrence`

```yaml
Occurrence:
  type: object
  description: "Uma única entidade para todo tipo (D076) — nunca uma API por tipo de ocorrência."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    type: { type: string, enum: [ATRASO, AVARIA, PANE, SINISTRO, OUTRO], description: "`tipo`." }
    description: { type: string, description: "`descricao`." }
    severity: { type: string, nullable: true, enum: [BAIXA, MEDIA, ALTA, CRITICA], description: "`gravidade`." }
    status: { type: string, enum: [ABERTA, RESOLVIDA] }
    occurred_at: { type: string, format: date-time, description: "`data_hora`." }
    location:
      type: object
      nullable: true
      description: Coordenadas do evento, quando capturadas pelo app no momento do registro —
        não persistido como coluna própria em `ocorrencias` neste Modelo Relacional (ver nota em
        017-trip-occurrences.md).
  required: [id, type, description, status, occurred_at]
```

## `TripStatusHistoryEntry`

```yaml
TripStatusHistoryEntry:
  type: object
  description: Uma linha de `viagem_status_history` — nunca editável, sempre append-only (D017/D018).
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    dimension: { type: string, enum: [OPERACIONAL, FISCAL, FINANCEIRO, COMPOSTO], description: "`dimensao`." }
    status: { type: string }
    actor_id:
      $ref: "../components/schemas.md#/UUID"
      nullable: true
      description: "`usuario_id` — nulo quando a transição é automática ('sistema')."
    origin: { type: string, description: "`origem` — ex.: app_motorista, portal_gestor, webhook_sefaz." }
    occurred_at: { type: string, format: date-time, description: "`data_hora`." }
    notes: { type: string, nullable: true, description: "`observacao` — obrigatória nas transições de exceção." }
    latitude: { type: number, format: double, nullable: true }
    longitude: { type: number, format: double, nullable: true }
  required: [id, dimension, status, origin, occurred_at]
```

## `TripTimelineEntry`

Ver [`019-trip-timeline.md`](../019-trip-timeline.md) — projeção de leitura (D187/D022), nunca uma
tabela própria.

```yaml
TripTimelineEntry:
  type: object
  properties:
    occurred_at: { type: string, format: date-time }
    source:
      type: string
      enum: [STATUS_OPERACIONAL, STATUS_FISCAL, STATUS_FINANCEIRO, STATUS_COMPOSTO, OCORRENCIA, COMENTARIO, ANEXO, CHECKLIST, ABASTECIMENTO, ORDEM_SERVICO, DOCUMENTO_FISCAL]
      description: De qual UNION ALL de origem esta entrada veio (D187/D022).
    summary: { type: string, description: Texto legível da entrada (ex. "Checklist aprovado", "Entrega 1 concluída"). }
    reference_id:
      $ref: "../components/schemas.md#/UUID"
      description: ID do registro de origem (uma linha de status_history, uma Ocorrência, um Anexo, etc.) — para o cliente buscar detalhe completo se precisar.
  required: [occurred_at, source, summary, reference_id]
```

## Como este documento cresce

Todo novo sub-recurso de Viagem (Lote 5 em diante, se houver) referencia estes schemas — nunca
redefine `Trip`/`TripStatus`/snapshots em outro arquivo.
