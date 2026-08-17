# RBAC_MATRIX.md — Matriz de Permissões

Fonte oficial de autorização do GestorFrete. Toda tela, API e integração usa exatamente esta
matriz (D060/D061) — nunca uma regra de acesso paralela.

## 1. Objetivo

Definir como usuários acessam funcionalidades do sistema, respeitando Multi-Tenant, Filiais,
Perfis, Escopos, Permissões, Auditoria e LGPD.

## 2. Arquitetura de autorização

```
Usuário
   │
   ▼
Perfil
   │
   ▼
Permissões
   │
   ▼
Escopo
   │
   ▼
Ações
```

Um Usuário tem um ou mais Perfis; cada Perfil concede um conjunto de Permissões; cada Permissão,
quando exercida, é delimitada por um Escopo (D053); o resultado final é o conjunto de Ações que o
usuário pode executar, sobre quais dados. Permissões Adicionais e Permissões Negadas (D052/D054)
se aplicam diretamente ao Usuário, por cima do que o Perfil concede — ver
[`../domain/README.md`](../domain/README.md) para como isso se relaciona ao modelo de domínio.

## 3. Tipos de usuários

### Usuários da Transportadora

Administrador Empresa, Diretor, Gerente Operacional, Supervisor de Frota, Coordenador Logístico,
Analista Logístico, Financeiro, Fiscal, Comercial, Manutenção, Mecânico, Motorista, Auditor.

### Equipe GestorFrete

Administrador SaaS, Implantação, Suporte, Consultor Comercial, Auditor Interno.

**Reconciliação com [`PERSONAS.md`](./PERSONAS.md)**, atualizada nesta revisão: a maioria destes
perfis já corresponde a uma persona documentada (Diretor→persona 1, Gerente Operacional→persona 2
"Gestor Operacional" — mesmo nome oficial, "Gerente" não deve virar sinônimo em uso, ver
[`../domain/UBIQUITOUS_LANGUAGE.md`](../domain/UBIQUITOUS_LANGUAGE.md); Mecânico→persona 4;
Financeiro→persona 6; Comercial→persona 8; Motorista→persona 9; Administrador SaaS→persona 15;
Implantação→persona 13; Suporte→persona 14; Consultor Comercial→persona 12). Um esclarecimento
novo desta revisão: **Auditor Interno** não é a mesma coisa que a persona 11 (**Auditor**) — Auditor
(persona 11) é o auditor *da própria transportadora*, escopado ao seu tenant; Auditor Interno é um
papel *da equipe GestorFrete*, com acesso cross-tenant para fins de compliance da plataforma (ver
seção 14). Continuam sem persona própria ainda: Administrador Empresa, Supervisor de Frota,
Coordenador Logístico, Analista Logístico, Fiscal (perfil) — mesma recomendação da revisão
anterior: estender `PERSONAS.md` quando esta etapa acabar, não durante ela. **Almoxarife** (persona
5) segue sem perfil de RBAC correspondente — gap ainda em aberto.

## 4. Estrutura da permissão

Toda permissão tem:

| Campo | Descrição |
|---|---|
| Código | Identificador técnico único, formato `bounded_context.entidade.acao`, em inglês (D058) |
| Nome | Nome em português, mostrado a quem configura RBAC |
| Descrição | O que a permissão autoriza, em uma frase |
| Módulo | Área funcional (ver [`PRODUCT_MAP.md`](./PRODUCT_MAP.md)) |
| Bounded Context | Dono técnico único (D059, D033) |
| Escopo | Quais dos escopos da seção 6 se aplicam a esta permissão |
| Criticidade | Baixa / Média / Alta / Crítica |
| Auditável | Sempre "Sim" — toda permissão é auditável (D007/D055), não é um campo variável |
| Requer Aprovação | Não, ou o(s) perfil(is) aprovador(es) (D062) |
| Disponível via API | Sempre "Sim" — nenhuma permissão é exclusiva de um canal (D061); a distinção real é se já existe um endpoint de **API Pública** externa para ela, o que hoje não existe para nenhuma (ver seção 12) |
| Disponível no App | Sim, apenas para as permissões relevantes ao Motorista em campo (ver seção 13) |

Por serem repetitivos e universais, "Auditável" e "Disponível via API" não são repetidos linha a
linha na matriz da seção 7 — valem "Sim" para todas, por definição (D007/D055/D061). As colunas que
realmente diferenciam uma permissão de outra (Código, Nome, Criticidade, Aprovação, App) são as que
aparecem na matriz.

Exemplos oficiais: `freight.trip.create`, `fleet.vehicle.edit`, `maintenance.work_order.approve`.

## 5. Tipos de ações

Vocabulário padrão (nem toda ação se aplica a toda entidade — só as que fazem sentido):

Visualizar, Criar, Editar, Excluir (sempre soft delete, D001), Cancelar, Aprovar, Reprovar,
Exportar Excel, Exportar PDF, Importar, Emitir Documento, Reemitir, Anexar Arquivos, Comentar,
Visualizar Valores, Alterar Valores, Liberar, Bloquear, Encerrar, Reabrir (ver nota abaixo),
Duplicar, Compartilhar.

**Nota sobre "Reabrir"**: por D016 (transições inválidas normativas já registradas nos fluxos),
entidades com estado terminal (Viagem `FINALIZADA`/`ENCERRADA`, OS `FECHADA`, Checklist
`APROVADO`/`REPROVADO`) **nunca são reabertas** — a ação "Reabrir" existe no vocabulário geral, mas
não é uma permissão válida para nenhuma dessas entidades especificamente; correção pós-encerramento
sempre gera um novo registro, nunca reabre o antigo.

## 6. Escopos (D053)

Empresa, Filial, Unidade, Centro de Custo, Frota, Departamento, Motorista, Veículo, Próprio
Usuário — ver definições em
[`../information-model/001-DATA_OWNERSHIP.md`](../information-model/001-DATA_OWNERSHIP.md) e
[`../information-model/README.md`](../information-model/README.md) (D047, três níveis de posse:
estes escopos operam dentro do Nível 2/3 — nunca sobre Platform Reference Data, que não tem
tenant, D046).

## 7. Matriz de módulos

Cobertura desta versão: todas as entidades já documentadas em [`../domain/`](../domain/)
(`001-cadastros.md` a `005-pneus.md`) e todos os 10 fluxos de [`../flows/`](../flows/) — **311
permissões**. Crescimento incremental, mesmo princípio de `ENTITY_CATALOG.md`/
`HIGH_VOLUME_ENTITIES.md`: os módulos ainda não detalhados em `docs/domain/006-financeiro.md` a
`012-ia.md` (CRM completo, Marketplace, Telemetria, IA, BI avançado, Suporte detalhado) entram
quando esses arquivos existirem — é assim que a matriz chega às 500+ permissões mencionadas como
expectativa, não de uma vez.

Colunas: Código · Nome · Criticidade · Requer Aprovação · App Motorista (`●` quando aplicável).

### 7.1 `crm` — Cliente

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| crm.client.view | Visualizar cliente | Baixa | — | |
| crm.client.create | Criar cliente | Baixa | — | |
| crm.client.edit | Editar cliente | Baixa | — | |
| crm.client.delete | Excluir cliente | Média | Gerente Operacional | |
| crm.client.export | Exportar clientes | Baixa | — | |
| crm.client.comment | Comentar cliente | Baixa | — | |
| crm.client_contact.view | Visualizar contato do cliente | Baixa | — | |
| crm.client_contact.create | Criar contato do cliente | Baixa | — | |
| crm.client_contact.edit | Editar contato do cliente | Baixa | — | |
| crm.client_contact.delete | Excluir contato do cliente | Baixa | — | |

### 7.2 `maintenance` — Fornecedor

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| maintenance.supplier.view | Visualizar fornecedor | Baixa | — | |
| maintenance.supplier.create | Criar fornecedor | Baixa | — | |
| maintenance.supplier.edit | Editar fornecedor | Baixa | — | |
| maintenance.supplier.delete | Excluir fornecedor | Média | Financeiro | |
| maintenance.supplier.export | Exportar fornecedores | Baixa | — | |
| maintenance.supplier.comment | Comentar fornecedor | Baixa | — | |

### 7.3 `drivers` — Motorista

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| drivers.driver.view | Visualizar motorista | Baixa | — | |
| drivers.driver.view_own | Visualizar o próprio cadastro | Baixa | — | ● |
| drivers.driver.create | Criar motorista | Baixa | — | |
| drivers.driver.edit | Editar motorista | Baixa | — | |
| drivers.driver.delete | Excluir motorista | Alta | Diretor | |
| drivers.driver.block | Bloquear motorista | Alta | Gerente Operacional | |
| drivers.driver.unblock | Desbloquear motorista | Alta | Gerente Operacional | |
| drivers.driver.export | Exportar motoristas | Baixa | — | |
| drivers.driver.comment | Comentar motorista | Baixa | — | |
| drivers.driver.attach | Anexar arquivo (CNH digitalizada) | Média | — | |
| drivers.driver.view_performance | Visualizar Meu Desempenho | Baixa | — | ● |
| drivers.driver.view_cnh | Visualizar dados da CNH | Média | — | |
| drivers.driver.edit_cnh | Editar dados da CNH | Média | — | |

### 7.4 `identity_access` — Usuário, Papel, Permissão, Funcionário

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| identity_access.user.view | Visualizar usuário | Baixa | — | |
| identity_access.user.create | Criar usuário | Média | — | |
| identity_access.user.edit | Editar usuário | Média | — | |
| identity_access.user.deactivate | Desativar usuário | Alta | Administrador Empresa | |
| identity_access.user.block | Bloquear usuário | Alta | Administrador Empresa | |
| identity_access.user.reset_password | Redefinir senha de usuário | Alta | — | |
| identity_access.role.view | Visualizar perfil (papel) | Baixa | — | |
| identity_access.role.create | Criar perfil | Crítica | Administrador Empresa | |
| identity_access.role.edit | Editar perfil | Crítica | Administrador Empresa | |
| identity_access.role.delete | Excluir perfil | Crítica | Administrador Empresa | |
| identity_access.permission.view | Visualizar catálogo de permissões | Baixa | — | |
| identity_access.permission.grant | Conceder permissão adicional | Crítica | Administrador Empresa | |
| identity_access.permission.revoke | Revogar permissão | Crítica | Administrador Empresa | |
| identity_access.permission.deny | Registrar permissão negada | Crítica | Administrador Empresa | |
| identity_access.employee.view | Visualizar funcionário | Baixa | — | |
| identity_access.employee.create | Criar funcionário | Baixa | — | |
| identity_access.employee.edit | Editar funcionário | Baixa | — | |
| identity_access.employee.delete | Excluir funcionário | Média | — | |

### 7.5 `tenancy` — Filial, Empresa

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| tenancy.branch.view | Visualizar filial | Baixa | — | |
| tenancy.branch.create | Criar filial | Alta | Diretor | |
| tenancy.branch.edit | Editar filial | Média | — | |
| tenancy.branch.delete | Excluir filial | Alta | Diretor | |
| tenancy.company_data.view | Visualizar dados da empresa | Baixa | — | |
| tenancy.company_data.edit | Editar dados da empresa | Alta | Administrador Empresa | |
| tenancy.timezone_locale.view | Visualizar timezone/localidade | Baixa | — | |
| tenancy.timezone_locale.edit | Editar timezone/localidade | Média | — | |
| tenancy.visual_identity.edit | Editar identidade visual do tenant | Baixa | — | |

### 7.6 `pricing` — Tabela de Preço

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| pricing.price_table.view | Visualizar tabela de preço | Baixa | — | |
| pricing.price_table.create | Criar tabela de preço | Média | — | |
| pricing.price_table.edit | Editar tabela de preço | Média | — | |
| pricing.price_table.publish | Publicar tabela de preço (tornar vigente) | Alta | Gerente Operacional | |
| pricing.price_table.deactivate | Desativar tabela de preço | Média | — | |
| pricing.price_table.export | Exportar tabela de preço | Baixa | — | |
| pricing.price_table_item.view | Visualizar item de tabela | Baixa | — | |
| pricing.price_table_item.create | Criar item de tabela | Baixa | — | |
| pricing.price_table_item.edit | Editar item de tabela | Baixa | — | |
| pricing.price_table_item.delete | Excluir item de tabela | Baixa | — | |

### 7.7 `routing` — Rota Padrão, Trecho, Praça de Pedágio

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| routing.standard_route.view | Visualizar rota padrão | Baixa | — | |
| routing.standard_route.create | Criar rota padrão | Baixa | — | |
| routing.standard_route.edit | Editar rota padrão | Baixa | — | |
| routing.standard_route.delete | Excluir rota padrão | Baixa | — | |
| routing.route_segment.view | Visualizar trecho de rota | Baixa | — | |
| routing.route_segment.create | Criar trecho de rota | Baixa | — | |
| routing.route_segment.edit | Editar trecho de rota | Baixa | — | |
| routing.toll_plaza.view | Visualizar praça de pedágio | Baixa | — | |
| routing.toll_plaza.create | Criar praça de pedágio | Baixa | — | |
| routing.toll_plaza.edit | Editar praça de pedágio | Baixa | — | |

### 7.8 `fleet` — Veículo, Implemento, Composição, Documentos, Seguro, Hodômetro, Licenciamento, Categoria

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| fleet.vehicle.view | Visualizar veículo | Baixa | — | |
| fleet.vehicle.view_own | Visualizar veículo da própria viagem | Baixa | — | ● |
| fleet.vehicle.create | Criar veículo | Média | — | |
| fleet.vehicle.edit | Editar veículo | Média | — | |
| fleet.vehicle.delete | Excluir veículo | Alta | Diretor | |
| fleet.vehicle.export | Exportar veículos | Baixa | — | |
| fleet.vehicle.comment | Comentar veículo | Baixa | — | |
| fleet.vehicle.view_availability | Visualizar disponibilidade do veículo | Baixa | — | |
| fleet.implement.view | Visualizar implemento | Baixa | — | |
| fleet.implement.create | Criar implemento | Média | — | |
| fleet.implement.edit | Editar implemento | Média | — | |
| fleet.implement.delete | Excluir implemento | Alta | Diretor | |
| fleet.vehicle_composition.view | Visualizar composição veicular | Baixa | — | |
| fleet.vehicle_composition.create | Criar composição veicular | Média | — | |
| fleet.vehicle_composition.validate | Validar composição veicular (CONTRAN) | Média | — | |
| fleet.vehicle_technical_sheet.view | Visualizar ficha técnica | Baixa | — | |
| fleet.vehicle_technical_sheet.edit | Editar ficha técnica | Média | — | |
| fleet.vehicle_document.view | Visualizar documento do veículo | Baixa | — | |
| fleet.vehicle_document.create | Criar documento do veículo | Baixa | — | |
| fleet.vehicle_document.attach | Anexar documento do veículo | Baixa | — | |
| fleet.insurance_policy.view | Visualizar apólice de seguro | Baixa | — | |
| fleet.insurance_policy.create | Criar apólice de seguro | Média | — | |
| fleet.insurance_policy.edit | Editar apólice de seguro | Média | — | |
| fleet.odometer_reading.view | Visualizar leitura de hodômetro | Baixa | — | |
| fleet.odometer_reading.create | Registrar leitura de hodômetro | Baixa | — | ● |
| fleet.vehicle_licensing.view | Visualizar licenciamento | Baixa | — | |
| fleet.vehicle_licensing.create | Registrar licenciamento | Baixa | — | |
| fleet.vehicle_licensing.edit | Editar licenciamento | Baixa | — | |
| fleet.vehicle_category.view | Visualizar categoria de veículo | Baixa | — | |
| fleet.vehicle_category.create | Criar categoria de veículo | Baixa | — | |
| fleet.vehicle_category.edit | Editar categoria de veículo | Baixa | — | |

### 7.9 `maintenance` — Ordem de Serviço, Item, Peça, Estoque, Plano Preventivo, Tipo de Serviço, Aprovação de Custo

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| maintenance.work_order.view | Visualizar ordem de serviço | Baixa | — | |
| maintenance.work_order.create | Criar ordem de serviço | Baixa | — | |
| maintenance.work_order.edit | Editar ordem de serviço | Baixa | — | |
| maintenance.work_order.cancel | Cancelar ordem de serviço | Média | Supervisor de Frota | |
| maintenance.work_order.approve_cost | Aprovar custo de OS acima da alçada | Alta | Supervisor de Frota / Financeiro | |
| maintenance.work_order.reject_cost | Reprovar custo de OS | Alta | Supervisor de Frota / Financeiro | |
| maintenance.work_order.close | Fechar ordem de serviço | Média | — | |
| maintenance.work_order.view_cost | Visualizar custo da OS | Média | — | |
| maintenance.work_order.comment | Comentar ordem de serviço | Baixa | — | |
| maintenance.work_order.attach | Anexar arquivo à OS | Baixa | — | |
| maintenance.work_order_item.view | Visualizar item de OS | Baixa | — | |
| maintenance.work_order_item.create | Criar item de OS | Baixa | — | |
| maintenance.work_order_item.edit | Editar item de OS | Baixa | — | |
| maintenance.part_request.view | Visualizar solicitação de peça | Baixa | — | |
| maintenance.part_request.create | Criar solicitação de peça | Baixa | — | |
| maintenance.part_request.edit | Editar solicitação de peça | Baixa | — | |
| maintenance.part_request.cancel | Cancelar solicitação de peça | Baixa | — | |
| maintenance.part_stock.view | Visualizar peça em estoque | Baixa | — | |
| maintenance.part_stock.create | Criar peça em estoque | Baixa | — | |
| maintenance.part_stock.edit | Editar peça em estoque | Baixa | — | |
| maintenance.stock_movement.view | Visualizar movimentação de estoque | Baixa | — | |
| maintenance.stock_movement.create | Registrar movimentação de estoque | Baixa | — | |
| maintenance.preventive_plan.view | Visualizar plano de manutenção preventiva | Baixa | — | |
| maintenance.preventive_plan.create | Criar plano de manutenção preventiva | Média | — | |
| maintenance.preventive_plan.edit | Editar plano de manutenção preventiva | Média | — | |
| maintenance.service_type.view | Visualizar tipo de serviço | Baixa | — | |
| maintenance.service_type.create | Criar tipo de serviço | Baixa | — | |
| maintenance.service_type.edit | Editar tipo de serviço | Baixa | — | |
| maintenance.cost_approval.approve | Aprovar (registro formal) | Alta | — | |
| maintenance.cost_approval.reject | Reprovar (registro formal) | Alta | — | |

### 7.10 `maintenance` — Pneu, Recapagem, Posicionamento, Modelo, Política

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| maintenance.tire.view | Visualizar pneu | Baixa | — | |
| maintenance.tire.create | Criar pneu | Baixa | — | |
| maintenance.tire.edit | Editar pneu | Baixa | — | |
| maintenance.tire.scrap | Sucatear pneu | Média | Analista de Frota | |
| maintenance.tire.export | Exportar pneus | Baixa | — | |
| maintenance.tire.view_history | Visualizar histórico do pneu | Baixa | — | |
| maintenance.retreading.view | Visualizar registro de recapagem | Baixa | — | |
| maintenance.retreading.create | Registrar recapagem | Baixa | — | |
| maintenance.tire_positioning.view | Visualizar posicionamento de pneu | Baixa | — | |
| maintenance.tire_positioning.create | Registrar posicionamento de pneu | Baixa | — | |
| maintenance.tire_model.view | Visualizar modelo de pneu | Baixa | — | |
| maintenance.tire_model.create | Criar modelo de pneu | Baixa | — | |
| maintenance.tire_model.edit | Editar modelo de pneu | Baixa | — | |
| maintenance.retreading_policy.view | Visualizar política de recapagem | Baixa | — | |
| maintenance.retreading_policy.edit | Editar política de recapagem | Alta | Diretor | |

### 7.11 `maintenance` — Checklist

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| maintenance.checklist.view | Visualizar checklist | Baixa | — | |
| maintenance.checklist.fill | Preencher checklist | Baixa | — | ● |
| maintenance.checklist.approve | Aprovar checklist | Média | — | |
| maintenance.checklist.reject | Reprovar checklist | Média | — | |
| maintenance.checklist.attach | Anexar foto ao checklist | Baixa | — | ● |
| maintenance.checklist.view_history | Visualizar histórico de checklists | Baixa | — | |

### 7.12 `freight` — Viagem

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| freight.trip.view | Visualizar viagem | Baixa | — | |
| freight.trip.view_own | Visualizar as próprias viagens | Baixa | — | ● |
| freight.trip.create | Criar viagem | Baixa | — | |
| freight.trip.edit | Editar viagem | Baixa | — | ● |
| freight.trip.dispatch | Despachar viagem | Média | — | |
| freight.trip.cancel | Cancelar viagem | Alta | Supervisor / Gerente Operacional | |
| freight.trip.reassign | Reatribuir motorista/veículo | Média | Gerente Operacional | |
| freight.trip.close | Encerrar viagem | Média | — | |
| freight.trip.duplicate | Duplicar viagem | Baixa | — | |
| freight.trip.share | Compartilhar viagem | Baixa | — | |
| freight.trip.view_cost | Visualizar custo da viagem | Alta | — | |
| freight.trip.edit_cost | Alterar valor do frete | Crítica | Financeiro + Coordenador Logístico | |
| freight.trip.export | Exportar viagens | Baixa | — | |
| freight.trip.comment | Comentar viagem | Baixa | — | |
| freight.trip.attach | Anexar arquivo à viagem | Baixa | — | |
| freight.trip.start | Iniciar viagem | Baixa | — | ● |
| freight.trip.finish | Finalizar viagem | Baixa | — | ● |
| freight.trip.view_route | Visualizar rota da viagem | Baixa | — | ● |
| freight.trip.view_documents | Visualizar documentos da viagem | Baixa | — | ● |

### 7.13 `freight` — Entrega, Coleta, Ocorrência, Romaneio, Canhoto

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| freight.delivery.view | Visualizar entrega | Baixa | — | |
| freight.delivery.create | Registrar entrega | Baixa | — | ● |
| freight.delivery.edit | Editar entrega | Baixa | — | |
| freight.pickup.view | Visualizar coleta | Baixa | — | |
| freight.pickup.create | Registrar coleta | Baixa | — | ● |
| freight.occurrence.view | Visualizar ocorrência | Baixa | — | |
| freight.occurrence.create | Registrar ocorrência | Baixa | — | ● |
| freight.occurrence.edit | Editar ocorrência | Baixa | — | |
| freight.packing_list.view | Visualizar romaneio | Baixa | — | |
| freight.packing_list.create | Criar romaneio | Baixa | — | |
| freight.packing_list.edit | Editar romaneio | Baixa | — | |
| freight.pod.view | Visualizar canhoto | Baixa | — | |
| freight.pod.create | Registrar canhoto | Baixa | — | ● |
| freight.pod.attach | Anexar foto/assinatura do canhoto | Baixa | — | ● |

### 7.14 `freight` — Cotação, Contrato de Frete, Solicitação de Frete

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| freight.quote.view | Visualizar cotação | Baixa | — | |
| freight.quote.create | Criar cotação | Baixa | — | |
| freight.quote.edit | Editar cotação | Baixa | — | |
| freight.quote.approve | Aprovar cotação | Média | — | |
| freight.quote.reject | Reprovar cotação | Média | — | |
| freight.quote.export | Exportar cotação | Baixa | — | |
| freight.freight_contract.view | Visualizar contrato de frete | Baixa | — | |
| freight.freight_contract.create | Criar contrato de frete | Média | — | |
| freight.freight_contract.edit | Editar contrato de frete | Média | — | |
| freight.freight_contract.close | Encerrar contrato de frete | Média | — | |
| freight.freight_request.view | Visualizar solicitação de frete | Baixa | — | |
| freight.freight_request.create | Criar solicitação de frete | Baixa | — | |
| freight.freight_request.discard | Descartar solicitação de frete | Baixa | — | |

### 7.15 `freight` — Abastecimento

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| freight.fuel_supply.view | Visualizar abastecimento | Baixa | — | |
| freight.fuel_supply.request | Solicitar abastecimento | Baixa | — | ● |
| freight.fuel_supply.authorize | Autorizar abastecimento | Média | — | |
| freight.fuel_supply.deny | Negar abastecimento | Média | — | |
| freight.fuel_supply.register | Registrar abastecimento (cupom/hodômetro/litros) | Baixa | — | ● |
| freight.fuel_supply.validate | Validar abastecimento | Média | — | |
| freight.fuel_supply.investigate | Investigar abastecimento suspeito | Alta | — | |
| freight.fuel_supply.reject | Rejeitar abastecimento (fraude/erro) | Alta | — | |

### 7.16 `tracking` — Posição, Telemetria, Heartbeat, Provedor, Equipamento, Geofence, Parada, Desvio, Velocidade

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| tracking.position.view | Visualizar posição de veículo | Baixa | — | |
| tracking.position.create_manual | Registrar posição manual | Média | Gestor Operacional | |
| tracking.telemetry.view | Visualizar leitura de telemetria | Baixa | — | |
| tracking.heartbeat.view | Visualizar heartbeat de equipamento | Baixa | — | |
| tracking.provider.view | Visualizar provedor de rastreamento | Baixa | — | |
| tracking.provider.create | Criar provedor de rastreamento | Média | — | |
| tracking.provider.edit | Editar provedor de rastreamento | Média | — | |
| tracking.equipment.view | Visualizar equipamento de rastreamento | Baixa | — | |
| tracking.equipment.create | Criar equipamento de rastreamento | Média | — | |
| tracking.equipment.edit | Editar equipamento de rastreamento | Média | — | |
| tracking.geofence.view | Visualizar geofence | Baixa | — | |
| tracking.geofence.create | Criar geofence | Baixa | — | |
| tracking.geofence.edit | Editar geofence | Baixa | — | |
| tracking.geofence.delete | Excluir geofence | Baixa | — | |
| tracking.stop.view | Visualizar paradas | Baixa | — | |
| tracking.route_deviation.view | Visualizar desvios de rota | Baixa | — | |
| tracking.speed_event.view | Visualizar eventos de velocidade | Baixa | — | |
| tracking.speed_limit_config.view | Visualizar configuração de limite de velocidade | Baixa | — | |
| tracking.speed_limit_config.create | Criar configuração de limite de velocidade | Média | — | |
| tracking.speed_limit_config.edit | Editar configuração de limite de velocidade | Média | — | |

### 7.17 `documents` — CT-e, MDF-e, CIOT, Carta de Correção, Configuração Fiscal

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| documents.cte.view | Visualizar CT-e | Baixa | — | |
| documents.cte.issue | Emitir CT-e | Média | — | |
| documents.cte.cancel | Cancelar CT-e | Alta | Diretor | |
| documents.cte.correct | Emitir carta de correção | Média | — | |
| documents.cte.export | Exportar CT-e | Baixa | — | |
| documents.mdfe.view | Visualizar MDF-e | Baixa | — | |
| documents.mdfe.issue | Emitir MDF-e | Média | — | |
| documents.mdfe.close | Encerrar MDF-e | Média | — | |
| documents.mdfe.cancel | Cancelar MDF-e | Alta | Diretor | |
| documents.ciot.view | Visualizar CIOT | Baixa | — | |
| documents.ciot.register | Registrar CIOT | Média | — | |
| documents.ciot.cancel | Cancelar CIOT | Média | — | |
| documents.sefaz_status.view | Visualizar status na SEFAZ | Baixa | — | |
| documents.nfe_reference.view | Visualizar NF-e referenciada | Baixa | — | |
| documents.document_type.view | Visualizar tipo de documento fiscal | Baixa | — | |
| documents.fiscal_config.view | Visualizar configuração fiscal do tenant | Baixa | — | |
| documents.fiscal_config.edit | Configurar dados fiscais gerais (regime tributário) | Alta | Diretor | |
| documents.fiscal_config.manage_certificate | Alterar certificado digital | Alta | Diretor | |
| documents.fiscal_config.manage_series | Alterar série de numeração de CT-e/MDF-e | Alta | Diretor | |
| documents.fiscal_config.switch_environment | Alternar ambiente homologação/produção | Alta | Diretor | |

### 7.18 `financial` — Fatura, Contas, Adiantamento, Haver, Centro de Custo, Plano de Contas, Conta Bancária, Estorno, Conciliação, Fluxo de Caixa, DRE, Valores da Viagem

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| financial.invoice.view | Visualizar fatura | Média | — | |
| financial.invoice.create | Gerar fatura | Média | — | |
| financial.invoice.cancel | Cancelar fatura | Alta | Financeiro | |
| financial.receivable.view | Visualizar conta a receber | Média | — | |
| financial.receivable.create | Criar conta a receber | Média | — | |
| financial.receivable.edit | Editar conta a receber | Média | — | |
| financial.receivable.confirm_receipt | Confirmar recebimento | Alta | — | |
| financial.receivable.export | Exportar contas a receber | Baixa | — | |
| financial.payable.view | Visualizar conta a pagar | Média | — | |
| financial.payable.create | Lançar conta a pagar | Média | — | |
| financial.payable.edit | Editar conta a pagar | Média | — | |
| financial.payable.approve | Aprovar conta a pagar acima da alçada | Alta | Financeiro | |
| financial.payable.reject | Reprovar conta a pagar | Alta | Financeiro | |
| financial.payable.pay | Efetuar pagamento | Alta | — | |
| financial.payable.reconcile | Conciliar pagamento | Média | — | |
| financial.advance.view | Visualizar adiantamento | Média | — | |
| financial.advance.view_own | Visualizar os próprios adiantamentos | Baixa | — | ● |
| financial.advance.create | Conceder adiantamento | Média | — | |
| financial.advance.edit | Editar adiantamento | Média | — | |
| financial.driver_balance.view | Visualizar haver do motorista | Média | — | |
| financial.driver_balance.view_own | Visualizar o próprio haver | Baixa | — | ● |
| financial.cost_center.view | Visualizar centro de custo | Baixa | — | |
| financial.cost_center.create | Criar centro de custo | Média | — | |
| financial.cost_center.edit | Editar centro de custo | Média | — | |
| financial.cost_allocation.view | Visualizar rateio de custo | Média | — | |
| financial.cost_allocation.create | Criar rateio de custo | Média | — | |
| financial.chart_of_accounts.view | Visualizar conta do plano de contas | Baixa | — | |
| financial.chart_of_accounts.create | Criar conta do plano de contas | Média | — | |
| financial.chart_of_accounts.edit | Editar conta do plano de contas | Média | — | |
| financial.chart_of_accounts.delete | Excluir conta do plano de contas | Média | — | |
| financial.bank_account.view | Visualizar conta bancária | Média | — | |
| financial.bank_account.create | Criar conta bancária | Alta | Financeiro | |
| financial.bank_account.edit | Editar conta bancária | Alta | Financeiro | |
| financial.bank_account.delete | Excluir conta bancária | Alta | Financeiro | |
| financial.reversal.view | Visualizar estorno | Média | — | |
| financial.reversal.create | Registrar estorno | Alta | Financeiro | |
| financial.bank_reconciliation.view | Visualizar conciliação bancária | Média | — | |
| financial.bank_reconciliation.create | Registrar conciliação bancária | Média | — | |
| financial.cash_flow.view | Visualizar fluxo de caixa | Alta | — | |
| financial.cash_flow.export | Exportar fluxo de caixa | Alta | — | |
| financial.dre.view | Visualizar DRE | Alta | — | |
| financial.dre.export | Exportar DRE | Alta | — | |
| financial.trip_predicted_value.view | Visualizar receita/custo previsto da viagem | Média | — | |
| financial.trip_actual_value.view | Visualizar receita/custo realizado da viagem | Alta | — | |
| financial.trip_margin.view | Visualizar margem da viagem | Alta | — | |

### 7.19 `subscription` / `billing` — Plano, Assinatura, Cobrança

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| subscription.plan.view | Visualizar plano | Baixa | — | |
| subscription.subscription.view | Visualizar assinatura | Baixa | — | |
| subscription.subscription.upgrade | Fazer upgrade de plano | Média | — | |
| subscription.subscription.downgrade | Fazer downgrade de plano | Média | — | |
| subscription.subscription.cancel | Cancelar assinatura | Alta | Administrador Empresa | |
| subscription.subscription.reactivate | Reativar assinatura | Média | — | |
| billing.recurring_charge.view | Visualizar cobrança recorrente | Baixa | — | |
| billing.recurring_charge.retry | Tentar cobrança novamente | Média | — | |

### 7.20 `onboarding` — Cadastro e Configuração Inicial

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| onboarding.signup.create | Realizar cadastro self-service | Baixa | — (público, sem RBAC — ponto de entrada) | |
| onboarding.tenant_setup.view | Visualizar configuração inicial do tenant | Baixa | — | |
| onboarding.tenant_setup.edit | Editar configuração inicial do tenant | Média | — | |
| onboarding.assisted_setup.perform | Realizar implantação assistida | Média | — | |

### 7.21 `audit` — Trilha e Logs

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| audit.trail.view | Visualizar trilha de auditoria | Alta | — | |
| audit.access_log.view | Visualizar logs de acesso | Alta | — | |
| audit.trail.export | Exportar trilha de auditoria | Alta | — | |

### 7.22 `storage` — Arquivos, Anexos, Comentários

`.attachment.*` já existia. `.file.*` e `.comment.*` criados no Sprint 10/Lote 12 (D325) —
`arquivos`/`comentarios` são infraestrutura transversal (D024/D186) que nunca teve código próprio;
agrupados aqui por serem o mesmo bounded context físico (`storage`) já usado por Anexo.

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| storage.attachment.view | Visualizar anexo | Baixa | — | |
| storage.attachment.create | Criar anexo | Baixa | — | ● |
| storage.attachment.delete | Excluir anexo | Média | Gerente Operacional | |
| storage.file.view | Visualizar metadados de arquivo | Baixa | — | |
| storage.file.upload | Enviar arquivo (upload) | Baixa | — | ● |
| storage.file.delete | Excluir arquivo | Média | Gerente Operacional | |
| storage.comment.view | Visualizar comentário | Baixa | — | ● |
| storage.comment.create | Criar comentário | Baixa | — | ● |
| storage.comment.edit_own | Editar o próprio comentário | Baixa | — | |
| storage.comment.delete_own | Excluir o próprio comentário | Baixa | — | |

### 7.23 `analytics` / `reporting` — Relatórios, Dashboard, Métrica, Indicador, Snapshot, Cubo

Códigos `*_report`/`executive_dashboard` (pré-existentes) cobrem relatórios pré-construídos/
canônicos — surface diferente e mais simples do que o sistema flexível de Métrica/Indicador/
Dashboard/Relatório Salvo abaixo (adicionado nesta preparação, D313), nunca confundidos.

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| analytics.freight_report.view | Visualizar relatório de fretes | Baixa | — | |
| analytics.freight_report.export | Exportar relatório de fretes | Baixa | — | |
| analytics.financial_report.view | Visualizar relatório financeiro | Alta | — | |
| analytics.financial_report.export | Exportar relatório financeiro | Alta | — | |
| analytics.executive_dashboard.view | Visualizar dashboard executivo | Média | — | |
| analytics.maintenance_report.view | Visualizar relatório de manutenção | Baixa | — | |
| analytics.driver_report.view | Visualizar relatório de motoristas | Baixa | — | |
| analytics.metric.view | Visualizar métrica | Baixa | — | |
| analytics.metric.create | Criar métrica | Média | — | |
| analytics.metric.edit | Editar métrica (nova versão, D155) | Média | — | |
| analytics.indicator.view | Visualizar indicador consolidado | Baixa | — | |
| analytics.snapshot.view | Visualizar snapshot analítico | Baixa | — | |
| analytics.snapshot.create | Iniciar consolidação de snapshot | Média | — | |
| analytics.cube.view | Visualizar cubo analítico | Baixa | — | |
| analytics.cube.create | Criar cubo analítico | Média | — | |
| analytics.cube.edit | Editar cubo analítico | Média | — | |
| reporting.dashboard.view_own | Visualizar os próprios dashboards | Baixa | — | |
| reporting.dashboard.view_shared | Visualizar dashboards compartilhados com o usuário | Baixa | — | |
| reporting.dashboard.create | Criar dashboard | Baixa | — | |
| reporting.dashboard.edit_own | Editar o próprio dashboard | Baixa | — | |
| reporting.dashboard.delete_own | Excluir o próprio dashboard | Baixa | — | |
| reporting.dashboard.share | Compartilhar dashboard com grupo/papel | Média | — | |
| reporting.saved_filter.view_own | Visualizar os próprios filtros salvos | Baixa | — | |
| reporting.saved_filter.create | Criar filtro salvo | Baixa | — | |
| reporting.saved_filter.edit_own | Editar o próprio filtro salvo | Baixa | — | |
| reporting.saved_filter.delete_own | Excluir o próprio filtro salvo | Baixa | — | |
| reporting.saved_report.view_own | Visualizar os próprios relatórios salvos | Baixa | — | |
| reporting.saved_report.create | Criar relatório salvo | Baixa | — | |
| reporting.saved_report.edit_own | Editar o próprio relatório salvo | Baixa | — | |
| reporting.saved_report.delete_own | Excluir o próprio relatório salvo | Baixa | — | |
| reporting.export.view_own | Visualizar as próprias exportações | Baixa | — | |
| reporting.export.create | Solicitar exportação | Baixa | — | |
| reporting.scheduled_update.view | Visualizar agendamento de atualização | Baixa | — | |
| reporting.scheduled_update.create | Criar agendamento de atualização | Média | — | |
| reporting.scheduled_update.edit | Editar agendamento de atualização | Média | — | |

### 7.24 `notification_center` — Alertas

`.alert.manage_own` e `.channel_preference.view` criados no Sprint 10/Lote 12 (D325) — a entidade
Notificação nunca existiu em Domain/DDL até este lote (D323); `.view`/`.configure`/
`.channel_preference.edit` já existiam, antecipando a capacidade sem o restante da cadeia (mesmo
padrão de D294).

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| notification_center.alert.view | Visualizar alertas | Baixa | — | ● |
| notification_center.alert.manage_own | Marcar como lida/descartar a própria notificação | Baixa | — | ● |
| notification_center.alert.configure | Configurar alertas | Baixa | — | |
| notification_center.channel_preference.view | Visualizar a própria preferência de canal | Baixa | — | ● |
| notification_center.channel_preference.edit | Editar a própria preferência de canal | Baixa | — | ● |

### 7.25 `support` — Ticket

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| support.ticket.view | Visualizar ticket | Baixa | — | |
| support.ticket.create | Criar ticket | Baixa | — | |
| support.ticket.respond | Responder ticket | Baixa | — | |
| support.ticket.close | Encerrar ticket | Baixa | — | |

### 7.26 Administração da Plataforma (cross-tenant — equipe GestorFrete)

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| platform.tenant.view | Visualizar tenant (cross-tenant) | Crítica | — (sempre auditado, seção 14) | |
| platform.tenant.suspend | Suspender tenant | Crítica | Administrador SaaS | |
| platform.tenant.reactivate | Reativar tenant | Crítica | Administrador SaaS | |
| platform.monitoring.view | Visualizar monitoramento da plataforma | Média | — | |
| platform.plan_global.view | Visualizar planos globais | Baixa | — | |
| platform.plan_global.edit | Editar planos globais | Crítica | Administrador SaaS | |
| platform.cross_tenant_access.grant | Conceder acesso cross-tenant temporário | Crítica | Administrador SaaS | |

### 7.27 `mobile` — Sessão, Dispositivo, Sincronização

Autoatendimento do próprio Motorista sobre a infraestrutura do App — nunca sobre dados de domínio
(ações de domínio como aceitar/iniciar viagem, preencher checklist etc. continuam usando os
códigos dos módulos correspondentes, D303). Sessão (D140) não tem código próprio — login é
pré-autenticação, mesmo padrão de `auth.login` (Lote 2 API).

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| mobile.device.view_own | Visualizar os próprios dispositivos | Baixa | — | ● |
| mobile.device.edit_own | Atualizar dados do próprio dispositivo (versão, push token) | Baixa | — | ● |
| mobile.sync.execute | Sincronizar comandos pendentes | Baixa | — | ● |

### 7.28 `ai` — Modelo, Inferência, Sugestão, Predição, Classificação, Anomalia, Visão Computacional, Feedback

Bounded context inteiramente sem representação antes desta preparação (D313) — 8 entidades
plenamente especificadas em Domain/Dictionary/DDL (D161–D172), nenhum código existia.

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| ai.model.view | Visualizar modelo de IA | Baixa | — | |
| ai.model.create | Criar modelo de IA | Alta | — | |
| ai.model.edit | Editar modelo de IA | Alta | — | |
| ai.inference.view | Visualizar inferência (entrada/saída/confiança/modelo/duração) | Média | — | |
| ai.inference.view_cost | Visualizar custo da inferência | Alta | — | |
| ai.suggestion.view | Visualizar sugestão de IA | Baixa | — | |
| ai.suggestion.decide | Aceitar/rejeitar/ignorar sugestão de IA | Média | — | |
| ai.prediction.view | Visualizar predição de IA | Baixa | — | |
| ai.classification.view | Visualizar classificação de IA | Baixa | — | |
| ai.anomaly.view | Visualizar anomalia detectada | Baixa | — | |
| ai.anomaly.review | Investigar/descartar anomalia detectada | Média | — | |
| ai.computer_vision.view | Visualizar leitura de visão computacional | Baixa | — | |
| ai.computer_vision.confirm | Confirmar/rejeitar leitura de visão computacional | Média | — | |
| ai.feedback.view | Visualizar feedback de IA | Baixa | — | |
| ai.feedback.create | Registrar feedback de IA | Baixa | — | ● |

### 7.29 `integration` — Configuração de Integração, Webhook, Execução de Job

Bounded context inteiramente sem representação antes desta preparação (D325) — as três entidades já
existiam em Domain/DDL desde o Sprint 09 (`010-administracao.md` Bloco 6), nenhum código RBAC
jamais foi criado. Sétima ocorrência do padrão "seção inteira ausente" (após D271/D283/D293/D304/
D313). `integration.job.trigger` é deliberadamente Alta/Aprovação — pedido explícito do usuário
("o endpoint não deve permitir que um usuário comum dispare qualquer job arbitrário").

| Código | Nome | Criticidade | Aprovação | App |
|---|---|---|---|---|
| integration.config.view | Visualizar configuração de integração | Média | — | |
| integration.config.create | Criar configuração de integração | Alta | — | |
| integration.config.edit | Editar configuração de integração | Alta | — | |
| integration.config.enable | Habilitar integração | Alta | — | |
| integration.config.disable | Desabilitar integração | Alta | — | |
| integration.webhook.view | Visualizar webhook | Média | — | |
| integration.webhook.create | Criar webhook | Alta | — | |
| integration.webhook.edit | Editar webhook | Alta | — | |
| integration.webhook.activate | Ativar webhook | Alta | — | |
| integration.webhook.suspend | Suspender webhook | Alta | — | |
| integration.webhook.test | Testar entrega de webhook | Média | — | |
| integration.job.view | Visualizar execução de job | Média | — | |
| integration.job.trigger | Disparar job manualmente | Alta | Administrador Empresa | |

**Total desta versão: 404 permissões.**

**Correção do OpenAPI Freeze (D329-adjacent finding)**: a linha acima ficou parada em "379" apesar
de sucessivas seções terem adicionado códigos em lotes anteriores sem recontagem exata — a
auditoria do Freeze (Sprint 10, `docs/api/OPENAPI_FREEZE.md`) recontou cada linha `código | nome |
criticidade | aprovação | app` da tabela por script (não de memória) e confirmou **404** códigos
únicos, sem duplicatas. Corrigido aqui; nenhuma permissão foi adicionada ou removida por esta
correção — é uma correção de contagem, não uma mudança de contrato.

## 8. Regras especiais

- **Motorista**: só visualiza suas próprias viagens, checklists, documentos e desempenho (todas as
  permissões `*.view_own`/`*_own` acima). Nunca vê financeiro, custos da empresa ou dados de outros
  motoristas — não por negação explícita (D054), mas porque o Perfil Motorista simplesmente não
  inclui nenhuma dessas permissões (ausência, não bloqueio).
- **Auditor**: apenas permissões `*.view*` — nenhuma de criar/editar/aprovar/cancelar em nenhum
  módulo. Reforça o que já estava em [`PERSONAS.md`](./PERSONAS.md), persona 11.
- **Administrador SaaS**: as únicas permissões `platform.*` (cross-tenant) — ver seção 14.

## 9. Hierarquia

```
Administrador
      │
   Diretor
      │
   Gerente
      │
  Supervisor
      │
   Analista
      │
 Operacional
```

**Sem herança implícita.** Este diagrama é uma referência organizacional (útil, por exemplo, para
sugerir um conjunto inicial de Permissões ao criar um Perfil novo) — **não** é um mecanismo de
autorização. Um Diretor não recebe automaticamente tudo que um Gerente tem; cada Perfil declara
suas Permissões explicitamente (D052). Herança implícita foi deliberadamente descartada: torna
difícil saber, olhando um Perfil, o que ele realmente concede.

## 10. Aprovação

Exemplos oficiais desta revisão, já refletidos na matriz da seção 7:

| Ação | Aprovador |
|---|---|
| Cancelar viagem (`freight.trip.cancel`) | Supervisor / Gerente Operacional |
| Cancelar CT-e (`documents.cte.cancel`) | Diretor |
| Alterar valor do frete (`freight.trip.edit_cost`) | Financeiro **+** Coordenador Logístico (D062 — duas aprovações simultâneas, não uma ou outra) |

## 11. Auditoria

Todo evento de acesso/permissão (D055) registra: usuário, perfil, permissão, ação, data/hora, IP,
dispositivo, motivo (quando aplicável) e resultado (concedido/negado). Consumido por `audit` (D007)
— ver [`audit.trail.view`](#721-audit--trilha-e-logs) na matriz.

## 12. API

D061: toda API (interna, usada pelo próprio frontend, ou futura API Pública) usa exatamente a
mesma matriz — nunca há permissão exclusiva de um canal. Hoje nenhuma permissão tem endpoint de API
Pública externo (essa API não existe ainda, é V4 — ver
[`MODULE_PRIORITY.md`](./MODULE_PRIORITY.md) e [`VISION.md`](./VISION.md), capítulo 23); quando
existir, contas de serviço (Usuários não-humanos) terão Perfis próprios, com Escopo explícito, nunca
acesso irrestrito "de sistema".

## 13. Aplicativo do Motorista

Permissões marcadas `●` na coluna App, na matriz da seção 7. Resumo do que o Motorista **pode**:
aceitar/iniciar/pausar/retomar/finalizar viagem (`freight.trip.edit` cobre aceitar/pausar/retomar —
D240, lacuna de granularidade já registrada, não um código próprio por comando), anexar fotos,
registrar ocorrência, preencher checklist, visualizar rota, visualizar documentos da viagem,
registrar coleta/entrega/canhoto, solicitar/registrar abastecimento, visualizar seu desempenho/
adiantamentos/haveres, gerenciar os próprios dispositivos e sincronizar comandos pendentes
(`mobile.*`, D304). O que **nunca** pode, porque o Perfil Motorista não inclui: `fleet.vehicle.edit`,
`documents.cte.issue`, `freight.trip.edit_cost`, ou qualquer `*.delete`.

## 14. Multiempresa

Usuário pertence a exatamente um Tenant (D005/D006) e nunca visualiza outro. Exceções — todas
Tipo de acesso "Cross-Tenant" ou "Temporário" (D056), nunca "Permanente" sem ressalva:

| Perfil | Tipo de acesso cross-tenant |
|---|---|
| Administrador SaaS | Permanente, mas sempre auditado (D055) e escopado por ação |
| Implantação | Temporário, durante a implantação de um tenant específico |
| Suporte | Temporário, durante o atendimento de um ticket específico |
| Auditor Interno | Cross-tenant para fins de compliance da própria plataforma GestorFrete — distinto do Auditor (persona 11), que é escopado a um único tenant |

Todo acesso cross-tenant é auditado (D055), possui motivo obrigatório, possui validade (mesmo o do
Administrador SaaS é revisável) e gera evento — sem exceção.

## Regras futuras

- Estender [`PERSONAS.md`](./PERSONAS.md) para os perfis novos identificados nesta e na revisão
  anterior (Administrador Empresa, Supervisor de Frota, Coordenador Logístico, Analista Logístico,
  Fiscal, Auditor Interno) — recomendado, não executado.
- Resolver a omissão de Almoxarife na lista de perfis desta revisão.
- Completar a matriz da seção 7 conforme `docs/domain/006-financeiro.md` a `012-ia.md` forem
  escritos (CRM completo, Marketplace, Telemetria, IA, BI avançado, Suporte detalhado) — caminho
  para as 500+ permissões esperadas.
- Granularidade exata do escopo "Unidade" (ver seção 6).
- Permissões por API Pública real, quando essa API existir (V4).
