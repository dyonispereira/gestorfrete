# 045 — Configuração Fiscal do Tenant

Bounded context proprietário: `documents` (D215). `configuracoes_fiscais_tenant` — única fonte de
numeração de CT-e/MDF-e (D110); `ctes.numero`/`mdfes.numero` são sempre cópias capturadas daqui,
nunca sequências próprias (`039-cte.md`/`040-mdfe.md`).

## D283 — RBAC não existia, corrigido na origem

`RBAC_MATRIX.md` §7.17 não tinha nenhum código para Configuração Fiscal antes desta preparação
(D200 aplicado à API) — terceira ocorrência desse tipo de lacuna nesta sprint (após `financial.
chart_of_accounts`/`financial.bank_account`, D271, Lote 7). Corrigido: `documents.fiscal_config.
view`/`.edit`/`.manage_certificate`/`.manage_series`/`.switch_environment` adicionados antes de
escrever este documento — granularidade alinhada ao pedido explícito do usuário (visualizar/
configurar/certificado/série/homologação-produção, cada um com sua própria permissão dado o nível
de sensibilidade distinto de cada ação).

## `GET /api/v1/configuracao-fiscal`

Singular — no máximo uma Configuração Fiscal por tenant (`uq_configuracoes_fiscais_tenant_id`),
mesmo padrão de `/assinatura` (`035-recurring-billing.md`).

**Segurança**: `bearerAuth` + `documents.fiscal_config.view`.

**Responses**: `200` (`FiscalConfiguration`, `fiscal-schemas.md`), `401`, `403`, `404` —
`FISCAL_CONFIG_NOT_FOUND` (tenant ainda não configurou, cenário só possível antes da primeira
emissão), `500`.

## `PATCH /api/v1/configuracao-fiscal`

D229 — parcial, mas **cada grupo de campo exige uma permissão diferente** (D267-style, segunda
aplicação de autorização por campo desta vez em nível de escrita, não só leitura):

| Campo | Permissão exigida |
|---|---|
| `tax_regime` (`regime_tributario`) | `documents.fiscal_config.edit` |
| `certificate_file_id`/`certificate_expires_at` | `documents.fiscal_config.manage_certificate` |
| `cte_series`/`mdfe_series` | `documents.fiscal_config.manage_series` |
| `environment` | `documents.fiscal_config.switch_environment` |

Enviar um campo sem a permissão correspondente resulta em `403` — nunca um `PATCH` parcialmente
aplicado silenciosamente ignorando o campo não autorizado (D218-style rigor: melhor rejeitar a
requisição inteira do que aplicar parte dela sem checagem explícita).

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          tax_regime: { type: string }
          certificate_file_id: { $ref: "components/schemas.md#/UUID" }
          certificate_expires_at: { type: string, format: date }
          cte_series: { type: string }
          mdfe_series: { type: string }
          environment: { type: string, enum: [PRODUCAO, HOMOLOGACAO] }
```

**D279 — nunca aceita o conteúdo do certificado no corpo**: `certificate_file_id` é sempre uma
referência a um arquivo já enviado a Storage (fluxo de upload fora deste endpoint, mesmo padrão de
`021-vehicle-documents.md`) — a API nunca recebe/retorna bytes de certificado digital.

**Responses**: `200` (`FiscalConfiguration`), `400`, `401`, `403`, `404`, `409` —
`FISCAL_CONFIG_SERIES_IN_USE` (trocar série com numeração em andamento pode exigir confirmação
explícita — regra de negócio a detalhar na implementação), `500`.

## `next_cte_number`/`next_mdfe_number` — nunca digitáveis

`readOnly` em `FiscalConfiguration` (D263-style, mesmo princípio de "saldo é derivado" aplicado
aqui a numeração: o próximo número é obtido atomicamente pela aplicação no momento da emissão,
nunca setado diretamente via API — mesmo com `.manage_series`, o cliente só troca a `série` em si,
nunca o contador).

## Sem `POST`/`DELETE`

Configuração Fiscal nasce durante o Onboarding do tenant (mesmo padrão de `Assinatura`,
`035-recurring-billing.md`) — sem `POST` público neste lote. `DELETE` não faz sentido para uma
configuração ativa de uso contínuo — desativação, se necessária, seria via `status = INATIVA`
(campo já existe), não modelado como comando explícito neste lote por falta de caso de uso
documentado.

## Fora de escopo, não esquecido

- **Upload do arquivo de certificado**: fluxo de Storage (obter `certificate_file_id`) não é
  detalhado aqui — mesmo tratamento de todo `*_arquivo_id` em toda a API até agora.
- **Alerta de vencimento de certificado**: `certificate_expires_at` já existe no schema, mas o
  mecanismo de notificação (`notification_center`) não é um endpoint deste lote.

## Como este documento cresce

Se `regime_tributario` evoluir de `TEXT` livre para um Enum fechado (regimes tributários têm um
conjunto finito real), isso é decisão de Domain/DDL primeiro (D101/D102) — o contrato aqui já aceita
qualquer string, sem mudança de schema necessária quando isso acontecer.
