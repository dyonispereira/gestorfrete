# components/mobile-schemas.md — Schemas do App Motorista

Bounded context `mobile` (D215) para a infraestrutura própria (Sessão/Dispositivo/Sincronização);
schemas de domínio (Trip/Delivery/Occurrence) são **reaproveitados** de `trip-schemas.md`, nunca
duplicados (D303).

## `MobileSession` — Sessão Mobile

```yaml
MobileSession:
  type: object
  description: "D140 — nunca representa identidade, nunca cacheia RBAC (D060/D296)."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    driver_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`motorista_id`." }
    vehicle_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`veiculo_tracionador_id`." }
    device_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`dispositivo_mobile_id`." }
    auth_method: { type: string, enum: [CPF_VEICULO, BIOMETRIA, PIN], readOnly: true, description: "`metodo_autenticacao`." }
    started_at: { type: string, format: date-time, readOnly: true, description: "`data_hora_inicio`." }
    expires_at: { type: string, format: date-time, readOnly: true, description: "`data_hora_expiracao_prevista`." }
    ended_at: { type: string, format: date-time, readOnly: true, description: "`data_hora_encerramento`." }
    end_reason: { type: string, enum: [LOGOUT, REVOGACAO_ADMINISTRATIVA, TROCA_DE_DISPOSITIVO], readOnly: true, description: "`motivo_encerramento`." }
    status: { type: string, enum: [ATIVA, EXPIRADA, ENCERRADA], readOnly: true }
  required: [id, driver_id, vehicle_id, device_id, auth_method, started_at, expires_at, status]
```

## `MobileDevice` — Dispositivo Mobile

```yaml
MobileDevice:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    device_identifier: { type: string, readOnly: true, description: "`identificador_dispositivo` — único na plataforma, definido no primeiro registro." }
    os: { type: string, enum: [ANDROID, IOS], readOnly: true, description: "`sistema_operacional`." }
    os_version: { type: string, description: "`versao_so`." }
    app_version: { type: string, description: "`versao_app`." }
    push_token: { type: string, description: "`token_push` — D302, nunca dispara mudança de estado sozinho." }
    status: { type: string, enum: [ATIVO, INATIVO, REVOGADO] }
    last_access_at: { type: string, format: date-time, readOnly: true, description: "`ultimo_acesso_em` — D081, projeção." }
  required: [id, device_identifier, os, app_version, status]
```

## `SyncQueueItem` — Item da Fila de Sincronização

```yaml
SyncQueueItem:
  type: object
  description: "D137 — um comando atômico por item. D139 — payload nunca sobrescrito."
  properties:
    local_id: { type: string, description: "`identificador_local_unico` — chave de idempotência (D111/D138), gerada no dispositivo." }
    sequence: { type: integer, description: "`sequencia_local` — D136, ordem de criação no dispositivo." }
    command: { type: string, description: "`tipo_comando` — vocabulário extensível (D120), ex.: ACCEPT_TRIP/START_TRIP/REGISTER_OCCURRENCE." }
    target_entity_type: { type: string, description: "`entidade_destino_tipo`." }
    target_entity_id: { $ref: "../components/schemas.md#/UUID", description: "`entidade_destino_id`." }
    payload: { type: object, description: "Preservado integralmente (D139/D299) — nunca reescrito após criado." }
  required: [local_id, sequence, command, target_entity_type, target_entity_id, payload]
```

## `SyncItemResult` — Resultado por item

```yaml
SyncItemResult:
  type: object
  properties:
    local_id: { type: string, description: "Ecoa o `local_id` enviado — correlação cliente↔servidor." }
    result: { type: string, enum: [PROCESSADO, REJEITADO, CONFLITO, PENDENTE], readOnly: true }
    server_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "ID definitivo da entidade afetada, quando aplicável." }
    error: { $ref: "../components/schemas.md#/Error", readOnly: true, description: "Presente quando `result = REJEITADO`." }
    conflict:
      type: object
      readOnly: true
      description: "Presente quando `result = CONFLITO` (D300) — nunca decidido pelo cliente."
      properties:
        current_state: { type: object, description: "Estado atual da entidade no backend." }
        reason: { type: string }
  required: [local_id, result]
```

## `SyncBatchResponse`

```yaml
SyncBatchResponse:
  type: object
  properties:
    sync_record_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`registros_sincronizacao.id`." }
    results:
      type: array
      items: { $ref: "#/SyncItemResult" }
  required: [sync_record_id, results]
```

## `SyncRecord` — Registro de Sincronização (nível de lote, D135)

```yaml
SyncRecord:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    session_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`sessao_mobile_id`." }
    started_at: { type: string, format: date-time, readOnly: true, description: "`data_hora_inicio`." }
    finished_at: { type: string, format: date-time, readOnly: true, description: "`data_hora_fim`." }
    duration_ms: { type: integer, readOnly: true, description: "`duracao_ms` — GENERATED." }
    command_count: { type: integer, readOnly: true, description: "`quantidade_comandos`." }
    success_count: { type: integer, readOnly: true, description: "`quantidade_sucesso`." }
    failure_count: { type: integer, readOnly: true, description: "`quantidade_falha`." }
  required: [id, session_id, started_at, finished_at, command_count, success_count, failure_count]
```

## `DigitalSignature` — Assinatura Digital

```yaml
DigitalSignature:
  type: object
  description: "D301 — sempre file_id, nunca binário. Hoje só documento_tipo = CANHOTO (extensível)."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    document_type: { type: string, enum: [CANHOTO], readOnly: true, description: "`documento_tipo`." }
    document_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`documento_id` — polimórfico." }
    signatory_role: { type: string, enum: [MOTORISTA, CLIENTE, RECEBEDOR], readOnly: true, description: "`papel_signatario`." }
    signatory_name: { type: string, readOnly: true, description: "`nome_signatario_informado` — quando papel = RECEBEDOR sem cadastro." }
    file_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`arquivo_id` — D107/D301." }
    captured_at: { type: string, format: date-time, readOnly: true }
    received_at: { type: string, format: date-time, readOnly: true }
  required: [id, document_type, document_id, signatory_role, file_id, captured_at, received_at]
```

## Como este documento cresce

`assinaturas_digitais_documento_tipo_enum` é extensível (hoje só `CANHOTO`) — quando Checklist for
formalizado fisicamente (`056-driver-checklists.md`), `CHECKLIST` pode ser adicionado ao Enum sem
mudar este schema, só o valor aceito.
