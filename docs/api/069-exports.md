# 069 — Exports (Exportações)

Bounded context proprietário: `reporting` (D215). `exportacoes_geradas` — Histórica, D157: contexto
completo (filtros, período, usuário, versão das métricas) sempre presente.

## D307 — assíncrona por padrão

**Nunca bloqueia a requisição HTTP** esperando a geração de um arquivo grande — o padrão de estado
já é assíncrono na própria DDL (`status` nasce `PROCESSANDO`, nunca `CONCLUIDA` na mesma
transação do `POST`).

```
POST /exports  →  201, status: PROCESSANDO
                        ↓ (processamento assíncrono)
                   status: CONCLUIDA + arquivo_id
                        ou
                   status: FALHOU + error_message
```

## `GET /api/v1/reporting/exports`

**Segurança**: `bearerAuth` + `reporting.export.view_own`.

**Query parameters**: `page`/`limit`, `status`, `saved_report_id`.

**Responses**: `200` (`Pagination` de `Export`, `bi-schemas.md`), `401`, `403`, `500`.

## `GET /api/v1/reporting/exports/{id}`

Endpoint de polling — o cliente consulta até `status` sair de `PROCESSANDO`.

**Segurança**: `reporting.export.view_own`. **Responses**: `200` (`Export`), `401`, `403`, `404`,
`500`.

## `POST /api/v1/reporting/exports`

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          saved_report_id: { $ref: "components/schemas.md#/UUID" }
          filters: { type: object, description: "Exportação avulsa (sem `saved_report_id`) exige filtros diretamente." }
          period: { type: string }
          output_format: { type: string, enum: [PDF, EXCEL, CSV] }
```

`filters_used`/`period`/`metric_versions` no `Export` resultante são **sempre capturados pela
aplicação no momento da solicitação** (D157) — nunca aceitos como cópia literal do corpo, mesmo
quando o cliente os informa (o backend resolve `saved_report_id` → filtros/métricas reais no
momento exato da chamada, garantindo que a exportação reflita o estado atual do Relatório Salvo).

**Segurança**: `reporting.export.create`. **Idempotency-Key**: obrigatório (D211/D307 — evita gerar
duas exportações idênticas por retry de rede).

**Responses**: `201` (`Export`, `status = PROCESSANDO`), `400`, `401`, `403`, `404` (Relatório
Salvo/Métrica não existe), `500`.

## `arquivo_id` — D308, sempre Storage

`file_id` só é preenchido quando `status = CONCLUIDA` — nunca o conteúdo binário embutido em
nenhum momento do ciclo de vida deste recurso, mesmo padrão de `xml_file_id`/`certificate_file_id`
(Lote 8) e `photo_file_id`/`signature_file_id` (Lote 10).

## Sem `PATCH`/`DELETE`

Exportação é, por natureza, um registro pontual e histórico — corrigir uma exportação errada é
solicitar uma nova (`POST` de novo), nunca editar/remover a existente (D109-style, mesmo princípio
de todo artefato gerado neste sistema).

## Como este documento cresce

Se o volume de exportações justificar um limite de retenção (arquivo expira/é removido do Storage
após N dias), isso é política de infraestrutura — o registro em `exportacoes_geradas` permanece
(histórico nunca é apagado, D001), só `file_id` pode passar a apontar para um arquivo já expirado
no Storage, detalhe de implementação não normatizado aqui.
