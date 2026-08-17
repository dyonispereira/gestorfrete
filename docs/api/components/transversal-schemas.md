# components/transversal-schemas.md — Schemas de Recursos Transversais

Bounded contexts `storage` (File/Attachment/Comment), `notification_center` (Notification/
ChannelPreference) e `integration` (IntegrationConfig/Webhook/JobExecution) — Sprint 10, Lote 12.

## `File`

```yaml
File:
  type: object
  description: "D315 — metadados do arquivo, distinto do mecanismo de Storage (078). D324."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    name: { type: string, description: "`nome_original`." }
    mime_type: { type: string, description: "`tipo_mime`." }
    size_bytes: { type: integer, description: "`tamanho_bytes`." }
    hash: { type: string, readOnly: true, description: "`hash_sha256`." }
    version: { type: integer, readOnly: true, description: "`versao` — nunca decresce." }
    previous_file_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`arquivo_anterior_id`." }
    origin: { type: string, enum: [UPLOAD_DIRETO, GERADO_PELO_SISTEMA, IMPORTADO], readOnly: true, description: "`origem`." }
    status: { type: string, enum: [ATIVO, EXCLUIDO], readOnly: true }
    created_at: { type: string, format: date-time, readOnly: true, description: "`criado_em`." }
  required: [id, name, mime_type, size_bytes, hash, version, origin, status, created_at]
```

## `Attachment`

```yaml
Attachment:
  type: object
  description: "D186/D316 — infraestrutura polimórfica compartilhada; dono sempre resolvido pelo path, nunca por campo do corpo."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    attachment_type: { type: string, description: "`tipo_anexo` — vocabulário extensível (D120-style): FOTO/ASSINATURA/XML/PDF/..." }
    file_id: { $ref: "../components/schemas.md#/UUID", description: "Referência a File (079) — nunca binário embutido." }
    description: { type: string }
    audit: { $ref: "../components/schemas.md#/AuditMetadata" }
  required: [id, attachment_type, file_id, audit]
```

## `Comment`

```yaml
Comment:
  type: object
  description: "D186/D316 — mesma infraestrutura compartilhada de Attachment."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    text: { type: string, description: "`texto`." }
    visible_to_client: { type: boolean, description: "`visivel_cliente` — D023. Conteúdo, nunca mecanismo de autorização." }
    author_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`usuario_id`." }
    audit: { $ref: "../components/schemas.md#/AuditMetadata" }
  required: [id, text, visible_to_client, author_id, audit]
```

## `Notification`

```yaml
Notification:
  type: object
  description: "D320 — efeito colateral de um evento de domínio, nunca a origem de uma nova decisão."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    channel: { type: string, enum: [IN_APP, PUSH, EMAIL], readOnly: true, description: "`canal`." }
    origin_event_type: { type: string, readOnly: true, description: "`evento_origem_tipo` — ex.: \"ViagemAtrasada\"." }
    entity_type: { type: string, readOnly: true, description: "`entidade_tipo` — referência opcional." }
    entity_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`entidade_id`." }
    title: { type: string, readOnly: true, description: "`titulo`." }
    message: { type: string, readOnly: true, description: "`mensagem`." }
    status: { type: string, enum: [NAO_LIDA, LIDA], readOnly: true }
    sent_at: { type: string, format: date-time, readOnly: true, description: "`enviado_em`." }
    read_at: { type: string, format: date-time, readOnly: true, description: "`lido_em`." }
  required: [id, channel, origin_event_type, title, message, status, sent_at]
```

## `ChannelPreference`

```yaml
ChannelPreference:
  type: object
  properties:
    channel: { type: string, enum: [IN_APP, PUSH, EMAIL], readOnly: true, description: "`canal`." }
    enabled: { type: boolean, description: "`habilitado` — default true quando nenhuma preferência foi salva." }
  required: [channel, enabled]
```

## `IntegrationConfig`

```yaml
IntegrationConfig:
  type: object
  description: "D321 — contrato único, nunca uma API diferente por fornecedor."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    type: { type: string, description: "`tipo` — ex.: \"ERP Externo\"/\"Contabilidade\"." }
    credential_file_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`credencial_arquivo_id` — nunca texto claro." }
    status: { type: string, enum: [ATIVA, INATIVA, COM_ERRO], readOnly: true }
    audit: { $ref: "../components/schemas.md#/AuditMetadata" }
  required: [id, type, credential_file_id, status, audit]
```

## `Webhook`

```yaml
Webhook:
  type: object
  description: "D111/D138 — entrega idempotente, reprocessável sem efeito colateral."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    integration_config_id: { $ref: "../components/schemas.md#/UUID", description: "`configuracao_integracao_id` — opcional, standalone quando ausente." }
    target_url: { type: string, format: uri, description: "`url_destino`." }
    subscribed_events: { type: array, items: { type: string }, description: "`eventos_assinados`." }
    signing_secret: { type: string, description: "Só presente na resposta do POST de criação — nunca reexibido depois." }
    status: { type: string, enum: [ATIVO, INATIVO, SUSPENSO], readOnly: true }
    audit: { $ref: "../components/schemas.md#/AuditMetadata" }
  required: [id, target_url, subscribed_events, status, audit]
```

## `JobExecution`

```yaml
JobExecution:
  type: object
  description: "D037 — histórica, nunca editada após criada. D322 — job_type sempre de um vocabulário já registrado no Backend."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    job_type: { type: string, readOnly: true, description: "`tipo_job`." }
    started_at: { type: string, format: date-time, readOnly: true, description: "`data_hora_inicio`." }
    finished_at: { type: string, format: date-time, readOnly: true, description: "`data_hora_fim`." }
    result: { type: string, enum: [SUCESSO, FALHA], readOnly: true, description: "`resultado`." }
  required: [id, job_type, started_at]
```

## Como este documento cresce

Nenhum schema aqui menciona um fornecedor/provedor físico específico (Storage, Integração) — mesmo
princípio de domínio-agnosticismo aplicado em todo o sprint (D291/D314/D321).
