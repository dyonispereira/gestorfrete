# CONFIGURATION_IMPLEMENTATION.md — Configuração Fiscal do Tenant

`configuracoes_fiscais_tenant` — única fonte de numeração de CT-e/MDF-e (D110). Fonte:
`relational/007-fiscal.md`, `045-configuracao-fiscal.md`. Singular por tenant
(`uq_configuracoes_fiscais_tenant_id`), mesmo padrão de `/assinatura`.

## `PATCH /configuracao-fiscal` — permissão por grupo de campo (D267-style, em escrita)

Quatro grupos, cada um com sua própria permissão — enviar um campo sem a permissão correspondente
rejeita a requisição **inteira** com `403` (D218-style, nunca um PATCH parcialmente aplicado):

| Campo(s) | Permissão |
|---|---|
| `tax_regime` | `documents.fiscal_config.edit` |
| `certificate_file_id`/`certificate_expires_at` | `documents.fiscal_config.manage_certificate` |
| `cte_series`/`mdfe_series` | `documents.fiscal_config.manage_series` |
| `environment` | `documents.fiscal_config.switch_environment` |

Implementado no Router (não no Handler): antes de montar o Command, verifica quais campos vieram no
corpo e quais permissões o ator tem — `AuthorizationError` se qualquer campo presente exigir uma
permissão ausente.

## Numeração atômica (D399)

`next_cte_number`/`next_mdfe_number` nunca digitáveis (`readOnly`) — a única forma de incrementar é
`CteRepository`/`MdfeRepository` capturando o próximo número via `SELECT ... FOR UPDATE` na linha de
`configuracoes_fiscais_tenant` do tenant, dentro da mesma transação da criação do documento.

## Sem `POST`/`DELETE`

Nasce no Onboarding (fora de escopo desta fundação) — para os testes, seed direto via Repository
(mesmo padrão de `PaymentMethod`, D386) já que não há um fluxo de Onboarding real implementado
ainda neste backend.

## Erros de domínio

`FISCAL_CONFIG_NOT_FOUND` (404, tenant sem configuração), `FISCAL_CONFIG_SERIES_IN_USE` (409, não
disparado nesta fundação — nenhuma verificação de "numeração em andamento" é modelada, mesma
disciplina de "endpoint documentado, condição de bloqueio vazia" de D394).

## Auditoria e tenant isolation

`PATCH` grava `logs_auditoria`. `SqlAlchemyFiscalConfigurationRepository` filtra por
`get_current_tenant_id()`.
