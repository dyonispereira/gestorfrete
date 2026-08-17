# 087 — Integrations (Configuração de Integração)

Bounded context proprietário: `integration` (D215). `configuracoes_integracao` — Master Data,
D321: contrato único, nunca uma API diferente por fornecedor.

## D321 — sem detalhe de fornecedor no contrato

Mesmo princípio de `078-storage.md` (D314) e `AnalyticsCube` (Lote 11): `tipo` é um valor de
vocabulário (`ERP Externo`/`Contabilidade`/...), nunca o nome comercial de um produto específico
tratado como schema. A lógica de tradução de dados de cada integração é infraestrutura (adapter),
mesmo princípio já usado para Provedor de Rastreamento (D291, Lote 9).

## `GET /api/v1/integrations`

**Segurança**: `bearerAuth` + `integration.config.view`.

**Query parameters**: `page`/`limit`, `type`, `status` (`ATIVA`/`INATIVA`/`COM_ERRO`).

**Responses**: `200` (`Pagination` de `IntegrationConfig`, `components/transversal-schemas.md`),
`401`, `403`, `500`.

## `GET /api/v1/integrations/{id}`

**Responses**: `200` (`IntegrationConfig`), `401`, `403`, `404`, `500`.

## `POST /api/v1/integrations`

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          type: { type: string }
          credential_file_id: { $ref: "components/schemas.md#/UUID", description: "Referência a File (079) já enviado via 078-storage.md — nunca a credencial em texto claro no corpo." }
        required: [type, credential_file_id]
```

`credencial_arquivo_id` nunca aceita texto claro (mesma disciplina de `USUARIO.SENHA_HASH` e do
certificado digital fiscal, D279) — o cliente primeiro envia a credencial via `078-storage.md`
(upload para um "cofre" — bucket de acesso restrito, detalhe de infraestrutura), depois referencia o
`file_id` aqui.

**Segurança**: `integration.config.create`.

**Responses**: `201` (`IntegrationConfig`, `status = ATIVA`), `400`, `401`, `403`, `404`
(`credential_file_id` não existe), `500`.

## `PATCH /api/v1/integrations/{id}`

D229 — parcial (`credential_file_id`, para rotação de credencial).

**Segurança**: `integration.config.edit`.

**Responses**: `200`, `400`, `401`, `403`, `404`, `500`.

## `POST /api/v1/integrations/{id}/commands/enable`

`INATIVA → ATIVA`.

**Segurança**: `integration.config.enable`.

**Responses**: `200` (`IntegrationConfig`), `401`, `403`, `404`, `409`, `500`.

## `POST /api/v1/integrations/{id}/commands/disable`

`ATIVA → INATIVA` (`COM_ERRO` também pode ser desabilitada manualmente).

**Segurança**: `integration.config.disable`.

**Responses**: `200`, `401`, `403`, `404`, `409`, `500`.

## `status = COM_ERRO` — sempre derivado, nunca um comando

Não existe `commands/mark-error` — `COM_ERRO` é calculado pela aplicação quando uma chamada real ao
adapter de infraestrutura falha (detalhe de implementação, fora deste contrato), nunca uma
transição que o cliente HTTP dispara diretamente.

## Sem `DELETE`

`RBAC_MATRIX.md` não tem `integration.config.delete` — desativação via `commands/disable`. Webhooks
vinculados (`088-webhooks.md`, `configuracao_integracao_id` opcional) permanecem intactos mesmo com
a Integração desabilitada — vínculo é referencial, não uma dependência de ciclo de vida (FK
`ON DELETE` nunca chega a ser relevante, pois não há exclusão física, D001).

## Como este documento cresce

Se um tipo de integração precisar de campos de configuração específicos além de
`type`/`credential_file_id` (ex.: URL base do ERP externo), isso é decisão de Domain/DDL primeiro
(`configuracoes_integracao` hoje só tem esses dois) — nunca um campo `config: object` livre sem
coluna física correspondente.
