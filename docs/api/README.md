# docs/api — Arquitetura da API (Sprint 10)

Índice mestre da arquitetura de API do GestorFrete. Contrato definido antes da implementação
(D210) — todo endpoint de módulo obedece à fundação do Lote 1, nunca o contrário.

## Fundação (Lote 1 — concluído)

| Documento | Conteúdo |
|---|---|
| [`OPENAPI_ARCHITECTURE.md`](./OPENAPI_ARCHITECTURE.md) | OpenAPI 3.1, REST, JSON, HTTPS, superfícies (ERP Web/App Motorista/API Pública/API Interna/Webhooks), padrão de resposta, cabeçalhos, pipeline Auth→Tenant→RBAC→Domínio |
| [`NAMING_CONVENTION.md`](./NAMING_CONVENTION.md) | Recursos, verbos HTTP, `kebab-case`, comandos de domínio nomeados, códigos HTTP, exceção de idioma (D221) |
| [`VERSIONING.md`](./VERSIONING.md) | `/api/v1`, D207, o que força `v2` |
| [`AUTHENTICATION.md`](./AUTHENTICATION.md) | Mecanismos por superfície (JWT Web/Mobile, API Key/Client Credential, HMAC de webhook), D208/D212 |
| [`ERROR_MODEL.md`](./ERROR_MODEL.md) | Envelope de erro, categorias, códigos HTTP, D209 |
| [`PAGINATION.md`](./PAGINATION.md) | Offset (Master Data/Transactional) vs. Cursor (Time Series/History) — decidido pela Categoria Física de `TABLES.md` |
| [`FILTERING_SORTING.md`](./FILTERING_SORTING.md) | Operadores de filtro (`__gt`/`__in`/etc.), sintaxe de ordenação |
| [`IDEMPOTENCY.md`](./IDEMPOTENCY.md) | `Idempotency-Key`, D211, camada HTTP de D111/D138 |
| [`RATE_LIMITING.md`](./RATE_LIMITING.md) | Dimensões (usuário/tenant/IP/API key) e categorias de operação — sem números fixados ainda |
| [`WEBHOOKS.md`](./WEBHOOKS.md) | Contrato sobre a tabela `webhooks` já física — evento, assinatura HMAC, retry, replay |

## Core + Identidade + Autenticação (Lote 2 — concluído)

| Documento | Conteúdo |
|---|---|
| [`001-authentication.md`](./001-authentication.md) | `login`/`refresh`/`logout`/`forgot-password`/`reset-password`/`me` |
| [`002-tenants.md`](./002-tenants.md) | `GET`/`PATCH /tenant` — sempre o tenant do contexto autenticado, nunca selecionável |
| [`003-users.md`](./003-users.md) | CRUD de Usuário + atribuição de Papel (`role_ids`, via `usuarios_papeis`, D222) |
| [`004-roles.md`](./004-roles.md) | CRUD de Papel + atribuição de Permissão por código |
| [`005-permissions.md`](./005-permissions.md) | Catálogo de Permissões — somente leitura (Platform Reference Data) |
| [`006-branches.md`](./006-branches.md) | CRUD de Filial — **emendado no Lote 3** (D231): endereço deixou de ser campo embutido |

## Cadastros (Lote 3 — concluído)

| Documento | Conteúdo |
|---|---|
| [`007-clients.md`](./007-clients.md) | CRUD de Cliente + sub-recursos Endereços/Contatos |
| [`008-suppliers.md`](./008-suppliers.md) | CRUD de Fornecedor — 1 recurso, `category` cobre oficina/posto/seguradora/borracharia/guincho/autopeças/outros |
| [`009-drivers.md`](./009-drivers.md) | CRUD de Motorista + `/me` + `block`/`unblock` + sub-recurso Documentos (CNH/RG/Exame/ANTT) |
| [`010-employees.md`](./010-employees.md) | CRUD de Funcionário (D196) — vínculo opcional a Usuário, direção `usuarios.funcionario_id` |
| [`011-addresses.md`](./011-addresses.md) | Sub-recurso compartilhado Cliente/Fornecedor/Filial (D182/D225/D231) |
| [`012-contacts.md`](./012-contacts.md) | Sub-recurso exclusivo de Cliente — não polimórfico |
| [`013-cost-centers.md`](./013-cost-centers.md) | CRUD de Centro de Custo — sem saldo/indicador (D090), sem `DELETE` (RBAC não tem o código) |

## Viagens (Lote 4 — concluído)

Primeira API operacional completa — Viagem é o core domain do GestorFrete
([`../flows/002-VIAGEM.md`](../flows/002-VIAGEM.md), referência canônica da máquina de estados).

| Documento | Conteúdo |
|---|---|
| [`014-trips.md`](./014-trips.md) | CRUD de Viagem, referências vs. snapshots, visão geral dos comandos |
| [`015-trip-deliveries.md`](./015-trip-deliveries.md) | Entregas (sub-recurso) + Canhoto — Coleta/Romaneio fora de escopo (sem endpoint ainda) |
| [`016-trip-resources.md`](./016-trip-resources.md) | Alocação de recursos — pacote atômico (D188), `commands/reallocate-resources` |
| [`017-trip-occurrences.md`](./017-trip-occurrences.md) | Ocorrências — uma única entidade para todo tipo (D076) |
| [`018-trip-status.md`](./018-trip-status.md) | **Documento central** — toda transição de `002-VIAGEM.md` mapeada para comando (ou marcada derivada/externa), RBAC, pré-condições, eventos, erros |
| [`019-trip-timeline.md`](./019-trip-timeline.md) | Timeline Universal (D187/D022) — projeção de leitura, cursor-paginada, honesta sobre quais fontes já estão incluídas |
| [`components/trip-schemas.md`](./components/trip-schemas.md) | `Trip`/`TripStatus`/`TripReferences`/`TripSnapshots`/`TripFinancials`/`TripAllocation`/`Delivery`/`ProofOfDelivery`/`Occurrence`/`TripTimelineEntry` |

## Frota (Lote 5 — concluído)

| Documento | Conteúdo |
|---|---|
| [`020-vehicles.md`](./020-vehicles.md) | CRUD de Veículo Tracionador (Identidade/Operacional) + sub-recurso Ficha Técnica (`technical-sheet`) |
| [`021-vehicle-documents.md`](./021-vehicle-documents.md) | Documentos do veículo — sub-recurso, referencia Storage (D251), sem `.edit` dedicado (gap documentado) |
| [`022-implements.md`](./022-implements.md) | CRUD de Implemento — entidade independente de Composição |
| [`023-vehicle-compositions.md`](./023-vehicle-compositions.md) | Composição Veicular — vigência (D248), nunca `PATCH`, pertence à Frota não à Viagem (D249) |
| [`024-odometer-readings.md`](./024-odometer-readings.md) | Leituras de hodômetro — Time Series imutável (D191/D246), cursor-paginada |
| [`025-vehicle-availability.md`](./025-vehicle-availability.md) | Disponibilidade — Read Model puro, sem verbo de escrita (D247) |
| [`components/fleet-schemas.md`](./components/fleet-schemas.md) | `VehicleIdentity`/`VehicleTechnicalSheet`/`VehicleOperational`/`Vehicle`/`Implement`/`VehicleComposition`/`OdometerReading`/`VehicleAvailability`/`VehicleDocument` |

## Manutenção (Lote 6 — concluído)

| Documento | Conteúdo |
|---|---|
| [`026-maintenance-orders.md`](./026-maintenance-orders.md) | **Documento central** — CRUD de Ordem de Serviço (Aggregate Root, D252) + toda transição de `003-MANUTENCAO.md` mapeada para comando (ou marcada derivada), D253 |
| [`027-maintenance-order-items.md`](./027-maintenance-order-items.md) | Itens de OS (sub-recurso) — custo realizado é derivado (D254/D087) |
| [`028-maintenance-approvals.md`](./028-maintenance-approvals.md) | Aprovações de custo — recurso próprio, alçada só consultada em `settings` (D255) |
| [`029-preventive-maintenance-plans.md`](./029-preventive-maintenance-plans.md) | CRUD de Plano de Manutenção Preventiva (`tipo_gatilho` extensível) + Tipos de Serviço (pré-requisito) |
| [`030-maintenance-history.md`](./030-maintenance-history.md) | Histórico operacional de status da OS — somente leitura (D257), nunca Timeline Universal |
| [`031-maintenance-triggers.md`](./031-maintenance-triggers.md) | Documentação de `origem_abertura` (D256) — sem endpoints, nenhum gatilho inventado |
| [`components/maintenance-schemas.md`](./components/maintenance-schemas.md) | `MaintenanceOrder`/`MaintenanceOrderItem`/`MaintenanceApproval`/`MaintenancePreventivePlan`/`ServiceType`/`MaintenanceOrderStatusHistoryEntry` |

## Financeiro (Lote 7 — concluído)

| Documento | Conteúdo |
|---|---|
| [`032-accounts-payable.md`](./032-accounts-payable.md) | CRUD de Conta a Pagar + comandos `approve`/`reject`/`pay` — desfecho negativo real é `REJEITADA`, nunca `cancel` (D273) |
| [`033-accounts-receivable.md`](./033-accounts-receivable.md) | CRUD mínimo de Fatura (D260) + sub-recurso Conta a Receber (parcelas) + `commands/confirm-receipt` |
| [`034-chart-of-accounts.md`](./034-chart-of-accounts.md) | CRUD de Plano de Contas — hierarquia sem ciclo, RBAC criado nesta preparação (D271) |
| [`035-recurring-billing.md`](./035-recurring-billing.md) | Plano/Assinatura/Cobrança Recorrente — bounded context `subscription`/`billing`, não `financial` (D272) |
| [`036-bank-accounts.md`](./036-bank-accounts.md) | CRUD de Conta Bancária (RBAC criado, D271) + extrato + saldo sempre derivado (D263) + Posição de Caixa (Read Model) |
| [`037-bank-reconciliation.md`](./037-bank-reconciliation.md) | Conciliação Bancária (Extrato→Lançamento→Correspondência→Conciliação) + Estorno Financeiro (D266) |
| [`038-financial-trip.md`](./038-financial-trip.md) | `GET /viagens/{id}/financeiro` — leitura especializada, Viagem continua dona dos valores (D262) |
| [`components/financial-schemas.md`](./components/financial-schemas.md) | `AccountsPayable`/`AccountsReceivable`/`Invoice`/`ChartOfAccounts`/`BankAccount`/`BankReconciliation`/`FinancialReversal`/`TripFinancialsView`/`SubscriptionPlan`/`Subscription`/`RecurringCharge` |

## Fiscal (Lote 8 — concluído)

| Documento | Conteúdo |
|---|---|
| [`039-cte.md`](./039-cte.md) | **Documento central** — máquina de 8 estados do CT-e, sem `POST` manual (criação automática via `ViagemDespachada`), comandos `validate`/`sign`/`transmit`/`cancel`/`inutilize` |
| [`040-mdfe.md`](./040-mdfe.md) | MDF-e — consolida CT-e `AUTORIZADO`, `commands/close` trava D019 até encerramento |
| [`041-ciot.md`](./041-ciot.md) | CIOT — motorista autônomo, `protocolo_antt` distinto de `protocolo_sefaz` |
| [`042-carta-correcao.md`](./042-carta-correcao.md) | Carta de Correção — artefato anexado ao CT-e `AUTORIZADO`, nunca altera o documento pai (D282) |
| [`043-nfe-referenciada.md`](./043-nfe-referenciada.md) | NF-e Referenciada — referência fiscal, nunca uma NF-e emitida pela transportadora |
| [`044-eventos-fiscais.md`](./044-eventos-fiscais.md) | Evento Fiscal — log técnico bruto, somente leitura (D277), distinto do `*StatusHistory` de negócio (D281) |
| [`045-configuracao-fiscal.md`](./045-configuracao-fiscal.md) | Configuração Fiscal do Tenant — RBAC criado nesta preparação (D283), certificado nunca em texto (D279) |
| [`components/fiscal-schemas.md`](./components/fiscal-schemas.md) | `CTe`/`MDFe`/`CIOT`/`CorrectionLetter`/`ReferencedNFe`/`FiscalEvent`/`*StatusHistoryEntry`/`FiscalConfiguration` |

## Rastreamento (Lote 9 — concluído)

| Documento | Conteúdo |
|---|---|
| [`046-tracking-providers.md`](./046-tracking-providers.md) | CRUD de Provedor de Rastreamento — domínio agnóstico de fornecedor (D291), RBAC criado (D293) |
| [`047-tracking-devices.md`](./047-tracking-devices.md) | Equipamentos de Rastreamento — múltiplos por veículo, no máximo um `PRINCIPAL` vigente (D128) |
| [`048-vehicle-positions.md`](./048-vehicle-positions.md) | Posições — Time Series, somente leitura, cursor obrigatório (D285/D286/D287) + catálogo de Origens |
| [`049-telemetry-readings.md`](./049-telemetry-readings.md) | Telemetria — Time Series EAV (D120), somente leitura, sem endpoint por sensor |
| [`050-heartbeats.md`](./050-heartbeats.md) | Heartbeats — sinal técnico, nunca evento de negócio automaticamente |
| [`051-tracking-events.md`](./051-tracking-events.md) | **Documento central** — Eventos derivados (D119/D288), autorização por categoria numa única tabela (D294) |
| [`052-geofences.md`](./052-geofences.md) | Geofences — CRUD completo de configuração (D289) + Configuração de Limite de Velocidade |
| [`053-tracking-history.md`](./053-tracking-history.md) | Histórico de Rastreamento — Read Model composto, sem tabela própria (D290) |
| [`components/tracking-schemas.md`](./components/tracking-schemas.md) | `TrackingProvider`/`TrackingEquipment`/`VehiclePosition`/`TelemetryReading`/`Heartbeat`/`TrackingEvent`/`Geofence`/`SpeedLimitConfig`/`LocationOrigin`/`TrackingHistoryEntry` |

## App Motorista (Lote 10 — concluído)

| Documento | Conteúdo |
|---|---|
| [`054-driver-authentication.md`](./054-driver-authentication.md) | Login/refresh/logout/me — tenant/RBAC nunca vêm do dispositivo (D295/D296), push só informativo (D302) |
| [`055-driver-trips.md`](./055-driver-trips.md) | **Documento central** — viagens do motorista, mesmos comandos de `018-trip-status.md` (D297/D303) |
| [`056-driver-checklists.md`](./056-driver-checklists.md) | Documentação-only — Domain/Flow completos, DDL nunca traduzida (D305), sem endpoints |
| [`057-driver-occurrences.md`](./057-driver-occurrences.md) | Ocorrências — mesma entidade de `017`, D303 |
| [`058-driver-deliveries.md`](./058-driver-deliveries.md) | Entregas + Canhoto — cria Assinatura na mesma transação |
| [`059-driver-signatures.md`](./059-driver-signatures.md) | Assinaturas — somente leitura, criação sempre via comando de Entrega |
| [`060-driver-sync.md`](./060-driver-sync.md) | Fila de Sincronização — ordem por `sequencia_local` (D298), conflito resolvido pelo backend (D300) |
| [`061-driver-devices.md`](./061-driver-devices.md) | Dispositivos — autoatendimento do próprio motorista (D304) |
| [`components/mobile-schemas.md`](./components/mobile-schemas.md) | `MobileSession`/`MobileDevice`/`SyncQueueItem`/`SyncItemResult`/`SyncBatchResponse`/`SyncRecord`/`DigitalSignature` |

## BI + IA (Lote 11 — concluído)

Maior lote da sprint — dois bounded contexts (`analytics`/`reporting` e `ai`), 16 documentos.

| Documento | Conteúdo |
|---|---|
| [`062-metrics.md`](./062-metrics.md) | CRUD de Métrica (catálogo) — `formula` versionada, `PATCH` incrementa `version` automaticamente (D155) |
| [`063-consolidated-indicators.md`](./063-consolidated-indicators.md) | Indicadores Consolidados — só leitura, zero verbo de escrita (D156) |
| [`064-analytical-snapshots.md`](./064-analytical-snapshots.md) | Snapshots Analíticos — `POST` só inicia consolidação assíncrona, imutável após `CONSOLIDADO` (D151) |
| [`065-analytics-cubes.md`](./065-analytics-cubes.md) | Cubos Analíticos — definição estrutural, domínio-agnóstico de infraestrutura de execução |
| [`066-dashboards.md`](./066-dashboards.md) | Dashboards — configuração/referência (D152), `commands/share` separado do `PATCH` |
| [`067-saved-filters.md`](./067-saved-filters.md) | Filtros Favoritos — sempre pessoais, nunca globais |
| [`068-saved-reports.md`](./068-saved-reports.md) | Relatórios Salvos — configuração, nunca duplica query física |
| [`069-exports.md`](./069-exports.md) | Exportações — assíncrona (D307), arquivo sempre em Storage (D308) |
| [`070-scheduled-updates.md`](./070-scheduled-updates.md) | Agendamentos de Atualização — nunca executa cálculo, só solicita (D159) |
| [`components/bi-schemas.md`](./components/bi-schemas.md) | `Metric`/`ConsolidatedIndicator`/`AnalyticalSnapshot`/`AnalyticsCube`/`Dashboard`/`SavedFilter`/`SavedReport`/`Export`/`ScheduledUpdate` |
| [`071-ai-models.md`](./071-ai-models.md) | CRUD administrativo restrito de Modelo de IA — `logical_provider` nunca é o fornecedor real (D170/D309) |
| [`072-ai-inferences.md`](./072-ai-inferences.md) | Inferências de IA — log técnico cursor-paginado, `cost` com autorização por campo (terceira ocorrência) |
| [`073-ai-suggestions.md`](./073-ai-suggestions.md) | Sugestões de IA — `accept`/`reject`/`ignore` nunca executam o comando operacional diretamente (D311) |
| [`074-ai-predictions.md`](./074-ai-predictions.md) | Predições de IA — validade temporal sempre explícita (D312) |
| [`075-ai-classifications.md`](./075-ai-classifications.md) | Classificações **e** Anomalias Detectadas — entidades distintas (D076), agrupadas por não ter arquivo próprio |
| [`076-computer-vision.md`](./076-computer-vision.md) | Visão Computacional — arquivo→inferência→revisão humana?→confirmação (D161/D164) |
| [`077-ai-feedback.md`](./077-ai-feedback.md) | Feedback de IA — polimórfico (5 tipos de saída), matéria-prima de retreinamento (D165) |
| [`components/ai-schemas.md`](./components/ai-schemas.md) | `AIModel`/`AIInference`/`AISuggestion`/`AIPrediction`/`AIClassification`/`AIAnomaly`/`ComputerVisionReading`/`AIFeedback` |

## Recursos Transversais (Lote 12 — concluído)

Último lote da OpenAPI antes do congelamento do contrato — não é um bounded context operacional
específico, mas capacidades usadas por praticamente todo o sistema.

| Documento | Conteúdo |
|---|---|
| [`078-storage.md`](./078-storage.md) | Mecanismo de upload/download — iniciar/concluir upload, URL temporária, domínio-agnóstico de provedor (D314) |
| [`079-files.md`](./079-files.md) | `File` — metadados de arquivo (nome/MIME/tamanho/hash/versão/status/origem), distinto do mecanismo (D315), tabela `arquivos` criada nesta preparação (D324) |
| [`080-attachments.md`](./080-attachments.md) | Anexos — infraestrutura polimórfica (D186), dono resolvido pelo path (D316), ativado para Viagem |
| [`081-comments.md`](./081-comments.md) | Comentários — mesma infraestrutura de Anexos, só o autor edita/exclui |
| [`082-global-search.md`](./082-global-search.md) | Busca global — sem RBAC próprio, filtrada pela permissão `.view` de cada tipo de resultado (D317) |
| [`083-timelines.md`](./083-timelines.md) | Timeline Universal — padrão documentado, read model (D318), único endpoint implementado continua sendo `019-trip-timeline.md` |
| [`084-reports.md`](./084-reports.md) | Reconciliado com `068-saved-reports.md` (Lote 11) — nenhum recurso novo (D326) |
| [`085-exports.md`](./085-exports.md) | Reconciliado com `069-exports.md` (Lote 11) — nenhum recurso novo (D326) |
| [`086-notifications.md`](./086-notifications.md) | Notificações — efeito colateral de evento de domínio (D320), entidade criada nesta preparação (D323) |
| [`087-integrations.md`](./087-integrations.md) | Configuração de Integração — contrato único, nunca uma API por fornecedor (D321) |
| [`088-webhooks.md`](./088-webhooks.md) | Webhooks — `signing_secret` exibido uma única vez; histórico de tentativas de entrega é lacuna documentada, não inventada |
| [`089-jobs.md`](./089-jobs.md) | Execução de Job — `commands/trigger` restrito, nunca dispara job arbitrário (D322) |
| [`091-vehicle-categories.md`](./091-vehicle-categories.md) | Categoria de Veículo — D363 fechado (V1 Operational Hardening, Parte 5): CRUD real, domain/repository já existiam |
| [`components/transversal-schemas.md`](./components/transversal-schemas.md) | `File`/`Attachment`/`Comment`/`Notification`/`ChannelPreference`/`IntegrationConfig`/`Webhook`/`JobExecution` |

## Components e contrato executável

| Documento | Conteúdo |
|---|---|
| [`components/schemas.md`](./components/schemas.md) | `UUID`/`Pagination`/`PageMeta`/`Error`/`ValidationError`/`AuditMetadata`/`TenantContext`/`Timestamp`/`Money`/`AddressFields` + schemas de entidade dos Lotes 2/3 |
| [`components/trip-schemas.md`](./components/trip-schemas.md) | Schemas do agregado Viagem (Lote 4) |
| [`components/fleet-schemas.md`](./components/fleet-schemas.md) | Schemas de Frota (Lote 5) |
| [`components/maintenance-schemas.md`](./components/maintenance-schemas.md) | Schemas de Manutenção (Lote 6) |
| [`components/financial-schemas.md`](./components/financial-schemas.md) | Schemas de Financeiro + Subscription/Billing (Lote 7) |
| [`components/fiscal-schemas.md`](./components/fiscal-schemas.md) | Schemas de Fiscal (Lote 8) |
| [`components/tracking-schemas.md`](./components/tracking-schemas.md) | Schemas de Rastreamento (Lote 9) |
| [`components/mobile-schemas.md`](./components/mobile-schemas.md) | Schemas do App Motorista (Lote 10) |
| [`components/bi-schemas.md`](./components/bi-schemas.md) | Schemas de BI — analytics/reporting (Lote 11) |
| [`components/ai-schemas.md`](./components/ai-schemas.md) | Schemas de IA (Lote 11) |
| [`components/transversal-schemas.md`](./components/transversal-schemas.md) | Schemas de Recursos Transversais (Lote 12) |
| [`components/responses.md`](./components/responses.md) | `400`–`500` reutilizáveis |
| [`components/parameters.md`](./components/parameters.md) | Path/query/header reutilizáveis |
| [`components/security.md`](./components/security.md) | Esquemas de segurança + mapeamento completo endpoint→permissão RBAC (Lotes 2 a 12) |
| [`openapi.yaml`](./openapi.yaml) | Contrato executável — validado com `@redocly/cli lint` (D220), **0 erros** |

## Decisões

| Decisão | Resumo |
|---|---|
| D207 | API versionada — `/api/v1` |
| D208 | Tenant vem do contexto autenticado, nunca do cliente |
| D209 | `error.code` é estável, nunca reciclado para outro significado |
| D210 | OpenAPI é a fonte oficial do contrato |
| D211 | Idempotência obrigatória para comandos críticos |
| D212 | API não bypassa RBAC — mesma matriz de `RBAC_MATRIX.md` |
| D213 | API pública não expõe ID interno desnecessariamente |
| D214 | Controller/API nunca conhece infraestrutura (Clean Architecture) |
| D215 | Endpoint pertence a um único bounded context — nunca híbrido |
| D216 | OpenAPI referencia RBAC existente — nenhum código de permissão criado no documento da API |
| D217 | Response nunca é cópia direta da tabela SQL — Tabela → Domain → DTO → Response |
| D218 | Tenant nunca vem do body, mesmo para Administrador SaaS |
| D219 | `DELETE` é sempre soft delete (D007/D177), nunca `DELETE` físico |
| D220 | `openapi.yaml` válido conforme OpenAPI 3.1, pronto para CI |
| D221 | Exceção de idioma: endpoints de Core/Identidade/Tenancy em inglês, módulos de negócio em português |
| D222 | `usuarios_papeis` (N:N Usuário↔Papel) criada — gap retroativo, relação já prevista no Domain Model mas nunca materializada em DDL |
| D223 | Recursos de coleção usam plural |
| D224 | Identificador técnico não precisa ser exposto quando o código funcional bastar |
| D225 | Sub-recursos só existem com ciclo de vida/autorização próprios |
| D226 | Filtros correspondem só a dados que existem fisicamente |
| D227 | API não cria relacionamento implícito inexistente no domínio |
| D228 | Coleção paginada sempre tem `meta.pagination` |
| D229 | `PATCH` altera só campos explicitamente enviados |
| D230 | Conflito de unicidade sempre `409`, modelo oficial de erro |
| D231 | `filiais.endereco` removida — Filial passa a usar `enderecos` (polimórfico), completando D182; reabriu `Branch` do Lote 2 |
| D232 | Sub-recurso respeita ownership do domínio (D033) |
| D233 | Status não é mutável por CRUD — só por comando |
| D234 | Comandos são orientados a intenção, nunca `set_status` |
| D235 | Comando inválido para o estado atual retorna `409 Conflict` |
| D236 | Eventos não são comandos — nunca publicados diretamente pelo cliente |
| D237 | Aggregate Root controla alterações internas de sub-entidades |
| D238 | Response de comando sempre retorna o estado resultante |
| D239 | `MotoristaAceitouViagem` (D129) adicionado a `EVENT_MAP.md` — nunca tinha sido catalogado |
| D240 | RBAC sem código para Interromper/Retomar/Aceitar — `freight.trip.edit` reaproveitado, lacuna documentada, não escondida |
| D241 | API não promete estado que o domínio não alcança — documenta só as transições efetivamente disponíveis no escopo atual |
| D242 | Lacunas de dependência permanecem explícitas — quando uma operação depende de outro módulo ainda não documentado, o contrato indica a dependência em vez de improvisar |
| D243 | Schema de API distingue referência de snapshot — referência representa a entidade atual, snapshot é `readOnly` e representa o histórico congelado |
| D246 | Leitura Time Series é somente leitura — API não atualiza nem exclui leituras históricas |
| D247 | Read Model não possui comandos de escrita — Disponibilidade não recebe `POST`/`PATCH`/`DELETE` |
| D248 | Vigência é alterada por nova versão — nunca editar uma associação temporal existente, fecha a anterior e cria uma nova |
| D249 | Composição é pacote físico da Frota, não recurso operacional da Viagem — a Viagem referencia o resultado |
| D250 | Dados de rastreamento não são duplicados em Frota — Frota pode consultar dados derivados de `tracking`, nunca é proprietária deles |
| D251 | Documentos de Frota referenciam Storage — API manipula metadados/`arquivo_id`, nunca binário embutido |
| D252 | Ordem de Serviço é Aggregate Root — Item de OS, Solicitação de Peça e Aprovação de Custo nunca contornam suas regras |
| D253 | Status da OS só por comando — nunca `PATCH`, cada transição é um verbo próprio |
| D254 | Custo Realizado é derivado — API não aceita `custo_previsto`/`custo_realizado` digitáveis |
| D255 | Aprovação não altera alçada — Manutenção consulta a configuração de `settings`, nunca a modifica |
| D256 | Gatilho é origem, não status — `origem_abertura` nunca sobrepõe a máquina de estados |
| D257 | Histórico é somente leitura — nenhum endpoint operacional reescreve `ordens_servico_status_history` |
| D258 | Evidências referenciam Storage — fotos/notas fiscais são sempre `arquivo_id`, nunca binário |
| D259 | `OrdemServicoAprovada`/`OrdemServicoReprovada` adicionados a `EVENT_MAP.md` — decisão de aprovação nunca tinha evento próprio catalogado |
| D260 | Recursos de referência necessários são expostos pela API mesmo fora do escopo inicial do lote, quando plenamente especificados e sem introduzir conceito novo |
| D261 | Financeiro é dono das obrigações financeiras — Contas a Pagar/Receber pertencem a `financial` |
| D262 | Viagem é dona dos valores de sua operação — Receita/Custo Previsto/Realizado continuam em `freight` |
| D263 | Saldo é derivado — Conta Bancária e Posição de Caixa nunca são valores digitáveis |
| D264 | Baixa é comando — pagamento/recebimento/conciliação nunca são edição de status via `PATCH` |
| D265 | Integração externa não define domínio — Asaas/bancos nunca são fonte da máquina de estados interna |
| D266 | Documento financeiro preserva histórico — correção é por Estorno, nunca sobrescrevendo o passado |
| D267 | Dados financeiros sensíveis têm autorização própria — visualização de valor pode ser mais restrita que a do registro |
| D268 | API financeira não cria Read Model novo — consulta o que já existe (`posicoes_caixa`, `Trip.financials`) |
| D269 | `assinaturas_status_history` criada — D017/D018 exigia histórico para `assinaturas.status`, nunca materializado |
| D270 | `EstornoRealizado` adicionado a `EVENT_MAP.md` — mecanismo de correção nunca tinha evento próprio catalogado |
| D271 | `financial.chart_of_accounts.*`/`.bank_account.*`/`.reversal.*` criados em `RBAC_MATRIX.md` — três entidades plenamente especificadas sem nenhum código |
| D272 | Assinatura/Cobrança Recorrente/Plano pertencem a `subscription`/`billing`, não a `financial`, apesar do agrupamento temático do lote |
| D273 | "Cancelar" do pedido não corresponde a um estado real de Contas a Pagar/Receber — desfecho negativo real é `REJEITADA` (Pagar) ou Estorno (Receber) |
| D274 | Estado fiscal somente por comando — `status` de CT-e/MDF-e/CIOT nunca muda via `PATCH` |
| D275 | Protocolo externo é idempotência — `protocolo_sefaz`/`protocolo_antt` impedem duplo resultado fiscal |
| D276 | XML nunca é atributo textual — sempre `xml_arquivo_id`, referência a Storage |
| D277 | Evento Fiscal é somente leitura para usuários — nasce sempre da integração |
| D278 | Integração externa não é chamada diretamente pela API pública — sempre via Application → Documents → Integration |
| D279 | Certificado digital nunca é retornado como segredo — só `certificado_digital_arquivo_id` |
| D280 | Viagem mantém apenas projeção fiscal resumida — máquina detalhada pertence a cada documento fiscal |
| D281 | Documento fiscal possui histórico próprio — `*StatusHistory` append-only por agregado |
| D282 | Cancelamento, denegação e inutilização permanecem semanticamente distintos — nunca tratados como sinônimos |
| D283 | `documents.fiscal_config.*` criado em `RBAC_MATRIX.md` — Configuração Fiscal não tinha nenhum código |
| D284 | Campos padrão de histórico fiscal (`usuario`/`origem`/`observacao`) alinhados nas três tabelas — inconsistentes entre si apesar do fluxo pedir uniformidade |
| D285 | Tracking é somente observacional — a API nunca altera diretamente status operacional |
| D286 | Time Series é somente leitura pela API de negócio — dados brutos entram só via integração |
| D287 | Time Series usa cursor pagination — nunca offset para Posição/Telemetria/Heartbeat/Evento |
| D288 | Eventos derivados referenciam a origem — nunca copiam dados da Posição/Geofence original |
| D289 | Geofence é configuração, não histórico — CRUD completo; entrada/saída pertence aos Eventos |
| D290 | Histórico de Tracking é Read Model — composto a partir de Posição/Telemetria/Evento, sem tabela própria |
| D291 | API não expõe fornecedor como regra de negócio — domínio agnóstico de provedor |
| D292 | Timestamp de captura e processamento permanecem distintos — nunca colapsados em um campo |
| D293 | `tracking.provider`/`.equipment`/`.telemetry`/`.heartbeat` criados em `RBAC_MATRIX.md` — quatro entidades sem nenhum código |
| D294 | `eventos_rastreamento` (uma tabela) ganha autorização por categoria de linha, não só por campo — primeira ocorrência desse padrão |
| D295 | Mobile nunca recebe autoridade de Tenant — `tenant_id` sempre do contexto de autenticação |
| D296 | Mobile nunca altera RBAC — permissões sempre resolvidas ao vivo pelo backend (D060) |
| D297 | Mobile executa comandos do domínio — não possui máquina de estados própria |
| D298 | Sincronização respeita `sequencia_local` — processada na ordem de criação no dispositivo |
| D299 | Payload offline é preservado — comando original nunca sobrescrito, mesmo após conflito |
| D300 | Conflito é resolvido pelo backend — o App nunca decide, sempre recebe estado + razão |
| D301 | Fotos e documentos usam Storage — sempre `arquivo_id`, nunca binário embutido |
| D302 | Push não altera domínio — puramente informativo, mudança só ocorre por ação validada |
| D303 | Endpoint Mobile não duplica endpoint administrativo — mesma regra de domínio nos dois canais |
| D304 | `freight.trip.edit` ganha marcador App e nova seção `mobile` criada em `RBAC_MATRIX.md` — duas lacunas de granularidade/seção corrigidas |
| D305 | Checklist: Domain/Flow completos, DDL nunca traduzida — `056` fica documentação-only, gap registrado não inventado |
| D306 | BI não modifica domínio operacional — todo endpoint de `analytics`/`reporting` é leitura, configuração ou geração de exportação |
| D307 | Exportação é assíncrona quando supera limite operacional — `status` nasce `PROCESSANDO`, nunca bloqueia a requisição |
| D308 | Arquivo exportado pertence ao Storage — `file_id`, nunca conteúdo binário embutido |
| D309 | Modelo de IA não é fornecedor — `logical_provider` é sempre o conceito lógico, nunca o nome do produto comercial |
| D310 | Inferência e Sugestão são recursos distintos — Inferência é técnica, Sugestão é produto derivado |
| D311 | IA não executa comando operacional diretamente — aceitar uma Sugestão só registra a decisão; a execução é sempre um comando explícito do bounded context responsável |
| D312 | Predição mantém validade temporal — depois do prazo, o resultado não é tratado automaticamente como atual |
| D313 | `analytics`/`reporting`/`ai` criados em `RBAC_MATRIX.md` — dois bounded contexts inteiros (43 códigos) sem nenhuma representação |
| D314 | Storage é agnóstico ao fornecedor físico — a interface nunca menciona MinIO/S3/Azure Blob |
| D315 | Arquivo é diferente de armazenamento físico — `File` (metadados) distinto do mecanismo (`storage`) |
| D316 | Anexo não pode criar relação arbitrária fora do domínio — o recurso pai determina o contexto pelo path |
| D317 | Busca global respeita exatamente as mesmas autorizações das consultas originais — sem RBAC próprio |
| D318 | Timeline é read model — nenhuma tabela `timelines`, sempre projeção composta |
| D319 | Exportações grandes são assíncronas — reafirmação transversal de D307 (Lote 11) |
| D320 | Notificação não é evento de domínio — é o efeito colateral de entrega de um evento já publicado |
| D321 | Integração não expõe detalhes internos do provedor — contrato único, nunca uma API por fornecedor |
| D322 | Jobs são autorizados individualmente — `integration.job.trigger` nunca dispara comando arbitrário |
| D323 | `Notificação`/`Preferência de Canal de Notificação` criadas em Domain/Dictionary/Relational — RBAC já as antecipava |
| D324 | `arquivos` criada em `relational/010-administracao.md` — D024 já especificava os atributos, nunca traduzidos; FK retroativa em módulos já publicados deliberadamente fora de escopo |
| D325 | RBAC `storage`(`.file`/`.comment`)/`notification_center`/`integration` — três lacunas na mesma auditoria, 22 códigos novos, total 357 → 379 |
| D326 | `084-reports.md`/`085-exports.md` reconciliados com `068`/`069` (Lote 11) — nenhum recurso novo, mesma entidade física |
| D327 | `EVENT_MAP.md` ganha seção `integration` — `WebhookEntregue`/`WebhookFalhou`/`JobConcluido`/`JobFalhou` nomeados desde o Sprint 09, nunca catalogados |
| D328 | `082`/`083` não recebem RBAC nem tabela física nova — busca e timeline reusam autorização/dados já existentes |

Detalhe completo de cada uma em [`../product/DECISIONS.md`](../product/DECISIONS.md).

## Achados do Lote 4

- **D239**: `MotoristaAceitouViagem` (D129, evento nomeado explicitamente na decisão) nunca tinha
  sido adicionado ao catálogo de `EVENT_MAP.md` — quarta vez que essa família de gap aparece
  (D194/D196/D201/D222), agora em Produto, não em Banco. Corrigido antes de escrever o comando
  `accept`.
- **D240**: leitura completa de `RBAC_MATRIX.md` 7.12 confirmou ausência de código para
  Interromper/Retomar e para o aceite do Motorista. Perguntado ao usuário — escolhida a opção de
  reaproveitar `freight.trip.edit`, documentada como lacuna de granularidade a refinar depois.
- Duas transições da máquina de estados (`EM_DESLOCAMENTO → CARREGANDO`,
  `CARREGANDO → EM_TRANSITO`) não são alcançáveis via API neste lote — dependem de Coleta/Romaneio,
  que não têm endpoint ainda (`015-trip-deliveries.md`, seção "Fora de escopo").
- `commands/retomar` não tem um nome de evento próprio catalogado em `EVENT_MAP.md`/
  `002-VIAGEM.md` — documentado como lacuna em `018-trip-status.md`, nenhum nome inventado.
- `ocorrencias.location` é aceito no contrato mas **não tem coluna física correspondente** no
  Modelo Relacional hoje — documentado explicitamente em `017-trip-occurrences.md`, não
  silenciosamente descartado nem inventado como persistido.

## Achados do Lote 5

- **`fleet.vehicle_document` sem `.edit`**: leitura completa de `RBAC_MATRIX.md` 7.8 confirmou que
  só existem `.view`/`.create`/`.attach` para documento de veículo — mesma família de lacuna de
  granularidade já vista em D240 (Lote 4). Resolvida **por precedente direto**, sem reabrir
  `AskUserQuestion`: `PATCH /veiculos/{id}/documentos/{documentoId}` reaproveita `.attach`,
  documentado em `021-vehicle-documents.md` e `components/security.md`.
- **Seguradora/Apólice/Licenciamento fora de escopo**: `seguradoras`, `apolices_seguro_veicular` e
  `licenciamentos_veiculo` existem fisicamente (`004-frota.md`) e têm código RBAC próprio
  (`fleet.insurance_policy.*`, `fleet.vehicle_licensing.*`), mas nenhum endpoint neste lote —
  fronteira de escopo deliberada, registrada em `020-vehicles.md`, não esquecida.
- **`VehicleTechnicalSheet` combina duas tabelas físicas numa visão coesa**: `manufacturer`/
  `model`/`manufacture_year`/`category_id` vivem em `veiculos_tracionadores`, o resto em
  `fichas_tecnicas_veiculo` — a separação Identidade/Técnico/Operacional pedida é conceitual, não
  1:1 com tabela; documentado explicitamente em `components/fleet-schemas.md` para não confundir
  quem for implementar o `PATCH` do sub-recurso.
- **D248 aplicado sem exceção**: não existe `PATCH /vehicle-compositions/{id}` em lugar nenhum do
  contrato — trocar Implemento ou tipo de combinação é sempre um novo `POST` que fecha a vigência
  anterior automaticamente, mesma disciplina de `alocacoes_recurso_viagem` (D188, Lote 4).
- **Nenhuma regra de Tracking duplicada em Frota** (D250): `Vehicle.tracking_reference` é
  `readOnly`, nullable, e fica `null` neste lote — não existe ainda uma API de Rastreamento para
  referenciar; o formato exato do ponteiro é decisão adiada para quando esse lote existir.

## Achados do Lote 6

- **D259**: `EVENT_MAP.md` catalogava `OrdemServicoAprovacaoPendente` mas não a decisão de
  aprovação/reprovação em si — ao contrário dos pares já existentes para padrões análogos
  (`ContaAPagarAprovada`/`Rejeitada`, `ChecklistAprovado`/`Reprovado`). Sexta ocorrência da família
  D194/D196/D201/D222/D239. Corrigido: `OrdemServicoAprovada`/`OrdemServicoReprovada` adicionados
  antes de escrever `028-maintenance-approvals.md`.
- **Lacuna de granularidade RBAC mais ampla até agora**: `maintenance.work_order` só tem códigos
  coarse-grained, sem um por transição (ao contrário de `freight.trip`, Lote 4) — cinco comandos de
  transição (`iniciar-diagnostico`/`concluir-diagnostico`/`aguardar-peca`/`retomar-execucao`/
  `concluir`) e o `DELETE` reaproveitam `.edit`, cada um documentado individualmente. Aplicado por
  autorização explícita do usuário para este lote (mesmo princípio de D240/Lote 5), sem reabrir
  `AskUserQuestion` por caso.
- **Ambiguidade `work_order.approve_cost`/`.reject_cost` vs. `cost_approval.approve`/`.reject`**:
  dois pares de código RBAC plausíveis para a mesma decisão — usado `cost_approval.*` por mapear
  1:1 ao recurso Aprovação modelado em `028`, sobreposição registrada como imprecisão de
  granularidade da matriz, não escolhida silenciosamente.
- **Fases (Abertura/Diagnóstico/Orçamento/Aprovação/Execução/Encerramento) permaneceram
  documentais**: `dictionary/004-manutencao.md` já deixava explícito que fase é organização de
  atributos, não estado — `MaintenanceOrder` ficou como schema flat (mesma forma da tabela física),
  a divisão por fase aparece só na prosa de `026-maintenance-orders.md`, nunca como estrutura
  aninhada que pudesse ser confundida com estado novo.
- **`custo_previsto`/`custo_realizado` com RBAC de campo, não só de endpoint**: `RBAC_MATRIX.md` tem
  `maintenance.work_order.view_cost` distinto de `.view` — primeira vez neste contrato que uma
  permissão controla campos específicos de uma resposta (os dois campos de custo retornam `null`
  para quem não tem `.view_cost`, mesmo tendo `.view` da OS).
- **`Tipo de Serviço` incluído no escopo do Lote 6** (não pedido explicitamente): `tipo_servico_id`
  é `NOT NULL` para criar um Plano Preventivo — sem endpoint próprio, `029` seria inutilizável.
  Já é Reference Data plenamente especificada (Domain/Dictionary/DDL/RBAC), então incluir seu CRUD
  mínimo não é criar entidade nova — é uma leitura de escopo, sinalizada aqui para o usuário
  confirmar ou reverter.
- **Peça em Estoque/Movimentação de Estoque/Solicitação de Peça fora de escopo**: tabelas e RBAC
  (`maintenance.part_stock.*`, `.stock_movement.*`, `.part_request.*`) existem, sem endpoint —
  `stock_part_id` em `MaintenanceOrderItem` é referência sem consulta própria neste lote.
- **`origem_abertura` documentado sem nenhum endpoint de gatilho** (D256): `031-maintenance-
  triggers.md` é documentação pura — nenhum `POST /maintenance/trigger` foi criado, os quatro
  gatilhos automáticos (Preventiva/Pane/Checklist/IA) ficam reservados para consumidores de evento
  futuros, cada um dependente de um módulo que ainda não tem API própria.

## Achados do Lote 7

- **D272 — a maior reconciliação de bounded context desta sprint**: o pedido agrupou `Assinatura`/
  `Cobrança Recorrente`/`Plano` dentro de "Financeiro" (`035-recurring-billing.md`), mas
  `RBAC_MATRIX.md` §7.19 confirma que pertencem a `subscription`/`billing` — SaaS billing do
  GestorFrete cobrando a transportadora-tenant, fisicamente em `relational/001-core.md`, nunca o
  dinheiro do tenant com seus próprios clientes/fornecedores (`financial`, D261). Documento mantido
  no número pedido, mas tags/RBAC seguem o bounded context real (D215 aplicado com rigor mesmo
  quando o agrupamento do lote sugere o contrário).
- **D272-nota**: a máquina de 8 estados de `flows/001-ONBOARDING.md` ("Tenant/Assinatura") é mais
  rica que o Enum físico de `assinaturas_status_enum` (4 valores: `TRIAL`/`ATIVA`/`CANCELADA`/
  `SUSPENSA`) — quatro estados conceituais (`RASCUNHO`/`AGUARDANDO_PAGAMENTO`/`INADIMPLENTE`/
  `CANCELAMENTO_SOLICITADO`) nunca foram materializados. Por D241, `035` expõe só as transições que
  o Enum real suporta — os quatro estados extras ficam como lacuna conhecida (D242), não simulados.
- **D269**: auditoria (D200 aplicado à API) encontrou que `assinaturas.status` não tinha tabela de
  histórico — sétima ocorrência da família D194/D196/D201/D222/D239/D259. Corrigida
  `assinaturas_status_history` em `relational/001-core.md`. `TenantStatusHistory`
  (`tenants.status`) é um gap relacionado mas diferente, sinalizado e **não** corrigido (fora do
  escopo de um lote de API; pertence a uma revisão de Core/Tenancy).
- **D270**: `estornos_financeiros` — mecanismo central de D266 — nunca teve evento catalogado em
  `EVENT_MAP.md`. Oitava ocorrência da mesma família. Corrigido: `EstornoRealizado` adicionado antes
  de escrever `037-bank-reconciliation.md`.
- **D271 — primeira lacuna de seção inteira de RBAC nesta sprint**: `Plano de Contas` e `Conta
  Bancária`, ambas tabelas físicas plenamente especificadas, não tinham nenhum código — nem
  coarse-grained. Diferente de toda lacuna anterior (que sempre tinha algo na família a
  reaproveitar). Resolvido na origem, mesmo princípio de D222/D196 aplicado a `RBAC_MATRIX.md`:
  `financial.chart_of_accounts.*`, `financial.bank_account.*` e `financial.reversal.*` criados
  antes de escrever `034`/`036`/`037`.
- **D273**: o pedido usou "cancelar"/"estornar" como verbos ilustrativos para Contas a Pagar/
  Receber — nenhum dos dois é um estado real (`contas_pagar_status_enum` tem `REJEITADA`, não
  `CANCELADA`; `contas_receber_status_enum` não tem nenhum estado terminal negativo). Nomes reais
  usados nos comandos, exemplo ilustrativo do usuário corrigido contra o Enum físico — mesma
  disciplina já aplicada ao vocabulário de gatilhos no Lote 5/6.
- **Autorização por campo aparece pela segunda e terceira vez**: `financial.trip_predicted_value.
  view`/`.trip_actual_value.view`/`.trip_margin.view` (`038-financial-trip.md`) controlam três
  grupos de campos da mesma resposta — mais granular que `maintenance.work_order.view_cost` (Lote
  6, dois grupos). Padrão emergente digno de nota para Fiscal (Lote 8), que provavelmente terá a
  mesma necessidade para dados de CT-e/MDF-e.
- **`financial.payable`/`.invoice`/`.receivable` já eram fine-grained**: ao contrário de
  `maintenance.work_order` (Lote 6), a seção `financial` já tinha um código por transição de
  negócio real — só `DELETE /contas-pagar/{id}` precisou reaproveitar `.edit` (sem `.delete`
  dedicado, mesmo precedente de sempre).
- **Fatura ganhou CRUD mínimo dentro de `033`** (D260 aplicado pela segunda vez): `contas_receber.
  fatura_id NOT NULL` torna Fatura um pré-requisito bloqueante, plenamente especificado em Domain/
  Dictionary/DDL/RBAC — mesmo raciocínio do `Tipo de Serviço` no Lote 6.
- **Fora de escopo, não esquecido**: Adiantamento/Haver do Motorista (D190, RBAC existe sem
  tabela), Rateio manual (RBAC `financial.cost_allocation.create` existe, fluxo não detalhado),
  Ocorrência financeira (citada no domínio, sem endpoint), sugestão automática de correspondência
  de conciliação (sem tabela/RBAC), importação eletrônica de extrato/Open Finance.

## Achados do Lote 8

- **D283 — terceira lacuna de seção inteira de RBAC**: `Configuração Fiscal do Tenant`
  (`configuracoes_fiscais_tenant`, D110, plenamente especificada) não tinha nenhum código — mesmo
  padrão de D271 (Lote 7), agora em `documents` §7.17. Resolvido na origem antes de `045-
  configuracao-fiscal.md` depender dela, com granularidade fina (`view`/`edit`/`manage_certificate`/
  `manage_series`/`switch_environment`) alinhada ao pedido explícito do usuário.
- **D284 — gap de inconsistência entre tabelas irmãs, não de ausência total**: `flows/009-
  FISCAL.md` pede "mesmos campos padrão" para as três tabelas de histórico fiscal
  (`usuario`/`origem`/`observacao`), mas `ctes_status_history` não tinha `origem`,
  `mdfes_status_history` não tinha `usuario_id`/`origem`, e `ciots_status_history` não tinha
  nenhum dos três. Nona ocorrência da família D194–D283, primeira vez que o padrão de gap é
  "implementado de forma assimétrica entre siblings" em vez de "ausente por completo".
- **Sem `POST /ctes`, com `POST /mdfes` explícito**: CT-e nasce automaticamente do consumidor de
  `ViagemDespachada` (`freight`) — nenhum comando manual de criação no domínio. MDF-e, ao
  contrário, exige uma decisão humana (quais CT-e consolidar), então tem `POST` explícito. A
  diferença reflete o domínio real, não uma inconsistência de design.
- **`documents.cte.issue` reaproveitado quatro vezes**: `validate`/`sign`/`transmit`/`inutilize`
  não têm código próprio — `009-FISCAL.md` trata "Emissão" como uma única responsabilidade do
  Faturista. Mesmo padrão de `maintenance.work_order.edit` (Lote 6), aplicado sem nova pergunta
  por autorização explícita do usuário desde o kickoff deste lote.
- **Confirmação negativa registrada**: o usuário alertou especificamente para verificar RBAC antes
  de assumir `documents.cte.view_value`/`.view_xml`/`.view_tax` (paralelo a
  `financial.trip_*_value.view`, Lote 7). Verificado: **não existem** — `documents.cte.view` gates
  o recurso inteiro. Nenhum código de campo foi inventado; a ausência foi documentada, não
  contornada silenciosamente.
- **`INUTILIZADO` sem evento catalogado — não tratado como gap**: diferente de D194–D284 (onde o
  fluxo nomeia algo que o artefato downstream não tem), aqui o próprio `flows/009-FISCAL.md` nunca
  nomeou um evento para essa transição, junto com as outras sete. Tratado como escopo deliberado
  do Domain (correção de numeração, baixo valor de broadcast), não como lacuna a corrigir.
- **XML/certificado sempre por referência**: nenhum endpoint deste lote aceita ou retorna conteúdo
  binário — `xml_file_id`/`certificate_file_id` em todo lugar (D276/D279), incluindo o novo padrão
  `GET .../xml` que resolve a referência sem servir o arquivo (Storage ainda não tem lote próprio).
- **Fora de escopo, não esquecido**: download binário de XML/certificado (sem contrato de Storage
  ainda), emissão em modo de contingência SEFAZ, reenvio manual de Evento Fiscal específico,
  `documents.document_type.view` (RBAC existe, sem tabela física — só Enum).

## Achados do Lote 9

- **D293 — maior lacuna em número de entidades desta sprint**: `Provedor`/`Equipamento`/
  `Telemetria`/`Heartbeat` (quatro das oito entidades físicas do módulo) não tinham nenhum código
  RBAC; `Geofence` não tinha `.delete`; `SpeedLimitConfig` não tinha `.create`. Corrigido na origem
  antes de escrever `046`/`047`/`049`/`050`/`052` — auditoria pedida explicitamente pelo usuário
  antes de qualquer endpoint (D200 aplicado com máximo rigor até agora).
- **D294 — primeira autorização por subconjunto de linhas**: `eventos_rastreamento` é uma única
  tabela com `tipo` em 7 valores; a matriz já fragmentava 3 deles em códigos próprios
  (`.stop`/`.route_deviation`/`.speed_event`) antes deste lote. `051-tracking-events.md` resolve os
  4 restantes reaproveitando `.geofence.view`/`.position.view` por categoria, e a coleção é
  filtrada por linha conforme os códigos do chamador — extensão do padrão de autorização por campo
  (D267, Lote 7) para autorização por categoria de conteúdo dentro da mesma tabela.
- **Tensão RBAC-vs-instrução registrada, não escondida**: `tracking.position.create_manual` existe
  na matriz e `flows/008-RASTREAMENTO.md` descreve entrada manual de posição como funcionalidade
  real do domínio — mas `048-vehicle-positions.md` não implementa esse endpoint, por instrução
  explícita deste lote ("nunca POST"). Documentado como reservado para o lote de ingestão, não como
  lacuna ignorada.
- **Filtro `equipment_id` recusado em `051`**: `eventos_rastreamento` não tem coluna física
  `equipamento_rastreamento_id` — D226 aplicado com rigor, mesmo sendo um filtro razoável de se
  pedir; o caminho real é `position_id → 048 → equipment_id`, documentado explicitamente.
- **D250 (Lote 5) pronto para ser resolvido, não resolvido aqui**: `Vehicle.tracking_reference`
  (`components/fleet-schemas.md`) ficou `readOnly`/nulo desde o Lote 5, esperando a API de
  Rastreamento existir. Ela existe agora (`048-vehicle-positions.md`) — mas `020-vehicles.md`/
  `fleet-schemas.md` são contrato já aprovado do Lote 5, e o pedido deste lote não incluiu reabri-lo
  (diferente de D231, que foi um caso de reabertura explicitamente decidido pelo usuário). Sinalizado
  aqui para decisão explícita antes de qualquer edição — não alterado unilateralmente.
- **`origens_localizacao` exposto sem arquivo próprio**: `GET /tracking/origins` foi adicionado
  dentro de `048` (não pedido explicitamente) para dar sentido ao filtro `?origin=` de Posições —
  mesmo raciocínio de D260, aplicado a um filtro em vez de a uma FK bloqueante de escrita.
- **Fora de escopo, não esquecido**: contrato de ingestão (webhook/polling/API do Provedor/queue —
  decisão de arquitetura ainda não tomada), sugestão automática de correspondência/matching,
  qualquer integração específica por fornecedor (D291).

## Achados do Lote 10

- **D305 — a inversão mais notável desta sprint**: o pedido presumia que Checklist não estava
  formalizado; a auditoria encontrou o oposto — `flows/007-CHECKLIST.md` está completo (5 estados,
  transições, eventos, RBAC com `●` App já correto). O que falta é só a DDL, e mesmo essa lacuna
  não é mecânica: a estrutura de "Modelo de Checklist" (itens, criticidade) nunca foi detalhada em
  Domain/Dictionary — corrigir agora inventaria escopo, não traduziria uma pendência (mesmo
  critério de D206). `056-driver-checklists.md` documenta tudo isso e fica sem endpoints.
- **`docs/domain/OFFLINE_STRATEGY.md` está vazio**: pedido explícito de cruzar a seção "Permitido/
  Não permitido offline" com esse arquivo — verificado, sem conteúdo. A tabela em `060-driver-
  sync.md` foi fundamentada diretamente em `flows/010-APP_MOTORISTA.md` (D130/D133) e na coluna App
  do RBAC, não num documento inexistente. Reportado explicitamente, não presumido nem escondido.
- **D304 — duas lacunas de naturezas diferentes na mesma auditoria**: `freight.trip.edit` já era
  usado pelo Motorista desde D240 (Lote 4) mas nunca tinha o marcador `●` — não é um código
  ausente, é um *marcador* ausente, primeira vez que esse subtipo de gap aparece. Separadamente,
  `Sessão`/`Dispositivo`/`Fila de Sincronização` não tinham nenhum código — quinta ocorrência do
  padrão "seção inteira ausente". Ambos corrigidos na mesma preparação, tratados como achados
  distintos por serem, de fato, problemas diferentes.
  - Nova seção `7.27 mobile`: deliberadamente restrita a autoatendimento
    (`mobile.device.view_own`/`.edit_own`/`mobile.sync.execute`) — nenhuma ação de domínio (aceitar
    viagem, preencher ocorrência, etc.) ganhou código em `mobile`; todas continuam nos módulos
    corretos (D303), confirmando que a separação bounded-context-por-dado (não por canal/API) se
    mantém consistente mesmo no lote mais "canal-específico" da sprint.
- **Nomes de comando corrigidos contra `018-trip-status.md`**: o kickoff usou `pause`/`resume`
  como exemplos ilustrativos — os nomes reais já estabelecidos em Lote 4 são `interromper`/
  `retomar` (D216) — usados literalmente em `055-driver-trips.md`, mesma disciplina já aplicada
  a enums em Lotes 5/6/9.
- **`assinaturas_digitais` sem `POST` próprio**: confirmado que o único `documento_tipo` real hoje
  (`CANHOTO`) já nasce dentro do comando de Entrega (`058`) — `059-driver-signatures.md` ficou
  puramente leitura, exatamente como o kickoff sugeria ("preferir o comando da entrega").
- **Fora de escopo, não esquecido**: revogação administrativa de Sessão/Dispositivo (RBAC não tem
  código do lado ERP Web ainda), contrato de ingestão de Rastreamento (permanece pendente desde o
  Lote 9, `048-vehicle-positions.md`), ranking de Meu Desempenho e demais indicadores (mencionados
  no fluxo mas não pedidos como endpoint neste lote).

## Achados do Lote 11

- **D313 — maior lacuna de RBAC da sprint**: `analytics`/`reporting` e `ai` — dois bounded contexts
  inteiros, 15 entidades plenamente especificadas (D151/D161-D172) — não tinham nenhuma seção em
  `RBAC_MATRIX.md` além de códigos avulsos de relatórios pré-construídos em §7.23. Corrigido antes
  de escrever qualquer um dos 16 documentos: 28 códigos em `analytics`/`reporting` + 15 códigos numa
  seção nova `7.28 ai`. Total de permissões: 314 → **357**. Décima ocorrência da família
  D194/.../D304, e a maior em número de códigos de uma só vez.
- **Erro de ordenação/contagem autocorrigido durante a preparação**: a seção `ai` foi inicialmente
  inserida antes de `mobile` (fora de ordem posicional) e o total foi somado errado na primeira
  passagem (355 em vez de 357) — ambos detectados e corrigidos antes de qualquer revisão externa,
  por recontagem exata das linhas adicionadas (28 + 15 = 43; 314 + 43 = 357).
- **Três níveis de autorização, terceira ocorrência do nível de campo**: `ai.inference.view_cost`
  segue o mesmo padrão de `maintenance.work_order.view_cost` (Lote 6) e
  `financial.trip_*_value.view` (Lote 7) — sem a permissão, `cost` retorna `null`, nunca omitido.
- **Anomalia Detectada dobrada dentro de `075-ai-classifications.md`**: o pedido do usuário não deu
  um número de arquivo próprio a `anomalias_detectadas`, apesar de ser estruturalmente distinta de
  Classificação (D076, reconciliação já feita no Domain — Classificação rotula sob demanda,
  Anomalia é evento detectado num fluxo contínuo). Em vez de inventar um número de arquivo não
  pedido ou omitir a entidade, foi dobrada dentro de `075`, com seção e endpoints próprios
  (`/ai/anomalies`), decisão sinalizada explicitamente no próprio documento.
- **`ai.suggestion.decide`/`ai.feedback.create` reaproveitados por comando/verbo**: `accept`/
  `reject`/`ignore` de Sugestão compartilham um único código (RBAC não distingue por comando); o
  `PATCH` de `actual_result` em Feedback reaproveita `.create` (sem `.edit` dedicado) — última
  ocorrência do padrão de reaproveitamento de D240 registrada neste segmento BI+IA.
- **`EVENT_MAP.md` sem nenhum evento de IA — não é um gap D194-style**: diferente da família
  D239/.../D294 (um fluxo canônico nomeia um evento ausente), nenhum fluxo jamais nomeou um evento
  de IA, porque não existe `flows/0NN-IA.md` dedicado. Registrado como lacuna de produto a
  considerar quando/se um fluxo de IA for formalizado — não inventado.
- **`AnalyticsCube`/`AIModel` deliberadamente agnósticos de infraestrutura**: nenhum schema ou
  documento deste lote menciona ClickHouse/BigQuery/Power BI/DuckDB (cubo) nem OpenAI/Anthropic/
  Gemini/Azure (modelo de IA) — mesmo princípio de D291 (Rastreamento nunca expõe fornecedor),
  aplicado agora à infraestrutura analítica e aos provedores de IA.
- **Fora de escopo, não esquecido**: contrato de ingestão/upload que dispara uma Inferência de IA
  (permanece pendente desde o Lote 9, mesma natureza do gap de ingestão de Rastreamento), retenção/
  expiração de arquivos de Exportação no Storage, granularidade por comando em `ai.suggestion.decide`
  (`.accept`/`.reject`/`.ignore` separados).

## Achados do Lote 12

- **A auditoria D200 mais ampla da sprint**: por atravessar quase todos os módulos, encontrou
  lacunas em três camadas diferentes na mesma preparação — Domain/DDL (D323, D324), RBAC (D325) e
  EVENT_MAP (D327) — mais uma reconciliação de escopo completa (D326). Nenhum lote anterior
  acumulou tantas camadas de origem corrigidas de uma vez.
- **D323/D324 — primeira vez nesta sprint que o gap é Domain/DDL, não só RBAC**: `Notificação`/
  `Preferência de Canal` e `Arquivo` nunca existiram como entidade física, apesar de `RBAC_MATRIX.md`
  (`notification_center.*`) e `DECISIONS.md` (D024) já as anteciparem havia muitas sprints. Ao
  contrário de D294 (RBAC fragmentando uma tabela existente por categoria), aqui o gap é a ausência
  total da tabela — resolvido com o mesmo tratamento "infraestrutura transversal" já usado para
  Anexo/Comentário (D186): tabela física + decisão registrada, sem profile completo de 20 campos.
- **D324 — retrofit deliberadamente recusado**: `arquivos` agora existe, mas as ~15 colunas
  `*_arquivo_id` já espalhadas por 8 arquivos `relational/` continuam sem FK física para ela — dar
  a elas uma FK real seria uma mudança estrutural ampla em módulos já publicados, fora do escopo de
  um lote de API (mesmo princípio de "arquitetura congelada" já aplicado a D250).
- **D326 — a reconciliação mais completa da sprint**: `084-reports.md`/`085-exports.md`, pedidos
  explicitamente no kickoff como recursos novos, descreviam exatamente `068-saved-reports.md`/
  `069-exports.md` (Lote 11) — mesma tabela física, mesmo bounded context. Em vez de duplicar (duas
  superfícies `/reports`/`/exports` concorrentes) ou ignorar o pedido, os dois arquivos viraram
  documentos de reconciliação explícita (D076), apontando para os recursos já existentes.
- **D316 aplicado com uma restrição adicional que Endereço (D225) não tinha**: `anexos`/
  `comentarios.entidade_tipo` são vocabulário de texto extensível, não um Enum físico fechado como
  `enderecos_entidade_tipo_enum` — então `080`/`081` não enumeram todo dono possível (dezenas de
  entidades têm "Anexos/Comentários suportados: Sim"), documentam o padrão único e ativam
  explicitamente só Viagem, fechando a lacuna que `019-trip-timeline.md` (Lote 4) já sinalizava
  desde o início ("Comentários/Anexos: Não — sem endpoint de API neste lote").
- **`088-webhooks.md` preserva uma lacuna pedida explicitamente pelo usuário**: histórico de
  tentativas de entrega individual não tem tabela física nem endpoint — só o estado atual
  (`status`) e os eventos `WebhookEntregue`/`WebhookFalhou` (D327). Documentado como lacuna
  conhecida, não uma entidade inventada para "completar" o recurso.
- **`082`/`083` fecham o lote sem nenhum código RBAC ou tabela nova** (D328): busca global e
  Timeline são os dois únicos documentos deste lote que não tocam `RBAC_MATRIX.md` nem
  `relational/` — confirmado explicitamente, não uma omissão.
- **Fora de escopo, não esquecido**: retrofit de FK em `*_arquivo_id` existentes (D324), ativação de
  Anexo/Comentário para donos além de Viagem (mecânico, D225-style, sob demanda), histórico de
  tentativas de entrega de Webhook, upload multipart direto sem URL assinada, rotação de
  `signing_secret` via comando próprio, granularidade por tipo de evento em Preferência de Canal.

## OpenAPI Freeze — concluído ([`OPENAPI_FREEZE.md`](./OPENAPI_FREEZE.md))

Auditoria final de 16 seções (Domain → Dictionary → Relational → RBAC → Events → State Machines →
Idempotência → Paginação → Multi-Tenant → Dados Sensíveis → Storage → Read Models → Duplicações →
Lacunas Conhecidas → Métricas → Resultado), todos os números extraídos mecanicamente dos arquivos
reais, nenhuma estimativa. **Status: PASS.** Duas correções de índice aplicadas (D330 — total de
permissões RBAC 379 → 404; D331 — total de entidades 175 → 177), nenhuma delas altera o contrato.
**D329** entra em vigor a partir daqui: nenhuma mudança incompatível na API sem decisão explícita de
versionamento registrada em `DECISIONS.md`.

## Como esta pasta cresce

Todos os 12 lotes planejados (Fundação → Core/Identidade → Cadastros → Viagens → Frota →
Manutenção → Financeiro → Fiscal → Rastreamento → App Motorista → BI+IA → Recursos Transversais) e
o OpenAPI Freeze estão concluídos e aprovados. Contrato congelado. Próximo: **Sprint 11 —
Backend**, pelo Core/Identity — nenhuma mudança de contrato nesta transição, o Backend implementa
exatamente o que está congelado aqui.
