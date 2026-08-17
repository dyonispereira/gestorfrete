# components/fiscal-schemas.md — Schemas de Fiscal

Bounded context `documents` (D215). Schemas compartilhados por `039` a `045`.

## `CTe`

```yaml
CTe:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    trip_id: { $ref: "../components/schemas.md#/UUID", description: "`viagem_id` — FK, imutável." }
    number: { type: string, readOnly: true, description: "`numero` — cópia capturada de `configuracoes_fiscais_tenant` na emissão (D110), nunca calculada aqui." }
    series: { type: string, readOnly: true, description: "`serie`." }
    access_key: { type: string, readOnly: true, description: "`chave_acesso` — 44 dígitos, preenchida a partir de `TRANSMITIDO`." }
    service_value: { type: string, description: "`valor_servico`." }
    status: { type: string, enum: [RASCUNHO, VALIDADO, ASSINADO, TRANSMITIDO, AUTORIZADO, CANCELADO, DENEGADO, INUTILIZADO], readOnly: true, description: "D274 — nunca via PATCH." }
    xml_file_id: { $ref: "../components/schemas.md#/UUID", description: "D276 — referência a Storage, nunca o XML embutido." }
    sefaz_protocol: { type: string, readOnly: true, description: "`protocolo_sefaz` — D275, chave de idempotência." }
    authorized_at: { type: string, format: date-time, readOnly: true, description: "`data_hora_autorizacao`." }
    audit: { $ref: "../components/schemas.md#/AuditMetadata" }
  required: [id, trip_id, service_value, status, audit]
```

## `MDFe`

```yaml
MDFe:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    trip_id: { $ref: "../components/schemas.md#/UUID", description: "`viagem_id`." }
    number: { type: string, readOnly: true, description: "`numero`." }
    series: { type: string, readOnly: true, description: "`serie`." }
    access_key: { type: string, readOnly: true, description: "`chave_acesso`." }
    status: { type: string, enum: [PENDENTE, AUTORIZADO, ENCERRADO, CANCELADO], readOnly: true }
    cte_ids:
      type: array
      items: { $ref: "../components/schemas.md#/UUID" }
      description: "`mdfes_ctes` — um ou mais CT-e `AUTORIZADO` consolidados (multi-cliente/multi-carga)."
    xml_file_id: { $ref: "../components/schemas.md#/UUID" }
    sefaz_protocol: { type: string, readOnly: true, description: "`protocolo_sefaz`." }
    closed_at: { type: string, format: date-time, readOnly: true, description: "`data_hora_encerramento`." }
    audit: { $ref: "../components/schemas.md#/AuditMetadata" }
  required: [id, trip_id, cte_ids, status, audit]
```

## `CIOT`

```yaml
CIOT:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    trip_id: { $ref: "../components/schemas.md#/UUID", description: "`viagem_id`." }
    driver_id: { $ref: "../components/schemas.md#/UUID", description: "`motorista_id` — exige vínculo AUTÔNOMO (validação de aplicação)." }
    ciot_code: { type: string, readOnly: true, description: "`codigo_ciot` — atribuído pela ANTT no registro." }
    status: { type: string, enum: [PENDENTE, REGISTRADO, CANCELADO], readOnly: true }
    antt_protocol: { type: string, readOnly: true, description: "`protocolo_antt` — D275, chave de idempotência." }
    registered_at: { type: string, format: date-time, readOnly: true, description: "`data_hora_registro`." }
    audit: { $ref: "../components/schemas.md#/AuditMetadata" }
  required: [id, trip_id, driver_id, status, audit]
```

## `CorrectionLetter` — Carta de Correção

```yaml
CorrectionLetter:
  type: object
  description: "D282 — nunca altera o CT-e diretamente; artefato/evento próprio anexado a um CT-e `AUTORIZADO`."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    sequence_number: { type: integer, readOnly: true, description: "`numero_sequencial`." }
    correction_text: { type: string, description: "`texto_correcao`." }
    xml_file_id: { $ref: "../components/schemas.md#/UUID", readOnly: true }
    sent_at: { type: string, format: date-time, readOnly: true, description: "`data_hora_envio`." }
  required: [id, sequence_number, correction_text, sent_at]
```

## `ReferencedNFe` — NF-e Referenciada

```yaml
ReferencedNFe:
  type: object
  description: "Referência fiscal — nunca uma NF-e emitida pela transportadora."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    access_key: { type: string, description: "`chave_acesso` — 44 dígitos." }
    xml_file_id: { $ref: "../components/schemas.md#/UUID" }
  required: [id, access_key]
```

## `FiscalEvent` — Evento Fiscal

```yaml
FiscalEvent:
  type: object
  description: "D277 — log técnico bruto, somente leitura para usuários. Distinto dos *StatusHistory de negócio (D281)."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    document_type: { type: string, enum: [CTE, MDFE, CIOT], readOnly: true, description: "`documento_tipo`." }
    document_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`documento_id` — polimórfico." }
    event_type: { type: string, enum: [REQUISICAO, RESPOSTA], readOnly: true, description: "`tipo_evento`." }
    payload_file_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "Payload sempre em Storage, nunca inline." }
    external_protocol: { type: string, readOnly: true, description: "`protocolo_externo` — D275." }
    started_at: { type: string, format: date-time, readOnly: true, description: "`data_hora_inicio`." }
    finished_at: { type: string, format: date-time, readOnly: true, description: "`data_hora_fim`." }
    duration_ms: { type: integer, readOnly: true, description: "`duracao_ms` — GENERATED." }
    attempt_number: { type: integer, readOnly: true, description: "`numero_tentativa`." }
    result: { type: string, enum: [SUCESSO, FALHA, TIMEOUT], readOnly: true, description: "`resultado`." }
    origin: { type: string, readOnly: true, description: "`origem` — 'documents' (automático) ou usuário (reenvio manual)." }
  required: [id, document_type, document_id, event_type, started_at, origin]
```

## Histórico de Status (D281) — três schemas, campos não uniformes até D284

`flows/009-FISCAL.md` pede os mesmos campos padrão para as três máquinas; a auditoria desta
preparação (D284) alinhou as três tabelas físicas para that padrão — os três schemas abaixo já
refletem isso, mesmo que fossem assimétricos antes da correção.

```yaml
CTeStatusHistoryEntry:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    status: { type: string, enum: [RASCUNHO, VALIDADO, ASSINADO, TRANSMITIDO, AUTORIZADO, CANCELADO, DENEGADO, INUTILIZADO] }
    user_id: { $ref: "../components/schemas.md#/UUID", description: "`usuario_id` — nulo quando a transição é automática (resposta SEFAZ)." }
    origin: { type: string, description: "`origem`." }
    notes: { type: string, description: "`observacao` — obrigatória em CANCELADO/DENEGADO." }
    occurred_at: { type: string, format: date-time, description: "`data_hora`." }
  required: [id, status, origin, occurred_at]

MDFeStatusHistoryEntry:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    status: { type: string, enum: [PENDENTE, AUTORIZADO, ENCERRADO, CANCELADO] }
    user_id: { $ref: "../components/schemas.md#/UUID" }
    origin: { type: string, description: "`origem`." }
    notes: { type: string, description: "`observacao`." }
    occurred_at: { type: string, format: date-time }
  required: [id, status, origin, occurred_at]

CIOTStatusHistoryEntry:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    status: { type: string, enum: [PENDENTE, REGISTRADO, CANCELADO] }
    user_id: { $ref: "../components/schemas.md#/UUID" }
    origin: { type: string, description: "`origem`." }
    notes: { type: string, description: "`observacao`." }
    occurred_at: { type: string, format: date-time }
  required: [id, status, origin, occurred_at]
```

## `FiscalConfiguration` — Configuração Fiscal do Tenant

```yaml
FiscalConfiguration:
  type: object
  description: "D110/D279 — única fonte de numeração de CT-e/MDF-e; certificado nunca retornado como segredo."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    certificate_file_id: { $ref: "../components/schemas.md#/UUID", description: "`certificado_arquivo_id` — D279, referência, nunca o conteúdo do certificado." }
    certificate_expires_at: { type: string, format: date, description: "`certificado_validade`." }
    environment: { type: string, enum: [PRODUCAO, HOMOLOGACAO], description: "`ambiente`." }
    tax_regime: { type: string, description: "`regime_tributario`." }
    cte_series: { type: string, description: "`serie_cte`." }
    next_cte_number: { type: integer, readOnly: true, description: "`proximo_numero_cte` — D110, nunca decresce nem é reutilizado." }
    mdfe_series: { type: string, description: "`serie_mdfe`." }
    next_mdfe_number: { type: integer, readOnly: true, description: "`proximo_numero_mdfe`." }
    status: { type: string, enum: [ATIVA, INATIVA] }
    audit: { $ref: "../components/schemas.md#/AuditMetadata" }
  required: [id, certificate_file_id, certificate_expires_at, environment, tax_regime, cte_series, mdfe_series, status, audit]
```

## Como este documento cresce

Nenhum campo de conteúdo de certificado, XML ou payload de integração é adicionado aqui — sempre
referência (`*_file_id`)/protocolo, nunca o artefato binário (D276/D279).
