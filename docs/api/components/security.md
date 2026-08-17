# components/security.md — Esquemas de Segurança e Mapeamento RBAC

## D216 — OpenAPI referencia RBAC existente

Nenhum código de permissão é criado neste documento ou em qualquer endpoint — todo código abaixo já
existe em [`../../product/RBAC_MATRIX.md`](../../product/RBAC_MATRIX.md), confirmado nesta
preparação (D200-style, verificado contra o arquivo real, não citado de memória): seções 7.4
(`identity_access`) e 7.5 (`tenancy`) no Lote 2; 7.1 (`crm`), 7.2 (`maintenance`), 7.3 (`drivers`) e
7.18 (`financial`, só `cost_center.*`) no Lote 3; 7.12 (`freight` — Viagem) e 7.13 (`freight` —
Entrega/Coleta/Ocorrência/Romaneio/Canhoto) no Lote 4; 7.8 (`fleet`) no Lote 5. A ausência confirmada de
`financial.cost_center.delete` (só `.view`/`.create`/`.edit` existem) é o motivo de
`013-cost-centers.md` não ter endpoint de exclusão — mesma disciplina, não uma omissão. No Lote 4,
a mesma leitura completa encontrou **duas lacunas de granularidade** (D240): não há código
dedicado para Interromper/Retomar Viagem nem para o aceite do Motorista (D129) — resolução
escolhida pelo usuário foi reaproveitar `freight.trip.edit` nesses três comandos, documentado
explicitamente em `018-trip-status.md`, nunca uma permissão nova criada sem passar pela matriz
oficial primeiro. No Lote 5, a mesma leitura completa de 7.8 confirmou o mesmo padrão de lacuna
para `fleet.vehicle_document`: existe `.view`/`.create`/`.attach`, não existe `.edit` — resolvida
por **precedente direto de D240** (reaproveitar o código mais próximo, `.attach`, documentado em
`021-vehicle-documents.md`), sem reabrir `AskUserQuestion` para um caso estruturalmente idêntico.
No Lote 6 (7.9 `maintenance` — Ordem de Serviço), a leitura completa encontrou a lacuna **mais
ampla até agora**: `maintenance.work_order` só tem códigos coarse-grained (`.view`/`.create`/
`.edit`/`.cancel`/`.approve_cost`/`.reject_cost`/`.close`/`.view_cost`/`.comment`/`.attach`) — ao
contrário de `freight.trip` (Lote 4), que tem um código por transição (`.dispatch`/`.start`/
`.finish`), `maintenance` não tem nenhum código dedicado por transição. Cinco comandos de
`026-maintenance-orders.md` (`iniciar-diagnostico`/`concluir-diagnostico`/`aguardar-peca`/
`retomar-execucao`/`concluir`) e o `DELETE` reaproveitam `.edit`, todos documentados explicitamente
— aplicando o mesmo princípio de reaproveitar-e-registrar, autorizado pelo usuário para este lote
sem necessidade de `AskUserQuestion` por caso. Também encontrado: `maintenance.cost_approval` só
tem `.approve`/`.reject`, sem `.view` — reaproveitado `.view_cost`; e uma ambiguidade não resolvida
silenciosamente entre `work_order.approve_cost`/`.reject_cost` e `cost_approval.approve`/`.reject`
(dois códigos para a mesma ação conceitual) — usado `cost_approval.*` por mapear 1:1 ao recurso
Aprovação modelado em `028-maintenance-approvals.md`, sobreposição registrada, não escondida.
No Lote 7 (7.18 `financial`), a auditoria encontrou a **primeira lacuna de seção inteira** desta
sprint: `Plano de Contas` e `Conta Bancária` — ambas tabelas físicas plenamente especificadas — não
tinham nenhum código, nem coarse-grained (diferente de toda lacuna anterior, que sempre tinha algo
na família a reaproveitar). Resolvido na origem, mesmo princípio de D222/D196 aplicado à matriz em
vez de à DDL (D271): `financial.chart_of_accounts.*` e `financial.bank_account.*` adicionados a
`RBAC_MATRIX.md` §7.18 antes de escrever `034`/`036`, seguindo a granularidade das linhas vizinhas.
`Estorno Financeiro` também não tinha código — `financial.reversal.view`/`.create` adicionados junto
(D271). Também descoberto: `Assinatura`/`Cobrança Recorrente`/`Plano` (D272) pertencem a
`subscription`/`billing` (§7.19), não a `financial` (§7.18) — leitura correta de bounded context
mesmo quando o agrupamento temático do lote sugeria o contrário.
No Lote 8 (7.17 `documents`), a mesma auditoria encontrou a **terceira lacuna de seção inteira**:
`Configuração Fiscal do Tenant` não tinha nenhum código — corrigido (D283) com granularidade
alinhada ao pedido explícito do usuário (`documents.fiscal_config.view`/`.edit`/
`.manage_certificate`/`.manage_series`/`.switch_environment`). O restante de `documents.cte`/
`.mdfe`/`.ciot` já era coarse-grained por natureza (`.issue` cobre toda a sequência RASCUNHO→
TRANSMITIDO de CT-e) — mesmo reaproveitamento já aplicado sem nova pergunta, agora por autorização
explícita do usuário desde o kickoff deste lote ("Não criar novas até consultar o RBAC... Se não
existir: corrigir RBAC antes da OpenAPI").
No Lote 9 (7.16 `tracking`), a auditoria pedida explicitamente pelo usuário (D200 aplicado antes de
escrever qualquer endpoint) encontrou a **maior lacuna em número de entidades afetadas**: `Provedor
de Rastreamento`, `Equipamento de Rastreamento`, `Telemetria` e `Heartbeat` — quatro das oito
entidades físicas do módulo — não tinham nenhum código; `Geofence` não tinha `.delete`;
`SpeedLimitConfig` não tinha `.create`. Corrigido (D293) com `tracking.provider.*`/
`.equipment.*`/`.telemetry.view`/`.heartbeat.view`/`.geofence.delete`/`.speed_limit_config.create`.
Também encontrado (D294): `eventos_rastreamento` é uma única tabela, mas a matriz já fragmentava
`.stop.view`/`.route_deviation.view`/`.speed_event.view` por categoria (`tipo`) antes deste lote,
sem cobrir `ENTROU_GEOFENCE`/`SAIU_GEOFENCE`/`IGNICAO_LIGADA`/`IGNICAO_DESLIGADA` — resolvido
reaproveitando `.geofence.view`/`.position.view` por categoria, primeira vez que autorização por
subconjunto de linhas (não só por campo, D267, ou por verbo, D240) aparece nesta API.
No Lote 10 (`mobile`/`freight`), a auditoria encontrou duas lacunas distintas (D304): (1)
`freight.trip.edit` — reaproveitado desde D240 (Lote 4) para `accept`/`interromper`/`retomar` do
Motorista — nunca tinha o marcador `●` (App) na coluna correspondente, apesar de já ser usado pelo
Perfil Motorista; corrigido, junto com a atualização da seção 13 (resumo do que o Motorista pode).
(2) `Sessão`/`Dispositivo`/`Fila de Sincronização` (D140) não tinham nenhum código — quinta
ocorrência do padrão "seção/código de RBAC inteiramente ausente". Corrigido com uma seção nova,
`7.27 mobile`, escopada estritamente a autoatendimento (`mobile.device.view_own`/`.edit_own`/
`mobile.sync.execute`) — nunca a dados de domínio, que continuam usando os códigos dos módulos
correspondentes (D303). Total de permissões: 311 → 314.
No Lote 11 (BI + IA), a auditoria pedida explicitamente pelo usuário encontrou a **maior lacuna da
sprint**: `analytics`/`reporting` e `ai` — dois bounded contexts inteiros, 15 entidades plenamente
especificadas (D151-D172) — não tinham nenhuma seção em `RBAC_MATRIX.md` além de códigos avulsos de
relatórios pré-construídos. Corrigido (D313): 28 códigos novos em `7.23 analytics`/`reporting`
(`analytics.metric.*`/`.indicator.view`/`.snapshot.*`/`.cube.*`, `reporting.dashboard.*`/
`.saved_filter.*`/`.saved_report.*`/`.export.*`/`.scheduled_update.*`) e 15 códigos novos numa seção
nova `7.28 ai` (`ai.model.*`/`.inference.view`/`.view_cost`/`.suggestion.view`/`.decide`/
`.prediction.view`/`.classification.view`/`.anomaly.view`/`.review`/`.computer_vision.view`/
`.confirm`/`.feedback.view`/`.create`). Total de permissões: 314 → **357**. Também confirmado:
`ai.inference.cost` é a **terceira ocorrência** de autorização por campo nesta API (após
`maintenance.work_order.view_cost`, Lote 6, e `financial.trip_*_value.view`, Lote 7); e
`ai.feedback.create` é reaproveitado para o `PATCH` de `actual_result` — sem `.edit` dedicado,
mesmo padrão de reaproveitamento de D240, aqui pela última vez neste segmento BI+IA.
No Lote 12 (Recursos Transversais), a auditoria (D200, ainda mais ampla por atravessar quase todos
os módulos) encontrou três lacunas na mesma preparação (D325): `storage` §7.22 só tinha
`.attachment.*` (Comentários, D186, nunca teve código; Storage/Files, D324, era uma entidade nova);
`notification_center` §7.24 tinha `.view`/`.configure`/`.channel_preference.edit` mas faltava
`.alert.manage_own`/`.channel_preference.view`; e `integration` — `Configuração de Integração`/
`Webhook`/`Execução de Job`, plenamente especificadas em Domain/DDL desde o Sprint 09, nunca
tiveram nenhuma seção RBAC (sétima ocorrência do padrão "seção inteira ausente", após D271/D283/
D293/D304/D313). Corrigido: 22 códigos novos (7 em `storage`, 2 em `notification_center`, 13 na
nova seção `7.29 integration`). Total de permissões: 357 → 379. Também confirmado: `084-reports.md`/
`085-exports.md` não precisaram de nenhum código novo — reconciliados com `reporting.*` (Lote 11,
D326); `082-global-search.md`/`083-timelines.md` também não — nenhum dos dois tem RBAC próprio por
design (D317/D328), sempre reaproveitando a permissão `.view` do recurso original.

## Esquemas de segurança (`openapi.yaml` `#/components/securitySchemes`)

```yaml
securitySchemes:
  bearerAuth:
    type: http
    scheme: bearer
    bearerFormat: JWT
    description: "AUTHENTICATION.md — Web (sessão) e Mobile (Access Token). Usado por todo
      endpoint deste lote, exceto login/forgot-password."
  apiKeyAuth:
    type: apiKey
    in: header
    name: X-Api-Key
    description: "AUTHENTICATION.md — API Pública/Interna (tokens_api). Não usado pelos endpoints
      deste lote (todos pensados para o ERP Web/App Motorista neste momento), declarado aqui para
      reuso quando a API Pública for implementada (OPENAPI_ARCHITECTURE.md seção 2)."
```

`security: - bearerAuth: []` no nível de operação declara **autenticação obrigatória** — mas nunca
substitui a checagem de RBAC (D212). A tabela abaixo é a segunda camada, obrigatória em todo
endpoint que não seja puramente "estou autenticado, quero meus próprios dados" (`GET /auth/me`).

## Mapeamento Endpoint → Permissão RBAC

| Endpoint | Método | Permissão exigida | Escopo (D053) |
|---|---|---|---|
| `/auth/login` | `POST` | Nenhuma (pré-autenticação) | — |
| `/auth/refresh` | `POST` | Nenhuma (token de refresh é a própria credencial) | — |
| `/auth/logout` | `POST` | Nenhuma (encerra a própria sessão) | Próprio usuário |
| `/auth/forgot-password` | `POST` | Nenhuma (pré-autenticação) | — |
| `/auth/reset-password` | `POST` | Nenhuma (token de reset é a própria credencial) | — |
| `/auth/me` | `GET` | Nenhuma além de autenticado | Próprio usuário |
| `/tenant` | `GET` | `tenancy.company_data.view` | Empresa inteira |
| `/tenant` | `PATCH` | `tenancy.company_data.edit` | Empresa inteira |
| `/users` | `GET` | `identity_access.user.view` | Empresa inteira |
| `/users/{id}` | `GET` | `identity_access.user.view` | Empresa inteira |
| `/users` | `POST` | `identity_access.user.create` | Empresa inteira |
| `/users/{id}` | `PATCH` | `identity_access.user.edit` | Empresa inteira |
| `/users/{id}` | `DELETE` | `identity_access.user.deactivate` | Empresa inteira |
| `/roles` | `GET` | `identity_access.role.view` | Empresa inteira |
| `/roles/{id}` | `GET` | `identity_access.role.view` | Empresa inteira |
| `/roles` | `POST` | `identity_access.role.create` | Empresa inteira |
| `/roles/{id}` | `PATCH` | `identity_access.role.edit` | Empresa inteira |
| `/roles/{id}` | `DELETE` | `identity_access.role.delete` | Empresa inteira |
| `/permissions` | `GET` | `identity_access.permission.view` | — (Platform Reference Data, D046) |
| `/permissions/{id}` | `GET` | `identity_access.permission.view` | — |
| `/branches` | `GET` | `tenancy.branch.view` | Empresa inteira |
| `/branches/{id}` | `GET` | `tenancy.branch.view` | Empresa inteira |
| `/branches` | `POST` | `tenancy.branch.create` | Empresa inteira |
| `/branches/{id}` | `PATCH` | `tenancy.branch.edit` | Empresa inteira |
| `/branches/{id}` | `DELETE` | `tenancy.branch.delete` | Empresa inteira |
| `/clients` | `GET` | `crm.client.view` | Empresa inteira |
| `/clients/{id}` | `GET` | `crm.client.view` | Empresa inteira |
| `/clients` | `POST` | `crm.client.create` | Empresa inteira |
| `/clients/{id}` | `PATCH` | `crm.client.edit` | Empresa inteira |
| `/clients/{id}` | `DELETE` | `crm.client.delete` | Empresa inteira |
| `/clients/{id}/addresses` (+ `/suppliers`, `/branches`) | `GET`/`POST` | Permissão de `.view`/`.edit` do **dono** (nunca uma permissão própria de Endereço, D216) | Empresa inteira |
| `/clients/{id}/addresses/{addressId}` (+ demais donos) | `GET`/`PATCH`/`DELETE` | Idem | Empresa inteira |
| `/clients/{id}/contacts` | `GET` | `crm.client_contact.view` | Empresa inteira |
| `/clients/{id}/contacts` | `POST` | `crm.client_contact.create` | Empresa inteira |
| `/clients/{id}/contacts/{contactId}` | `PATCH` | `crm.client_contact.edit` | Empresa inteira |
| `/clients/{id}/contacts/{contactId}` | `DELETE` | `crm.client_contact.delete` | Empresa inteira |
| `/suppliers` | `GET` | `maintenance.supplier.view` | Empresa inteira |
| `/suppliers/{id}` | `GET` | `maintenance.supplier.view` | Empresa inteira |
| `/suppliers` | `POST` | `maintenance.supplier.create` | Empresa inteira |
| `/suppliers/{id}` | `PATCH` | `maintenance.supplier.edit` | Empresa inteira |
| `/suppliers/{id}` | `DELETE` | `maintenance.supplier.delete` | Empresa inteira |
| `/drivers` | `GET` | `drivers.driver.view` | Empresa inteira |
| `/drivers/{id}` | `GET` | `drivers.driver.view` | Empresa inteira |
| `/drivers/me` | `GET` | `drivers.driver.view_own` | Próprio usuário |
| `/drivers` | `POST` | `drivers.driver.create` | Empresa inteira |
| `/drivers/{id}` | `PATCH` | `drivers.driver.edit` | Empresa inteira |
| `/drivers/{id}/block` | `POST` | `drivers.driver.block` | Empresa inteira |
| `/drivers/{id}/unblock` | `POST` | `drivers.driver.unblock` | Empresa inteira |
| `/drivers/{id}` | `DELETE` | `drivers.driver.delete` | Empresa inteira |
| `/drivers/{id}/documents` (CNH) | `GET`/`POST`/`PATCH` | `drivers.driver.view_cnh`/`.edit_cnh` | Empresa inteira |
| `/drivers/{id}/documents` (demais tipos) | `GET`/`POST`/`PATCH` | `drivers.driver.view`/`.edit` (sem código próprio, D216) | Empresa inteira |
| `/drivers/{id}/documents/{documentId}` | `DELETE` | `drivers.driver.edit` | Empresa inteira |
| `/employees` | `GET` | `identity_access.employee.view` | Empresa inteira |
| `/employees/{id}` | `GET` | `identity_access.employee.view` | Empresa inteira |
| `/employees` | `POST` | `identity_access.employee.create` | Empresa inteira |
| `/employees/{id}` | `PATCH` | `identity_access.employee.edit` | Empresa inteira |
| `/employees/{id}` | `DELETE` | `identity_access.employee.delete` | Empresa inteira |
| `/cost-centers` | `GET` | `financial.cost_center.view` | Empresa inteira |
| `/cost-centers/{id}` | `GET` | `financial.cost_center.view` | Empresa inteira |
| `/cost-centers` | `POST` | `financial.cost_center.create` | Empresa inteira |
| `/cost-centers/{id}` | `PATCH` | `financial.cost_center.edit` | Empresa inteira |
| `/cost-centers/{id}` | `DELETE` | **Não existe** — sem código RBAC (`financial.cost_center.delete` não existe em `RBAC_MATRIX.md`, D216); desativação via `PATCH status=INATIVO` | — |
| `/viagens` | `GET` | `freight.trip.view` / `.view_own` | Empresa inteira / Próprio usuário |
| `/viagens/{id}` | `GET` | `freight.trip.view` / `.view_own` | Empresa inteira / Próprio usuário |
| `/viagens` | `POST` | `freight.trip.create` | Empresa inteira |
| `/viagens/{id}` | `PATCH` | `freight.trip.edit` | Empresa inteira |
| `/viagens/{id}` | `DELETE` | `freight.trip.edit` (sem `.delete` dedicado — exclusão só em `RASCUNHO`/`PLANEJADA`) | Empresa inteira |
| `/viagens/{id}/commands/accept` | `POST` | `freight.trip.edit` (D240 — sem código dedicado) | Próprio usuário |
| `/viagens/{id}/commands/dispatch` | `POST` | `freight.trip.dispatch` | Empresa inteira |
| `/viagens/{id}/commands/start` | `POST` | `freight.trip.start` | Próprio usuário |
| `/viagens/{id}/commands/finish` | `POST` | `freight.trip.finish` | Próprio usuário |
| `/viagens/{id}/commands/interromper` | `POST` | `freight.trip.edit` (D240) | Empresa inteira |
| `/viagens/{id}/commands/retomar` | `POST` | `freight.trip.edit` (D240) | Empresa inteira |
| `/viagens/{id}/commands/cancelar` | `POST` | `freight.trip.cancel` | Empresa inteira |
| `/viagens/{id}/commands/close-administrative` | `POST` | `freight.trip.close` | Empresa inteira |
| `/viagens/{id}/commands/reallocate-resources` | `POST` | `freight.trip.reassign` | Empresa inteira |
| `/viagens/{id}/entregas` | `GET` | `freight.delivery.view` | Empresa inteira |
| `/viagens/{id}/entregas` | `POST` | `freight.delivery.create` | Empresa inteira |
| `/viagens/{id}/entregas/{entregaId}` | `GET`/`PATCH` | `freight.delivery.view` / `.edit` | Empresa inteira |
| `/viagens/{id}/entregas/{entregaId}/canhoto` | `POST` | `freight.pod.create` | Empresa inteira |
| `/viagens/{id}/resources` | `GET` | `freight.trip.view` | Empresa inteira |
| `/viagens/{id}/resources` | `POST` | `freight.trip.edit` | Empresa inteira |
| `/viagens/{id}/occurrences` | `GET` | `freight.occurrence.view` | Empresa inteira |
| `/viagens/{id}/occurrences` | `POST` | `freight.occurrence.create` | Empresa inteira |
| `/viagens/{id}/occurrences/{occurrenceId}` | `GET`/`PATCH` | `freight.occurrence.view` / `.edit` | Empresa inteira |
| `/viagens/{id}/timeline` | `GET` | `freight.trip.view` / `.view_own` | Empresa inteira / Próprio usuário |
| `/veiculos` | `GET` | `fleet.vehicle.view` / `.view_own` | Empresa inteira / Próprio usuário |
| `/veiculos/{id}` | `GET` | `fleet.vehicle.view` / `.view_own` | Empresa inteira / Próprio usuário |
| `/veiculos` | `POST` | `fleet.vehicle.create` | Empresa inteira |
| `/veiculos/{id}` | `PATCH` | `fleet.vehicle.edit` | Empresa inteira |
| `/veiculos/{id}` | `DELETE` | `fleet.vehicle.delete` | Empresa inteira |
| `/veiculos/{id}/technical-sheet` | `GET` | `fleet.vehicle_technical_sheet.view` | Empresa inteira |
| `/veiculos/{id}/technical-sheet` | `PATCH` | `fleet.vehicle_technical_sheet.edit` | Empresa inteira |
| `/veiculos/{id}/documentos` | `GET` | `fleet.vehicle_document.view` | Empresa inteira |
| `/veiculos/{id}/documentos` | `POST` | `fleet.vehicle_document.create` | Empresa inteira |
| `/veiculos/{id}/documentos/{documentoId}` | `PATCH` | `fleet.vehicle_document.attach` (sem `.edit` dedicado, D216/D240-precedente) | Empresa inteira |
| `/implementos` | `GET` | `fleet.implement.view` | Empresa inteira |
| `/implementos/{id}` | `GET` | `fleet.implement.view` | Empresa inteira |
| `/implementos` | `POST` | `fleet.implement.create` | Empresa inteira |
| `/implementos/{id}` | `PATCH` | `fleet.implement.edit` | Empresa inteira |
| `/implementos/{id}` | `DELETE` | `fleet.implement.delete` | Empresa inteira |
| `/vehicle-compositions` | `GET` | `fleet.vehicle_composition.view` | Empresa inteira |
| `/vehicle-compositions/{id}` | `GET` | `fleet.vehicle_composition.view` | Empresa inteira |
| `/vehicle-compositions` | `POST` | `fleet.vehicle_composition.create` | Empresa inteira |
| `/vehicle-compositions/{id}/commands/validate` | `POST` | `fleet.vehicle_composition.validate` | Empresa inteira |
| `/veiculos/{id}/odometro/leituras` | `GET` | `fleet.odometer_reading.view` | Empresa inteira |
| `/veiculos/{id}/odometro/leituras` | `POST` | `fleet.odometer_reading.create` (Escopo inclui Motorista via app) | Empresa inteira / Próprio usuário |
| `/veiculos/disponibilidade` | `GET` | `fleet.vehicle.view_availability` | Empresa inteira |
| `/veiculos/{id}/disponibilidade` | `GET` | `fleet.vehicle.view_availability` | Empresa inteira |
| `/ordens-servico` | `GET` | `maintenance.work_order.view` (+ `.view_cost` para campos de custo) | Empresa inteira |
| `/ordens-servico/{id}` | `GET` | `maintenance.work_order.view` (+ `.view_cost`) | Empresa inteira |
| `/ordens-servico` | `POST` | `maintenance.work_order.create` | Empresa inteira |
| `/ordens-servico/{id}` | `PATCH` | `maintenance.work_order.edit` | Empresa inteira |
| `/ordens-servico/{id}` | `DELETE` | `maintenance.work_order.edit` (sem `.delete` dedicado — exclusão só em `ABERTA`) | Empresa inteira |
| `/ordens-servico/{id}/commands/iniciar-diagnostico` | `POST` | `maintenance.work_order.edit` (sem código dedicado) | Empresa inteira |
| `/ordens-servico/{id}/commands/concluir-diagnostico` | `POST` | `maintenance.work_order.edit` (sem código dedicado) | Empresa inteira |
| `/ordens-servico/{id}/commands/aguardar-peca` | `POST` | `maintenance.work_order.edit` (sem código dedicado) | Empresa inteira |
| `/ordens-servico/{id}/commands/retomar-execucao` | `POST` | `maintenance.work_order.edit` (sem código dedicado) | Empresa inteira |
| `/ordens-servico/{id}/commands/concluir` | `POST` | `maintenance.work_order.edit` (sem código dedicado) | Empresa inteira |
| `/ordens-servico/{id}/commands/fechar` | `POST` | `maintenance.work_order.close` | Empresa inteira |
| `/ordens-servico/{id}/commands/cancelar` | `POST` | `maintenance.work_order.cancel` | Empresa inteira |
| `/ordens-servico/{id}/itens` | `GET` | `maintenance.work_order_item.view` | Empresa inteira |
| `/ordens-servico/{id}/itens` | `POST` | `maintenance.work_order_item.create` | Empresa inteira |
| `/ordens-servico/{id}/itens/{itemId}` | `PATCH` | `maintenance.work_order_item.edit` | Empresa inteira |
| `/ordens-servico/{id}/aprovacoes` | `GET` | `maintenance.work_order.view_cost` (sem `cost_approval.view` dedicado) | Empresa inteira |
| `/ordens-servico/{id}/aprovacoes/{aprovacaoId}` | `GET` | `maintenance.work_order.view_cost` | Empresa inteira |
| `/ordens-servico/{id}/aprovacoes/{aprovacaoId}/commands/approve` | `POST` | `maintenance.cost_approval.approve` | Empresa inteira |
| `/ordens-servico/{id}/aprovacoes/{aprovacaoId}/commands/reject` | `POST` | `maintenance.cost_approval.reject` | Empresa inteira |
| `/ordens-servico/{id}/historico-status` | `GET` | `maintenance.work_order.view` (sem código dedicado) | Empresa inteira |
| `/planos-manutencao` | `GET` | `maintenance.preventive_plan.view` | Empresa inteira |
| `/planos-manutencao/{id}` | `GET` | `maintenance.preventive_plan.view` | Empresa inteira |
| `/planos-manutencao` | `POST` | `maintenance.preventive_plan.create` | Empresa inteira |
| `/planos-manutencao/{id}` | `PATCH` | `maintenance.preventive_plan.edit` | Empresa inteira |
| `/tipos-servico` | `GET` | `maintenance.service_type.view` | Empresa inteira |
| `/tipos-servico/{id}` | `GET` | `maintenance.service_type.view` | Empresa inteira |
| `/tipos-servico` | `POST` | `maintenance.service_type.create` | Empresa inteira |
| `/tipos-servico/{id}` | `PATCH` | `maintenance.service_type.edit` | Empresa inteira |
| `/contas-pagar` | `GET` | `financial.payable.view` | Empresa inteira |
| `/contas-pagar/{id}` | `GET` | `financial.payable.view` | Empresa inteira |
| `/contas-pagar` | `POST` | `financial.payable.create` | Empresa inteira |
| `/contas-pagar/{id}` | `PATCH` | `financial.payable.edit` | Empresa inteira |
| `/contas-pagar/{id}` | `DELETE` | `financial.payable.edit` (sem `.delete` dedicado — exclusão só em `LANCADA`) | Empresa inteira |
| `/contas-pagar/{id}/commands/approve` | `POST` | `financial.payable.approve` | Empresa inteira |
| `/contas-pagar/{id}/commands/reject` | `POST` | `financial.payable.reject` | Empresa inteira |
| `/contas-pagar/{id}/commands/pay` | `POST` | `financial.payable.pay` | Empresa inteira |
| `/contas-pagar/{id}/aprovacoes` | `GET` | `financial.payable.view` | Empresa inteira |
| `/contas-pagar/{id}/rateios` | `GET` | `financial.cost_allocation.view` | Empresa inteira |
| `/faturas` | `GET` | `financial.invoice.view` | Empresa inteira |
| `/faturas/{id}` | `GET` | `financial.invoice.view` | Empresa inteira |
| `/faturas` | `POST` | `financial.invoice.create` | Empresa inteira |
| `/faturas/{id}/commands/cancel` | `POST` | `financial.invoice.cancel` | Empresa inteira |
| `/faturas/{id}/contas-receber` | `GET` | `financial.receivable.view` | Empresa inteira |
| `/faturas/{id}/contas-receber` | `POST` | `financial.receivable.create` | Empresa inteira |
| `/faturas/{id}/contas-receber/{parcelaId}` | `GET` | `financial.receivable.view` | Empresa inteira |
| `/faturas/{id}/contas-receber/{parcelaId}` | `PATCH` | `financial.receivable.edit` | Empresa inteira |
| `/faturas/{id}/contas-receber/{parcelaId}/commands/confirm-receipt` | `POST` | `financial.receivable.confirm_receipt` | Empresa inteira |
| `/plano-contas` | `GET` | `financial.chart_of_accounts.view` (D271) | Empresa inteira |
| `/plano-contas/{id}` | `GET` | `financial.chart_of_accounts.view` (D271) | Empresa inteira |
| `/plano-contas` | `POST` | `financial.chart_of_accounts.create` (D271) | Empresa inteira |
| `/plano-contas/{id}` | `PATCH` | `financial.chart_of_accounts.edit` (D271) | Empresa inteira |
| `/plano-contas/{id}` | `DELETE` | `financial.chart_of_accounts.delete` (D271) | Empresa inteira |
| `/contas-bancarias` | `GET` | `financial.bank_account.view` (D271) | Empresa inteira |
| `/contas-bancarias/{id}` | `GET` | `financial.bank_account.view` (D271) | Empresa inteira |
| `/contas-bancarias` | `POST` | `financial.bank_account.create` (D271) | Empresa inteira |
| `/contas-bancarias/{id}` | `PATCH` | `financial.bank_account.edit` (D271) | Empresa inteira |
| `/contas-bancarias/{id}` | `DELETE` | `financial.bank_account.delete` (D271) | Empresa inteira |
| `/contas-bancarias/{id}/extrato` | `GET` | `financial.bank_reconciliation.view` (sem código próprio de "ver extrato") | Empresa inteira |
| `/contas-bancarias/{id}/saldo` | `GET` | `financial.bank_account.view` | Empresa inteira |
| `/posicoes-caixa` | `GET` | `financial.cash_flow.view` | Empresa inteira |
| `/conciliacoes-bancarias` | `GET` | `financial.bank_reconciliation.view` | Empresa inteira |
| `/conciliacoes-bancarias/{id}` | `GET` | `financial.bank_reconciliation.view` | Empresa inteira |
| `/conciliacoes-bancarias` | `POST` | `financial.bank_reconciliation.create` | Empresa inteira |
| `/estornos-financeiros` | `GET` | `financial.reversal.view` (D271) | Empresa inteira |
| `/estornos-financeiros/{id}` | `GET` | `financial.reversal.view` (D271) | Empresa inteira |
| `/estornos-financeiros` | `POST` | `financial.reversal.create` (D271) | Empresa inteira |
| `/viagens/{id}/financeiro` | `GET` | `financial.trip_predicted_value.view` + `financial.trip_actual_value.view` + `financial.trip_margin.view` (autorização por campo, D267) | Empresa inteira |
| `/planos` | `GET` | `subscription.plan.view` (bounded context `subscription`, D272 — não `financial`) | Empresa inteira |
| `/planos/{id}` | `GET` | `subscription.plan.view` | Empresa inteira |
| `/assinatura` | `GET` | `subscription.subscription.view` | Próprio tenant |
| `/assinatura/commands/upgrade` | `POST` | `subscription.subscription.upgrade` | Próprio tenant |
| `/assinatura/commands/downgrade` | `POST` | `subscription.subscription.downgrade` | Próprio tenant |
| `/assinatura/commands/cancel` | `POST` | `subscription.subscription.cancel` (Aprovação: Administrador Empresa) | Próprio tenant |
| `/assinatura/commands/reactivate` | `POST` | `subscription.subscription.reactivate` | Próprio tenant |
| `/cobrancas-recorrentes` | `GET` | `billing.recurring_charge.view` (bounded context `billing`, D272) | Próprio tenant |
| `/cobrancas-recorrentes/{id}` | `GET` | `billing.recurring_charge.view` | Próprio tenant |
| `/cobrancas-recorrentes/{id}/commands/retry` | `POST` | `billing.recurring_charge.retry` | Próprio tenant |
| `/ctes` | `GET` | `documents.cte.view` | Empresa inteira |
| `/ctes/{id}` | `GET` | `documents.cte.view` | Empresa inteira |
| `/ctes/{id}/commands/validate` | `POST` | `documents.cte.issue` (sem código dedicado) | Empresa inteira |
| `/ctes/{id}/commands/sign` | `POST` | `documents.cte.issue` (sem código dedicado) | Empresa inteira |
| `/ctes/{id}/commands/transmit` | `POST` | `documents.cte.issue` (sem código dedicado) | Empresa inteira |
| `/ctes/{id}/commands/cancel` | `POST` | `documents.cte.cancel` (Aprovação: Diretor) | Empresa inteira |
| `/ctes/{id}/commands/inutilize` | `POST` | `documents.cte.issue` (sem código dedicado) | Empresa inteira |
| `/ctes/{id}/status-history` | `GET` | `documents.cte.view` (sem código dedicado) | Empresa inteira |
| `/ctes/{id}/xml` | `GET` | `documents.cte.view` | Empresa inteira |
| `/ctes/{id}/cartas-correcao` | `GET` | `documents.cte.correct` | Empresa inteira |
| `/ctes/{id}/cartas-correcao` | `POST` | `documents.cte.correct` | Empresa inteira |
| `/ctes/{id}/cartas-correcao/{cartaId}` | `GET` | `documents.cte.correct` | Empresa inteira |
| `/ctes/{id}/cartas-correcao/{cartaId}/xml` | `GET` | `documents.cte.correct` | Empresa inteira |
| `/ctes/{id}/nfe-referenciadas` | `GET` | `documents.nfe_reference.view` | Empresa inteira |
| `/ctes/{id}/nfe-referenciadas` | `POST` | `documents.cte.issue` (sem `.nfe_reference.create` dedicado) | Empresa inteira |
| `/ctes/{id}/nfe-referenciadas/{nfeId}` | `GET` | `documents.nfe_reference.view` | Empresa inteira |
| `/mdfes` | `GET` | `documents.mdfe.view` | Empresa inteira |
| `/mdfes/{id}` | `GET` | `documents.mdfe.view` | Empresa inteira |
| `/mdfes` | `POST` | `documents.mdfe.issue` | Empresa inteira |
| `/mdfes/{id}/commands/close` | `POST` | `documents.mdfe.close` | Empresa inteira |
| `/mdfes/{id}/commands/cancel` | `POST` | `documents.mdfe.cancel` (Aprovação: Diretor) | Empresa inteira |
| `/mdfes/{id}/status-history` | `GET` | `documents.mdfe.view` (sem código dedicado) | Empresa inteira |
| `/mdfes/{id}/xml` | `GET` | `documents.mdfe.view` | Empresa inteira |
| `/ciots` | `GET` | `documents.ciot.view` | Empresa inteira |
| `/ciots/{id}` | `GET` | `documents.ciot.view` | Empresa inteira |
| `/ciots` | `POST` | `documents.ciot.register` (sem `.create` dedicado) | Empresa inteira |
| `/ciots/{id}/commands/register` | `POST` | `documents.ciot.register` | Empresa inteira |
| `/ciots/{id}/commands/cancel` | `POST` | `documents.ciot.cancel` | Empresa inteira |
| `/ciots/{id}/status-history` | `GET` | `documents.ciot.view` (sem código dedicado) | Empresa inteira |
| `/fiscal/events` | `GET` | `documents.sefaz_status.view` (sem código dedicado a "eventos fiscais") | Empresa inteira |
| `/fiscal/events/{id}` | `GET` | `documents.sefaz_status.view` | Empresa inteira |
| `/configuracao-fiscal` | `GET` | `documents.fiscal_config.view` (D283) | Empresa inteira |
| `/configuracao-fiscal` | `PATCH` | `documents.fiscal_config.edit`/`.manage_certificate`/`.manage_series`/`.switch_environment` (por grupo de campo, D283/D267-style) | Empresa inteira |
| `/tracking/providers` | `GET` | `tracking.provider.view` (D293) | Empresa inteira |
| `/tracking/providers/{id}` | `GET` | `tracking.provider.view` (D293) | Empresa inteira |
| `/tracking/providers` | `POST` | `tracking.provider.create` (D293) | Empresa inteira |
| `/tracking/providers/{id}` | `PATCH` | `tracking.provider.edit` (D293) | Empresa inteira |
| `/tracking/equipment` | `GET` | `tracking.equipment.view` (D293) | Empresa inteira |
| `/tracking/equipment/{id}` | `GET` | `tracking.equipment.view` (D293) | Empresa inteira |
| `/tracking/equipment` | `POST` | `tracking.equipment.create` (D293) | Empresa inteira |
| `/tracking/equipment/{id}` | `PATCH` | `tracking.equipment.edit` (D293) | Empresa inteira |
| `/tracking/equipment/{id}/heartbeats` | `GET` | `tracking.heartbeat.view` (D293) | Empresa inteira |
| `/vehicles/{vehicleId}/tracking/positions` | `GET` | `tracking.position.view` | Empresa inteira |
| `/tracking/origins` | `GET` | `tracking.position.view` (sem código próprio) | Empresa inteira |
| `/vehicles/{vehicleId}/tracking/telemetry` | `GET` | `tracking.telemetry.view` (D293) | Empresa inteira |
| `/tracking/events` | `GET` | `tracking.stop.view` / `.route_deviation.view` / `.speed_event.view` / `.geofence.view` / `.position.view` (por categoria, D294) | Empresa inteira |
| `/tracking/events/{id}` | `GET` | Idem, conforme `type` do registro (D294) | Empresa inteira |
| `/tracking/geofences` | `GET` | `tracking.geofence.view` | Empresa inteira |
| `/tracking/geofences/{id}` | `GET` | `tracking.geofence.view` | Empresa inteira |
| `/tracking/geofences` | `POST` | `tracking.geofence.create` | Empresa inteira |
| `/tracking/geofences/{id}` | `PATCH` | `tracking.geofence.edit` | Empresa inteira |
| `/tracking/geofences/{id}` | `DELETE` | `tracking.geofence.delete` (D293) | Empresa inteira |
| `/tracking/speed-limit-configs` | `GET` | `tracking.speed_limit_config.view` | Empresa inteira |
| `/tracking/speed-limit-configs` | `POST` | `tracking.speed_limit_config.create` (D293) | Empresa inteira |
| `/tracking/speed-limit-configs/{id}` | `PATCH` | `tracking.speed_limit_config.edit` | Empresa inteira |
| `/vehicles/{vehicleId}/tracking/history` | `GET` | `tracking.position.view` (base) + filtragem por linha conforme `.telemetry.view`/categoria de evento (D290/D294) | Empresa inteira |
| `/mobile/auth/login` | `POST` | Nenhuma (pré-autenticação) | — |
| `/mobile/auth/refresh` | `POST` | Nenhuma (token de refresh é a própria credencial) | — |
| `/mobile/auth/logout` | `POST` | Nenhuma (encerra a própria sessão) | Próprio motorista |
| `/mobile/auth/me` | `GET` | Nenhuma além de autenticado | Próprio motorista |
| `/mobile/trips` | `GET` | `freight.trip.view_own` | Próprio motorista |
| `/mobile/trips/{id}` | `GET` | `freight.trip.view_own` | Próprio motorista |
| `/mobile/trips/{id}/commands/accept` | `POST` | `freight.trip.edit` (D240/D304 — App ● desde esta preparação) | Próprio motorista |
| `/mobile/trips/{id}/commands/start` | `POST` | `freight.trip.start` | Próprio motorista |
| `/mobile/trips/{id}/commands/interromper` | `POST` | `freight.trip.edit` (D240/D304) | Próprio motorista |
| `/mobile/trips/{id}/commands/retomar` | `POST` | `freight.trip.edit` (D240/D304) | Próprio motorista |
| `/mobile/trips/{id}/commands/finish` | `POST` | `freight.trip.finish` | Próprio motorista |
| `/mobile/trips/{id}/occurrences` | `GET` | `freight.occurrence.view` | Próprio motorista |
| `/mobile/trips/{id}/occurrences` | `POST` | `freight.occurrence.create` | Próprio motorista |
| `/mobile/trips/{id}/deliveries` | `GET` | `freight.delivery.view` | Próprio motorista |
| `/mobile/trips/{id}/deliveries/{deliveryId}` | `GET` | `freight.delivery.view` | Próprio motorista |
| `/mobile/trips/{id}/deliveries/{deliveryId}/pod` | `POST` | `freight.pod.create` + `freight.pod.attach` | Próprio motorista |
| `/mobile/signatures` | `GET` | `freight.delivery.view` (sem `freight.pod.view` dedicado) | Próprio motorista |
| `/mobile/signatures/{id}` | `GET` | `freight.delivery.view` | Próprio motorista |
| `/mobile/sync` | `POST` | `mobile.sync.execute` (D304) | Próprio motorista |
| `/mobile/sync/records` | `GET` | `mobile.sync.execute` (D304) | Próprio motorista |
| `/mobile/devices` | `GET` | `mobile.device.view_own` (D304) | Próprio motorista |
| `/mobile/devices/{id}` | `GET` | `mobile.device.view_own` (D304) | Próprio motorista |
| `/mobile/devices/{id}` | `PATCH` | `mobile.device.edit_own` (D304) | Próprio motorista |
| `/analytics/metrics` | `GET` | `analytics.metric.view` (D313) | Empresa inteira |
| `/analytics/metrics/{id}` | `GET` | `analytics.metric.view` (D313) | Empresa inteira |
| `/analytics/metrics` | `POST` | `analytics.metric.create` (D313) | Empresa inteira |
| `/analytics/metrics/{id}` | `PATCH` | `analytics.metric.edit` (D313) | Empresa inteira |
| `/analytics/indicators` | `GET` | `analytics.indicator.view` (D313) | Empresa inteira |
| `/analytics/indicators/{id}` | `GET` | `analytics.indicator.view` (D313) | Empresa inteira |
| `/analytics/snapshots` | `GET` | `analytics.snapshot.view` (D313) | Empresa inteira |
| `/analytics/snapshots` | `POST` | `analytics.snapshot.create` (D313) | Empresa inteira |
| `/analytics/snapshots/{id}` | `GET` | `analytics.snapshot.view` (D313) | Empresa inteira |
| `/analytics/cubes` | `GET` | `analytics.cube.view` (D313) | Empresa inteira |
| `/analytics/cubes` | `POST` | `analytics.cube.create` (D313) | Empresa inteira |
| `/analytics/cubes/{id}` | `GET` | `analytics.cube.view` (D313) | Empresa inteira |
| `/analytics/cubes/{id}` | `PATCH` | `analytics.cube.edit` (D313) | Empresa inteira |
| `/reporting/dashboards` | `GET` | `reporting.dashboard.view_own` + `.view_shared` (D313) | Próprio usuário / Compartilhado |
| `/reporting/dashboards` | `POST` | `reporting.dashboard.create` (D313) | Próprio usuário |
| `/reporting/dashboards/{id}` | `GET` | `reporting.dashboard.view_own` / `.view_shared` (D313) | Próprio usuário / Compartilhado |
| `/reporting/dashboards/{id}` | `PATCH` | `reporting.dashboard.edit_own` (D313) | Próprio usuário |
| `/reporting/dashboards/{id}` | `DELETE` | `reporting.dashboard.delete_own` (D313) | Próprio usuário |
| `/reporting/dashboards/{id}/commands/share` | `POST` | `reporting.dashboard.share` (D313) | Próprio usuário |
| `/reporting/saved-filters` | `GET` | `reporting.saved_filter.view_own` (D313) | Próprio usuário |
| `/reporting/saved-filters` | `POST` | `reporting.saved_filter.create` (D313) | Próprio usuário |
| `/reporting/saved-filters/{id}` | `GET` | `reporting.saved_filter.view_own` (D313) | Próprio usuário |
| `/reporting/saved-filters/{id}` | `PATCH` | `reporting.saved_filter.edit_own` (D313) | Próprio usuário |
| `/reporting/saved-filters/{id}` | `DELETE` | `reporting.saved_filter.delete_own` (D313) | Próprio usuário |
| `/reporting/saved-reports` | `GET` | `reporting.saved_report.view_own` (D313) | Próprio usuário |
| `/reporting/saved-reports` | `POST` | `reporting.saved_report.create` (D313) | Próprio usuário |
| `/reporting/saved-reports/{id}` | `GET` | `reporting.saved_report.view_own` (D313) | Próprio usuário |
| `/reporting/saved-reports/{id}` | `PATCH` | `reporting.saved_report.edit_own` (D313) | Próprio usuário |
| `/reporting/saved-reports/{id}` | `DELETE` | `reporting.saved_report.delete_own` (D313) | Próprio usuário |
| `/reporting/exports` | `GET` | `reporting.export.view_own` (D313) | Próprio usuário |
| `/reporting/exports` | `POST` | `reporting.export.create` (D313) | Próprio usuário |
| `/reporting/exports/{id}` | `GET` | `reporting.export.view_own` (D313) | Próprio usuário |
| `/reporting/scheduled-updates` | `GET` | `reporting.scheduled_update.view` (D313) | Empresa inteira |
| `/reporting/scheduled-updates` | `POST` | `reporting.scheduled_update.create` (D313) | Empresa inteira |
| `/reporting/scheduled-updates/{id}` | `GET` | `reporting.scheduled_update.view` (D313) | Empresa inteira |
| `/reporting/scheduled-updates/{id}` | `PATCH` | `reporting.scheduled_update.edit` (D313) | Empresa inteira |
| `/ai/models` | `GET` | `ai.model.view` (D313) | Empresa inteira |
| `/ai/models` | `POST` | `ai.model.create` (D313) | Empresa inteira |
| `/ai/models/{id}` | `GET` | `ai.model.view` (D313) | Empresa inteira |
| `/ai/models/{id}` | `PATCH` | `ai.model.edit` (D313) | Empresa inteira |
| `/ai/inferences` | `GET` | `ai.inference.view` (+ `.view_cost` para `cost`, D313) | Empresa inteira |
| `/ai/inferences/{id}` | `GET` | `ai.inference.view` (+ `.view_cost`) | Empresa inteira |
| `/ai/suggestions` | `GET` | `ai.suggestion.view` (D313) | Empresa inteira |
| `/ai/suggestions/{id}` | `GET` | `ai.suggestion.view` (D313) | Empresa inteira |
| `/ai/suggestions/{id}/commands/accept` | `POST` | `ai.suggestion.decide` (D313) | Empresa inteira |
| `/ai/suggestions/{id}/commands/reject` | `POST` | `ai.suggestion.decide` (D313) | Empresa inteira |
| `/ai/suggestions/{id}/commands/ignore` | `POST` | `ai.suggestion.decide` (D313) | Empresa inteira |
| `/ai/predictions` | `GET` | `ai.prediction.view` (D313) | Empresa inteira |
| `/ai/predictions/{id}` | `GET` | `ai.prediction.view` (D313) | Empresa inteira |
| `/ai/classifications` | `GET` | `ai.classification.view` (D313) | Empresa inteira |
| `/ai/classifications/{id}` | `GET` | `ai.classification.view` (D313) | Empresa inteira |
| `/ai/anomalies` | `GET` | `ai.anomaly.view` (D313) | Empresa inteira |
| `/ai/anomalies/{id}` | `GET` | `ai.anomaly.view` (D313) | Empresa inteira |
| `/ai/anomalies/{id}/commands/review` | `POST` | `ai.anomaly.review` (D313) | Empresa inteira |
| `/ai/computer-vision/readings` | `GET` | `ai.computer_vision.view` (D313) | Empresa inteira |
| `/ai/computer-vision/readings/{id}` | `GET` | `ai.computer_vision.view` (D313) | Empresa inteira |
| `/ai/computer-vision/readings/{id}/commands/confirm` | `POST` | `ai.computer_vision.confirm` (D313) | Empresa inteira |
| `/ai/computer-vision/readings/{id}/commands/reject` | `POST` | `ai.computer_vision.confirm` (D313) | Empresa inteira |
| `/ai/feedback` | `GET` | `ai.feedback.view` (D313) | Empresa inteira |
| `/ai/feedback` | `POST` | `ai.feedback.create` (App ●, D313) | Empresa inteira / Próprio motorista |
| `/ai/feedback/{id}` | `GET` | `ai.feedback.view` (D313) | Empresa inteira |
| `/ai/feedback/{id}` | `PATCH` | `ai.feedback.create` (sem `.edit` dedicado, D313) | Empresa inteira / Próprio motorista |
| `/storage/uploads` | `POST` | `storage.file.upload` (D325) | Empresa inteira / Próprio motorista |
| `/storage/uploads/{id}/commands/complete` | `POST` | `storage.file.upload` (D325) | Empresa inteira / Próprio motorista |
| `/storage/files/{id}/download-url` | `GET` | `storage.file.view` (D325) | Empresa inteira |
| `/storage/files/{id}` | `DELETE` | `storage.file.delete` (D325) | Empresa inteira |
| `/storage/files` | `GET` | `storage.file.view` (D325) | Empresa inteira |
| `/storage/files/{id}` | `GET` | `storage.file.view` (D325) | Empresa inteira |
| `/storage/files/{id}/versions` | `GET` | `storage.file.view` (D325) | Empresa inteira |
| `/viagens/{id}/attachments` | `GET` | `freight.trip.view`/`.view_own` + `storage.attachment.view` | Empresa inteira / Próprio usuário |
| `/viagens/{id}/attachments` | `POST` | `freight.trip.edit` + `storage.attachment.create` (App ●) | Empresa inteira / Próprio motorista |
| `/viagens/{id}/attachments/{attachmentId}` | `DELETE` | `freight.trip.edit` + `storage.attachment.delete` | Empresa inteira |
| `/viagens/{id}/comments` | `GET` | `freight.trip.view`/`.view_own` + `storage.comment.view` (App ●) | Empresa inteira / Próprio usuário |
| `/viagens/{id}/comments` | `POST` | `freight.trip.view`/`.view_own` + `storage.comment.create` (App ●) | Empresa inteira / Próprio motorista |
| `/viagens/{id}/comments/{commentId}` | `PATCH` | `storage.comment.edit_own` | Próprio autor |
| `/viagens/{id}/comments/{commentId}` | `DELETE` | `storage.comment.delete_own` | Próprio autor |
| `/search` | `GET` | Nenhuma própria — filtrado por `.view` de cada tipo de resultado (D317) | Empresa inteira / Próprio usuário |
| `/notifications` | `GET` | `notification_center.alert.view` (App ●) | Próprio usuário |
| `/notifications/{id}` | `GET` | `notification_center.alert.view` (App ●) | Próprio usuário |
| `/notifications/{id}/commands/mark-read` | `POST` | `notification_center.alert.manage_own` (D325, App ●) | Próprio usuário |
| `/notifications/channel-preferences` | `GET` | `notification_center.channel_preference.view` (D325, App ●) | Próprio usuário |
| `/notifications/channel-preferences/{channel}` | `PATCH` | `notification_center.channel_preference.edit` (App ●) | Próprio usuário |
| `/integrations` | `GET` | `integration.config.view` (D325) | Empresa inteira |
| `/integrations` | `POST` | `integration.config.create` (D325) | Empresa inteira |
| `/integrations/{id}` | `GET` | `integration.config.view` (D325) | Empresa inteira |
| `/integrations/{id}` | `PATCH` | `integration.config.edit` (D325) | Empresa inteira |
| `/integrations/{id}/commands/enable` | `POST` | `integration.config.enable` (D325) | Empresa inteira |
| `/integrations/{id}/commands/disable` | `POST` | `integration.config.disable` (D325) | Empresa inteira |
| `/integrations/webhooks` | `GET` | `integration.webhook.view` (D325) | Empresa inteira |
| `/integrations/webhooks` | `POST` | `integration.webhook.create` (D325) | Empresa inteira |
| `/integrations/webhooks/{id}` | `GET` | `integration.webhook.view` (D325) | Empresa inteira |
| `/integrations/webhooks/{id}` | `PATCH` | `integration.webhook.edit` (D325) | Empresa inteira |
| `/integrations/webhooks/{id}/commands/activate` | `POST` | `integration.webhook.activate` (D325) | Empresa inteira |
| `/integrations/webhooks/{id}/commands/suspend` | `POST` | `integration.webhook.suspend` (D325) | Empresa inteira |
| `/integrations/webhooks/{id}/commands/test` | `POST` | `integration.webhook.test` (D325) | Empresa inteira |
| `/jobs` | `GET` | `integration.job.view` (D325) | Empresa inteira |
| `/jobs/{id}` | `GET` | `integration.job.view` (D325) | Empresa inteira |
| `/jobs/commands/trigger` | `POST` | `integration.job.trigger` (D322/D325, Aprovação: Administrador Empresa) | Empresa inteira |

## Notas de RBAC específicas deste lote

- **`identity_access.user.deactivate` vs. `identity_access.user.block`**: `DELETE /users/{id}`
  (soft delete, D219) usa `.deactivate` — bloqueio (`.block`, suspensão por segurança, distinta de
  desativação de cadastro) é uma ação diferente, não modelada como endpoint neste lote (fica para
  quando `bloqueios_acesso` ganhar sua própria rota, fora do escopo de "Usuários" básico).
- **`identity_access.permission.grant`/`.revoke`/`.deny`** existem em `RBAC_MATRIX.md` mas não têm
  endpoint neste lote — alterar quais Permissões um Papel tem acontece via `PATCH /roles/{id}`
  (campo `permissions`), não por uma rota própria de concessão/revogação individual. Se o produto
  precisar de auditoria mais fina por concessão individual, isso é decisão de um lote futuro, não
  inventada agora.
- **Nenhum endpoint altera Permissão diretamente em Usuário** — reforça o que o usuário já pediu
  explicitamente: permissão é sempre via Papel (`papel_permissao`), nunca uma atribuição individual
  a um Usuário específico (não existe tabela para isso no Modelo Relacional, e não seria criada
  aqui — D101/D103).
- **`/permissions` é somente leitura** para clientes normais — `POST`/`PATCH`/`DELETE` de Permissão
  pertence à administração da própria plataforma GestorFrete (`RBAC_MATRIX.md` seção 7.26), fora da
  superfície do produto, fora deste lote.
- **`fleet.vehicle_document.attach` reutilizado para `PATCH`** (Lote 5): `RBAC_MATRIX.md` 7.8 só tem
  `.view`/`.create`/`.attach` para documento de veículo, sem `.edit` — mesma lacuna de granularidade
  já vista em D240, resolvida pelo mesmo precedente (reaproveitar o código mais próximo), sem nova
  pergunta ao usuário por ser estruturalmente idêntica.
- **Composição/Hodômetro/Disponibilidade não têm `.edit`/`.delete`** (Lote 5, por design): confirmado
  em `RBAC_MATRIX.md` 7.8 que `fleet.vehicle_composition` só tem `.view`/`.create`/`.validate`
  (D248 — nunca editado in-place), `fleet.odometer_reading` só tem `.view`/`.create` (D246 —
  imutável), e Disponibilidade não tem nenhum código de escrita, só `.view_availability` (D247 —
  Read Model). Em nenhum dos três casos a ausência é uma lacuna a resolver — é o desenho pretendido.
- **`maintenance.work_order.edit` cobre seis operações distintas** (Lote 6): `RBAC_MATRIX.md` 7.9 é
  coarse-grained para transições de OS — ao contrário de `freight.trip` (Lote 4, um código por
  transição), não há `.iniciar_diagnostico`/`.concluir_diagnostico`/`.aguardar_peca`/
  `.retomar_execucao`/`.concluir`/`.delete` dedicados. Os cinco comandos de transição e o `DELETE`
  reaproveitam `.edit`, cada um documentado individualmente em `components/security.md` e em
  `026-maintenance-orders.md` — maior concentração de reaproveitamento num único lote até agora,
  registrada explicitamente como candidata a refinamento de granularidade futuro, não corrigida
  aqui (corrigir exigiria alterar `RBAC_MATRIX.md`, fora do escopo de um lote de API).
- **`maintenance.cost_approval` sem `.view`** (Lote 6): só `.approve`/`.reject` existem —
  reaproveitado `maintenance.work_order.view_cost` para `GET /aprovacoes` (Aprovações são
  informação de custo, mesma natureza de `.view_cost`).
- **Ambiguidade `work_order.approve_cost`/`.reject_cost` vs. `cost_approval.approve`/`.reject`**
  (Lote 6): a matriz tem dois pares de código plausíveis para a mesma decisão de aprovação de
  custo — não resolvida silenciosamente escolhendo um; usado `cost_approval.*` por mapear
  diretamente ao recurso Aprovação (`028-maintenance-approvals.md`), sobreposição registrada como
  imprecisão de granularidade da matriz a refinar, não como lacuna de código ausente.
- **`maintenance.preventive_plan`/`service_type` sem `.delete`** (Lote 6, mesmo padrão de
  `financial.cost_center` no Lote 3): desativação via `PATCH status=INATIVO`, sem reaproveitar
  `.edit` para simular exclusão — só cabe reaproveitar quando não existe campo de status
  equivalente (caso de Ordem de Serviço, que não tem "status inativo" antes de `EM_DIAGNOSTICO`).
- **`financial.chart_of_accounts.*`/`financial.bank_account.*`/`financial.reversal.*` criados
  nesta preparação** (Lote 7, D271): primeira vez que uma seção inteira estava ausente da matriz
  para uma entidade plenamente especificada em Domain/Dictionary/DDL — resolvido na origem antes de
  `034`/`036`/`037` dependerem dela, mesmo princípio de D222/D196 aplicado a `RBAC_MATRIX.md`.
- **`financial.payable`/`financial.invoice`/`financial.receivable` já eram fine-grained** (Lote 7):
  ao contrário de `maintenance.work_order` (Lote 6), a seção `financial` já tinha um código por
  transição de negócio (`.approve`/`.reject`/`.pay`/`.confirm_receipt`) — nenhum reaproveitamento
  de `.edit` foi necessário para os comandos de estado, só para `DELETE /contas-pagar/{id}` (sem
  `.delete` dedicado, mesmo precedente de sempre).
- **`financial.trip_predicted_value.view`/`.trip_actual_value.view`/`.trip_margin.view`** (Lote 7):
  três permissões controlando três grupos de campos da mesma resposta (`038-financial-trip.md`) —
  segunda ocorrência de autorização por campo nesta API (primeira foi `maintenance.work_order.
  view_cost`, Lote 6), aqui ainda mais granular (três níveis, não dois).
- **`Assinatura`/`Cobrança Recorrente`/`Plano` usam `subscription`/`billing`, não `financial`**
  (Lote 7, D272): confirmado por leitura completa de `RBAC_MATRIX.md` §7.19 — o agrupamento
  temático do pedido do usuário ("Financeiro") não determina o bounded context real; `035-
  recurring-billing.md` usa os códigos corretos apesar do número de arquivo sugerir o contrário.
- **`documents.fiscal_config.*` criado nesta preparação** (Lote 8, D283): terceira lacuna de seção
  inteira desta sprint (após `financial.chart_of_accounts`/`.bank_account`, D271) — resolvida na
  origem antes de `045-configuracao-fiscal.md` depender dela, com granularidade fina por ação
  (view/edit/certificate/series/environment) alinhada ao pedido explícito do usuário.
- **`documents.cte.issue` cobre toda a sequência RASCUNHO→TRANSMITIDO+inutilize** (Lote 8): mesmo
  padrão de `maintenance.work_order.edit` (Lote 6) — a matriz trata "Emitir CT-e" como uma única
  responsabilidade do Faturista (`009-FISCAL.md` seção Permissões), não um código por sub-passo.
  `commands/validate`/`.sign`/`.transmit`/`.inutilize` reaproveitam `.issue`; só `commands/cancel`
  tem código próprio (`.cancel`, já existente, criticidade Alta/Diretor).
- **`documents.nfe_reference` sem `.create`**: só `.view` existe — `POST /ctes/{id}/nfe-
  referenciadas` reaproveita `documents.cte.issue` (compor o CT-e inclui suas referências de NF-e).
- **`documents.ciot` sem `.create`**: `.register` cobre criação+registro como uma responsabilidade
  única — ciclo de CIOT é simples o bastante para não separar os dois códigos.
- **`documents.sefaz_status.view` reaproveitado para `/fiscal/events`**: não existe um código
  dedicado a "eventos fiscais" — `.sefaz_status.view` é o mais próximo semanticamente (visualizar
  resultado técnico da comunicação com a SEFAZ).
- **Sem autorização por campo em `documents.cte`/`.mdfe`/`.ciot`** (diferente de `financial`, Lote
  7): verificado explicitamente por pedido do usuário ("verificar RBAC antes de assumir
  `view_value`/`view_xml`/`view_tax`") — `RBAC_MATRIX.md` §7.17 não tem nenhuma dessas variantes;
  `.view` gates o recurso inteiro, incluindo `service_value`/`xml_file_id`. Confirmação negativa
  registrada, nenhum código de campo inventado.
- **`tracking.provider`/`.equipment`/`.telemetry`/`.heartbeat` criados nesta preparação** (Lote 9,
  D293): quatro entidades inteiras sem RBAC de uma vez — maior lacuna em número de entidades desta
  sprint. `tracking.geofence.delete` e `tracking.speed_limit_config.create` também estavam
  faltando isoladamente (padrão "código único ausente", diferente das quatro seções inteiras).
- **`tracking.stop`/`.route_deviation`/`.speed_event`/`.geofence`/`.position` fragmentam uma única
  tabela por categoria** (Lote 9, D294): `eventos_rastreamento.tipo` tem 7 valores, a matriz só
  cobria 3 antes desta preparação — `ENTROU_GEOFENCE`/`SAIU_GEOFENCE` reaproveitam `.geofence.view`,
  `IGNICAO_LIGADA`/`IGNICAO_DESLIGADA` reaproveitam `.position.view`. Primeira vez que a autorização
  filtra por **subconjunto de linhas** de uma mesma tabela em vez de por campo (D267, Lote 7) ou por
  verbo/comando (D240, Lote 4) — `051-tracking-events.md` documenta o mapeamento completo.
- **Tensão registrada, não escondida**: `tracking.position.create_manual` existe na matriz e o
  domínio (`flows/008-RASTREAMENTO.md`) descreve entrada manual de posição como funcionalidade
  real — mas por instrução explícita deste lote ("Somente leitura. Nunca POST/PATCH/DELETE"),
  `048-vehicle-positions.md` não implementa esse endpoint. RBAC/domínio não foram silenciosamente
  ignorados nem contrariados: a lacuna fica documentada, reservada para quando o contrato de
  ingestão for definido.
- **`freight.trip.edit` ganha o marcador App (●)** (Lote 10, D304): já era usado pelo Motorista
  desde D240 (Lote 4) para `accept`/`interromper`/`retomar`, mas a matriz nunca refletiu isso na
  coluna App nem no resumo da seção 13 — corrigido nesta preparação, primeira vez que um marcador
  retroativo (não um código novo) foi a lacuna encontrada.
- **`mobile.device`/`mobile.sync` — primeira seção RBAC própria de `mobile`** (Lote 10, D304): antes
  desta preparação, `mobile` não tinha nenhum código — todas as ações de domínio do Motorista já
  reaproveitavam `freight`/`drivers`/`maintenance`/`financial` (correto, D303). A infraestrutura do
  próprio App (Sessão/Dispositivo/Fila de Sincronização, D140) nunca teve representação — resolvida
  com uma seção nova, deliberadamente restrita a autoatendimento (`_own`), nunca a dados de domínio.
- **`freight.pod.view` não existe**: `/mobile/signatures` reaproveita `freight.delivery.view` (o
  Canhoto/Assinatura é sempre consultado no contexto de uma Entrega) — mesmo padrão de sub-recurso
  já usado em outros lotes, não uma lacuna a corrigir.
- **`freight.delivery.edit`/`.occurrence.edit` não são App (●)**: confirmado por leitura da matriz
  — edição de Entrega/Ocorrência é responsabilidade do Gestor Operacional, não exposta em
  `057`/`058` para o Motorista, mesmo tendo os códigos `.view`/`.create` App-acessíveis.
- **`analytics`/`reporting`/`ai` criados nesta preparação** (Lote 11, D313): maior lacuna de RBAC da
  sprint em número de códigos — dois bounded contexts inteiros (15 entidades) sem representação,
  43 códigos novos ao todo (28 + 15). Resolvido na origem, mesmo princípio de D222/D196/D271/D283/
  D293/D304 aplicado à matriz antes de qualquer um dos 16 arquivos deste lote ser escrito.
- **`ConsolidatedIndicator`/`AnalyticalSnapshot`/`AISuggestion`/`AIPrediction`/`AIClassification`/
  `AIAnomaly`/`ComputerVisionReading` são todos somente leitura ou quase-somente-leitura** (Lote 11):
  a matriz confirma que nenhuma dessas entidades tem `.create`/`.edit`/`.delete` de escrita direta —
  todas nascem de processamento interno (`analytics`/`ai`) ou de comandos de decisão específicos
  (`.decide`/`.review`/`.confirm`), nunca de um `POST`/`PATCH` genérico do cliente.
- **`ai.inference.view_cost` — terceira ocorrência de autorização por campo** (Lote 11): mesmo
  padrão de `maintenance.work_order.view_cost` (Lote 6) e `financial.trip_*_value.view` (Lote 7);
  sem essa permissão, `cost` retorna `null`, nunca omitido silenciosamente do schema.
- **`ai.feedback.create` reaproveitado para o `PATCH` de `actual_result`** (Lote 11): sem `.edit`
  dedicado em `RBAC_MATRIX.md` — mesmo padrão de reaproveitamento de D240, documentado em
  `077-ai-feedback.md`, última ocorrência deste padrão neste segmento BI+IA.
- **`EVENT_MAP.md` não tem nenhum evento de IA** (Lote 11): confirmado por leitura completa —
  diferente da família de gaps D239/D259/.../D284/D294 (um fluxo canônico nomeia um evento ausente),
  aqui nenhum fluxo jamais nomeou um evento de IA, porque não existe `flows/0NN-IA.md` dedicado. Não
  inventado — registrado como lacuna de produto a considerar quando/se um fluxo de IA for
  formalizado.
- **Anexo/Comentário ganham RBAC próprio, ao contrário de Endereço** (Lote 12): `011-addresses.md`
  (Lote 3, D225) estabeleceu que Endereço **não** tem permissão própria — reaproveita `.view`/`.edit`
  do dono. Anexo/Comentário são diferentes: `storage.attachment.*`/`.comment.*` já existiam (Anexo)
  ou foram criados agora (Comentário, D325) como códigos **próprios**, verificados **em conjunto**
  com a permissão de visualização do dono (duas camadas: "o dono existe e é visível" + "posso
  anexar/comentar"), nunca reaproveitados diretamente do dono como Endereço fez. A diferença reflete
  o RBAC real: a matriz já tratava Anexo como recurso com RBAC próprio desde antes deste lote.
- **`storage.comment.create` não exige `freight.trip.edit`** (Lote 12): comentar uma Viagem exige
  apenas poder *visualizá-la* (`freight.trip.view`/`.view_own`) — comunicação não é alteração de
  dado operacional, diferente de Anexo (que exige `.edit` do dono, por representar evidência que
  passa a compor o registro).
- **`Comment`/`Attachment` não têm soft delete próprio** (Lote 12): `comentarios`/`anexos` (D186)
  nunca ganharam `excluido_em`/`excluido_por` — `DELETE` remove o vínculo fisicamente (não é uma
  exceção a D219, é uma tabela desenhada como puramente Histórica desde o Lote 4).
- **`082-global-search.md`/`083-timelines.md` não têm RBAC próprio, por design** (Lote 12, D317/
  D328): busca filtra por tipo usando a permissão `.view` de cada recurso original; Timeline reusa
  a permissão do Aggregate Root dono (ex.: `freight.trip.view` para `019-trip-timeline.md`). Nenhum
  código novo foi criado para nenhum dos dois — confirmado, não uma omissão.
- **`084-reports.md`/`085-exports.md` não têm RBAC próprio** (Lote 12, D326): reconciliados com
  `reporting.saved_report.*`/`.export.*` (Lote 11) — mesma entidade física, nenhum código
  duplicado.
- **`integration.job.trigger` é a permissão mais restrita criada neste lote** (Lote 12, D322):
  única com Aprovação (Administrador Empresa) em toda a seção `7.29 integration` — pedido explícito
  do usuário para impedir que um usuário comum dispare qualquer job arbitrário.

## Como este documento cresce

Todo endpoint novo (Lote 3 em diante) adiciona uma linha à tabela de mapeamento antes de ser
implementado — nunca um endpoint sem uma linha correspondente aqui. Se a Permissão necessária ainda
não existir em `RBAC_MATRIX.md`, o processo é o mesmo de D101 aplicado ao domínio: a Permissão
nasce lá primeiro, registrada como decisão, só depois o endpoint a referencia.
