# OPENAPI_FREEZE.md — Auditoria Final de Congelamento (Sprint 10)

Documento oficial do congelamento do contrato OpenAPI do GestorFrete. Não cria endpoint, não altera
contrato, não corrige arquitetura sem decisão registrada — é uma auditoria de consistência em 5
camadas (Domain → Dictionary → Relational → RBAC → OpenAPI), seguida de 12 verificações
transversais. Toda contagem abaixo é extraída mecanicamente dos arquivos reais (`grep`/`awk`/
`@redocly/cli stats`), nunca estimada.

**Regra a partir deste documento (D329)**: após a aprovação deste Freeze, nenhuma alteração
incompatível pode ser feita nos contratos da API sem decisão explícita de versionamento registrada
em `DECISIONS.md`.

---

## Seção 1 — Cobertura de Domínio

177 entidades catalogadas (`ENTITY_CATALOG.md`, corrigido nesta auditoria de 175 → 177, D331) em 12
categorias, mapeadas para 25 prefixos de bounded context em `RBAC_MATRIX.md`. Deste total, **19
bounded contexts têm pelo menos um endpoint** na OpenAPI; **6 não têm nenhum** — confirmado por
busca literal em `components/security.md` (0 ocorrências de cada prefixo na coluna de permissão).

### Bounded contexts COM endpoint

| Bounded context | Lote(s) | Observação |
|---|---|---|
| `identity_access` | 2 | Usuários, Papéis, Permissões |
| `tenancy` | 2 | Tenant, Filial |
| `crm` | 3 | Cliente |
| `maintenance` | 3, 6 | Fornecedor; Ordem de Serviço e derivados |
| `drivers` | 3 | Motorista |
| `fleet` | 5 | Veículo, Implemento, Composição |
| `freight` | 4 | Viagem — core domain |
| `tracking` | 9 | Posição, Telemetria, Geofence |
| `documents` | 8 | CT-e, MDF-e, CIOT |
| `financial` | 7 | Contas a Pagar/Receber, Plano de Contas |
| `subscription`/`billing` | 7 | Plano, Assinatura, Cobrança Recorrente |
| `analytics`/`reporting` | 11 | Métrica, Indicador, Dashboard, Exportação |
| `ai` | 11 | Modelo, Inferência, Sugestão, Visão Computacional |
| `mobile` | 10 | Dispositivo, Sincronização (autoatendimento) |
| `storage` | 12 | Arquivo, Anexo, Comentário |
| `notification_center` | 12 | Notificação, Preferência de Canal |
| `integration` | 12 | Configuração de Integração, Webhook, Job |
| `audit`* | — | Ver nota abaixo — código existe, consumido internamente |
| `onboarding`* | — | Ver nota abaixo |

\* `audit` e `onboarding` aparecem na tabela de bounded contexts com RBAC, mas **nenhum dos dois
tem endpoint de leitura/escrita próprio** — listados aqui e detalhados na tabela "SEM endpoint"
abaixo por serem casos-limite (têm código RBAC, não têm rota).

### Bounded contexts SEM nenhum endpoint (6) — motivo de cada um

| Bounded context | Entidades/Tabelas físicas | Motivo |
|---|---|---|
| `pricing` | Tabela de Preço, Cotação, Contrato de Frete (`tabelas_preco`/`cotacoes`/`contratos_frete`, `relational/003-operacao.md`) | Consumidas por referência (FK) dentro de `freight`, nunca ganharam CRUD próprio em nenhum lote — nenhum kickoff pediu esse recurso. RBAC (`pricing.*`, 10 códigos) pré-existia a este sprint, nunca referenciado por um endpoint. |
| `routing` | Rota Padrão, Trecho, Praça de Pedágio (`relational/003-operacao.md`) | Mesmo padrão de `pricing` — referência consumida por `freight`, sem lote de CRUD próprio pedido. |
| `support` | Ticket de Suporte, Interação do Ticket, Atribuição de Consultor Comercial | Explicitamente adiado desde `domain/010-administracao.md` ("pertencem a `support`, fora dos 6 blocos pedidos... não removidas, apenas não cobertas"). Nunca reaberto. |
| `onboarding` | Sem tabela própria — fluxo consome `tenants`/`assinaturas`/`usuarios` | `RBAC_MATRIX.md` tem `onboarding.signup.create` marcado como ponto de entrada público, mas **nenhum `POST /onboarding/signup` foi construído** — `002-tenants.md` (Lote 2) só tem `GET`/`PATCH /tenant`, sempre do tenant já autenticado, nunca criação self-service. Gap real, não apenas escopo teórico — sinalizado explicitamente na Seção 14. |
| `audit` | `logs_auditoria` (`relational/010-administracao.md`, D193/D194) | Tabela física existe desde o Sprint 09, RBAC (`audit.trail.view`/`.access_log.view`/`.trail.export`) existe, mas nenhum `GET /audit-logs` foi construído em nenhum lote — o papel de Auditor não tem endpoint próprio para consultar a trilha via API ainda. |
| `platform` | Administração cross-tenant (`RBAC_MATRIX.md` §7.26) | Deliberadamente fora do produto tenant-facing — é a ferramenta interna da própria equipe GestorFrete, um front distinto (não modelado nesta OpenAPI, que é a API do produto). |

**Nenhuma das seis ausências é uma lacuna a corrigir agora** — `pricing`/`routing`/`support`/
`platform` são fronteiras de escopo já conhecidas (não pedidas em nenhum kickoff); `onboarding`/
`audit` são gaps reais, registrados na Seção 14 como "A validar" para um lote futuro.

### Entidades internas/técnicas sem endpoint (dentro de contexts que TÊM cobertura)

Nem toda entidade de um bounded context coberto precisa de endpoint — confirmado, não uma omissão:

| Entidade/Tabela | Natureza | Motivo |
|---|---|---|
| `logs_auditoria` | Histórica, técnica | Ver `audit` acima |
| `eventos_fiscais` | Time Series técnica | Só leitura (`044`), nunca escrita — é log de integração, não recurso de negócio |
| `heartbeats` | Time Series técnica | Só leitura (`050`), sinal técnico |
| `execucoes_job` | Histórica, técnica | Só leitura + trigger restrito (`089`) |
| `inferencias_ia` | Log técnico | Só leitura (`072`) |
| Checklist (`checklists`/`itens_checklist`) | — | **Não existe fisicamente** — D305 (Lote 10): Domain/Flow completos, DDL nunca traduzida, decisão deliberada de não inventar estrutura |
| Peça em Estoque/Movimentação de Estoque/Solicitação de Peça | Master/Transactional | RBAC existe, sem endpoint (Lote 6, "fora de escopo") |
| Seguradora/Apólice/Licenciamento de Veículo | Master Data | RBAC existe, sem endpoint (Lote 5, "fora de escopo") |
| Adiantamento/Haver do Motorista | Transactional | RBAC existe, sem tabela física ainda (D190) |
| Pneu/Recapagem/Posicionamento | Master/Transactional | Fluxo próprio nunca convertido em API (Lote 6, "fora de escopo") |

---

## Seção 2 — Cobertura do Dictionary

**Metodologia**: cada um dos 12 lotes aplicou D200 antes de fechar qualquer schema — o processo
usado consistentemente foi ler o Data Dictionary Funcional real (nunca de memória) e transcrever
nome/obrigatoriedade/tipo/enum exatamente, nunca inventar um atributo. Esta seção consolida essa
disciplina, não a refaz campo a campo (117 schemas, centenas de campos) — verificação de ponta a
ponta já ocorreu lote a lote (rastro completo em `DECISIONS.md` D216–D328); aqui a auditoria faz
verificação estrutural do conjunto inteiro + amostragem dirigida aos pontos de maior risco.

### Verificações mecânicas (100% dos 117 schemas)

| Verificação | Resultado |
|---|---|
| `nullable: true` em `openapi.yaml` (inválido em OpenAPI 3.1/JSON Schema 2020-12) | **0 ocorrências** — PASS. Convenção mantida em todo o sprint: `nullable` só aparece nos `.md` de prosa, nunca no YAML executável (nullability expressa por ausência em `required`) |
| Schemas duplicados (mesmo nome, duas definições colidindo) | **0** — PASS |
| Campo `tenant_id` exposto como propriedade editável em algum schema | **0** — PASS (Seção 9 detalha) |

### Regras de tradução aplicadas consistentemente (auditadas por amostragem)

- **Snapshot vs. Referência (D243)**: todo schema com par referência/snapshot (`Trip.motorista_id`
  vs. `Trip.motorista_nome_snapshot`, `AnalyticalSnapshot.participating_metrics`,
  `Export.metric_versions`) marca o snapshot como `readOnly`, nunca aceito em `POST`/`PATCH`.
- **Campo derivado nunca é input (D217)**: custo realizado (OS), saldo (Conta Bancária), margem
  (Viagem), `version`/`hash` (File) — todos `readOnly`, calculados pela aplicação.
- **Enum corrigido contra a fonte real, nunca a ilustração do pedido**: `pause`/`resume` (kickoff
  Lote 10) → `interromper`/`retomar` (`018-trip-status.md` real); "cancelar"/"estornar" (kickoff
  Lote 7) → `REJEITADA`/Estorno (Enum físico real, D273); unidades de trigger preventivo
  corrigidas contra o Enum físico (Lote 5/6).
- **Campo aceito mas sinalizado como sem coluna física, nunca inventado silenciosamente**:
  `ocorrencias.location` (`017-trip-occurrences.md`, Lote 4) — único caso identificado onde um
  campo do schema não tem coluna física ainda; documentado explicitamente na época, continua
  documentado, não silenciosamente "resolvido" nesta auditoria (resolver exigiria uma decisão de
  Domain/DDL nova, fora do escopo do Freeze).

**Resultado**: nenhum schema inventa atributo inexistente no Dictionary. PASS.

---

## Seção 3 — Cobertura Relacional

**Metodologia**: mesma disciplina — cada lote comparou API Resource → Entity → Tabela antes de
fechar o documento (D200 aplicado à camada física em todos os 12 lotes, não só nos 9 do Sprint 09).
Consolidação abaixo.

| Verificação | Resultado |
|---|---|
| Conteúdo binário/base64 em algum schema de negócio | **0 ocorrências** de `base64`/`binary`/`blob` em `openapi.yaml` — PASS (D107 preservado em toda a API) |
| Campos de referência a arquivo (`*_file_id`) | 43 ocorrências, 12 nomes distintos (`file_id`, `xml_file_id`, `credential_file_id`, `signature_file_id`, `certificate_file_id`, `source_file_id`, `previous_file_id`, `photo_file_id`, `evidence_file_id`, `payload_file_id`, etc.) — todos UUID de referência lógica, nunca binário embutido |
| `DELETE` sem código RBAC correspondente construído mesmo assim | **0** — todo `DELETE` documentado tem o código RBAC citado explicitamente (`.delete`/`.delete_own`, ou reaproveitamento registrado, ex. `.edit`/`.attach`) |
| Status aceito pelo endpoint sem suporte no Enum físico | **0 identificado** — toda transição documentada foi checada contra o `_status_enum` real na época de construção (ex.: Assinatura expõe só os 4 estados reais do Enum físico, não os 8 conceituais do fluxo, D241/D272-nota) |
| FK referenciada em `requestBody` sem tabela de destino existente | **0 identificado** — toda FK aceita em corpo de request (`metric_id`, `cube_id`, `saved_report_id`, `credential_file_id`, etc.) resolve contra uma tabela já materializada nesta sprint |

### Pontos de atenção já registrados (não são bugs, são decisões)

- **`arquivo_id` sem FK física** (D107/D324): por design — Storage é MinIO/S3, não Postgres; as
  colunas `*_arquivo_id` das ~15 tabelas que os referenciam continuam sem `REFERENCES arquivos(id)`
  — decisão explícita, não uma omissão a corrigir no Freeze.
- **`Vehicle.tracking_reference`** (D250, Lote 5): `readOnly`/nulo — a API de Rastreamento existe
  desde o Lote 9, mas `020-vehicles.md`/`fleet-schemas.md` (contrato já aprovado do Lote 5) não
  foram reabertos para preenchê-lo. Sinalizado, não corrigido — reabrir contrato aprovado exige
  decisão explícita do usuário (mesma disciplina de "arquitetura congelada"), não uma correção de
  Freeze.

**Resultado**: PASS, com os dois pontos acima citados na Seção 14 como lacunas conhecidas.

---

## Seção 4 — Cobertura RBAC

**A camada mais auditável mecanicamente** — `components/security.md` tem uma linha por par
Endpoint/Método desde o Lote 2.

### Números reais (recontados nesta auditoria, não de memória)

| Métrica | Valor |
|---|---|
| Linhas na tabela de mapeamento (`security.md`) | **363** |
| Códigos RBAC definidos em `RBAC_MATRIX.md` (recontados por script) | **404** (corrigido de 379 nesta auditoria — D330; a divergência era de contagem, não de conteúdo) |
| Bounded contexts com RBAC definido | 25 |
| Bounded contexts com pelo menos 1 endpoint usando seu RBAC | 19 |

### Classificação de autorização — toda linha tem um dos três rótulos, nenhuma omissa

| Rótulo | Endpoints | Exemplos |
|---|---|---|
| **PUBLIC** (sem `bearerAuth`) | 6 | `POST /auth/login`, `/auth/refresh`, `/auth/forgot-password`, `/auth/reset-password`, `/mobile/auth/login`, `/mobile/auth/refresh` |
| **AUTHENTICATED** (`bearerAuth`, sem RBAC além da sessão) | 4 | `POST /auth/logout`, `GET /auth/me`, `POST /mobile/auth/logout`, `GET /mobile/auth/me` |
| **RBAC delegado** (sem código próprio, herda a autorização de cada recurso consultado) | 1 | `GET /search` (D317) |
| **RBAC** (código(s) próprio(s) exigido(s)) | 352 | Todo o restante |

**Zero linhas sem classificação** — confirmado por leitura completa da tabela: toda linha tem
"Nenhuma (pré-autenticação)"/"Nenhuma além de autenticado" ou um código `bounded_context.recurso.
verbo` explícito. PASS no critério "todo endpoint indica PUBLIC/AUTHENTICATED/RBAC".

### Verificações de qualidade do RBAC

| Verificação | Resultado |
|---|---|
| Código citado existe de fato em `RBAC_MATRIX.md` | Verificado incrementalmente a cada lote (D216 — nunca inventado no documento da API); nenhuma divergência encontrada nesta consolidação |
| Código no bounded context correto | Verificado — achado notável: `Assinatura`/`Cobrança Recorrente`/`Plano` usam `subscription`/`billing`, não `financial`, apesar do agrupamento temático do Lote 7 sugerir o contrário (D272) |
| Campo sensível com autorização própria quando existe | 3 ocorrências de autorização por campo: `maintenance.work_order.view_cost` (Lote 6), `financial.trip_predicted_value.view`/`.trip_actual_value.view`/`.trip_margin.view` (Lote 7, 3 campos), `ai.inference.view_cost` (Lote 11) |
| Row-level/subconjunto quando necessário | `tracking.stop.view`/`.route_deviation.view`/`.speed_event.view`/`.geofence.view`/`.position.view` fragmentam `eventos_rastreamento` por categoria (D294, Lote 9) — única ocorrência deste padrão, correta e suficiente para o caso real |
| Mobile ganhou permissão de domínio nova (não deveria) | **0** — `mobile.*` tem só 3 códigos, todos de autoatendimento de infraestrutura (`device.view_own`/`.edit_own`/`sync.execute`); toda ação de domínio do Motorista reaproveita o código do módulo dono (D303, confirmado nos 12 lotes) |
| Endpoint administrativo liberado a usuário comum inadvertidamente | **0** — `integration.job.trigger` é o único comando de efeito amplo do sprint, e tem Aprovação (Administrador Empresa) explícita (D322); `platform.*` (cross-tenant) não tem nenhum endpoint construído (Seção 1), então não há superfície administrativa exposta a auditar aqui |

**Resultado**: PASS, após a correção de contagem D330 (nenhuma mudança de permissão, só de número
reportado).

---

## Seção 5 — Cobertura de Eventos

### Metodologia

Todo comando (`POST .../commands/*` ou criação que gera evento) foi checado contra `EVENT_MAP.md`
em tempo de construção — 11 achados desta família ao longo do sprint (D194/D196/D201/D222/D239/
D259/D270/D283-adjacente/D293-adjacente/D313-negativo/D327), cada um registrado e corrigido na
origem antes do endpoint ser fechado.

### Eventos no catálogo

| Métrica | Valor |
|---|---|
| Eventos distintos catalogados em `EVENT_MAP.md` | **87** |
| Seções de bounded context publicador | 10 (`freight`, `documents`, `financial`, `maintenance`, `tracking`, `mobile`, `drivers`, `billing`/`subscription`, `tenancy`, `integration` — mais o consumidor transversal `audit`) |

### Lacunas de evento conhecidas e deliberadamente não preenchidas

| Lacuna | Motivo de não corrigir |
|---|---|
| Decisão de Sugestão de IA (`aceitar`/`rejeitar`/`ignorar`) sem evento catalogado | Nenhum `flows/0NN-IA.md` existe — não há fluxo canônico que já tenha nomeado o evento (diferente da família D239, onde o fluxo nomeia e o catálogo não capturou); registrado como lacuna de produto (D313) |
| `commands/retomar` (Viagem) sem nome de evento próprio | `018-trip-status.md` documenta a lacuna desde o Lote 4 — nenhum nome inventado |
| `INUTILIZADO` (CT-e) sem evento catalogado | O próprio `flows/009-FISCAL.md` nunca nomeou esse evento — escopo deliberado do Domain (Lote 8) |
| Histórico de tentativas de entrega de Webhook | `WebhookEntregue`/`WebhookFalhou` existem (D327, catalogados nesta sprint) mas não há endpoint para consultá-los diretamente (`088-webhooks.md`) — lacuna documentada, não inventada |

### Verificação — nenhum endpoint publica Domain Event manualmente

Confirmado por leitura de toda a superfície de comandos: nenhum `POST` aceita um campo tipo
`event_name`/`event_payload` livre — todo evento é sempre um efeito colateral do comando de
domínio, nunca uma publicação direta pelo cliente HTTP (D236).

**Resultado**: PASS — cobertura de eventos consistente, lacunas conhecidas listadas na Seção 14.

---

## Seção 6 — Máquinas de Estado

Toda transição documentada foi checada contra o Enum físico e o fluxo canônico na época de
construção — nenhuma transição na API existe sem uma correspondente no Domain (D235: transição
inválida para o estado atual é sempre `409`, nunca uma tentativa silenciosamente aceita).

| Agregado | Dimensões/Estados | Documento canônico | Comandos expostos |
|---|---|---|---|
| **Viagem — Operacional** | 11 estados (`RASCUNHO`→...→`CANCELADA`) | `flows/002-VIAGEM.md`, `018-trip-status.md` | `dispatch`/`start`/`finish`/`interromper`/`retomar`/`cancelar`/`close-administrative` + `accept` (Motorista) |
| **Viagem — Fiscal** | 5 estados | `002-VIAGEM.md` | Derivado dos comandos de `039-cte.md`/`040-mdfe.md`, nunca um comando próprio na Viagem |
| **Viagem — Financeiro** | 4 estados | `002-VIAGEM.md` | Derivado de `032`/`033`, nunca um comando próprio na Viagem |
| **Ordem de Serviço** | Coarse-grained (`.edit` reaproveitado, D253) | `flows/003-MANUTENCAO.md`, `026-maintenance-orders.md` | `iniciar-diagnostico`/`concluir-diagnostico`/`aguardar-peca`/`retomar-execucao`/`concluir`/`fechar`/`cancelar` |
| **CT-e** | 8 estados | `flows/009-FISCAL.md`, `039-cte.md` | `validate`/`sign`/`transmit`/`cancel`/`inutilize` |
| **MDF-e** | Consolida CT-e `AUTORIZADO` | `040-mdfe.md` | `close`/`cancel` |
| **CIOT** | — | `041-ciot.md` | `register`/`cancel` |
| **Contas a Pagar** | 4 estados reais (não `CANCELADA`, D273) | `032-accounts-payable.md` | `approve`/`reject`/`pay` |
| **Contas a Receber** | Sem terminal negativo próprio — correção via Estorno | `033-accounts-receivable.md` | `confirm-receipt` |
| **Assinatura** | 4 estados físicos (`TRIAL`/`ATIVA`/`CANCELADA`/`SUSPENSA`) vs. 8 conceituais no fluxo | `035-recurring-billing.md`, D241/D272-nota | `upgrade`/`downgrade`/`cancel`/`reactivate` |
| **Sugestão de IA** | 5 estados (`PENDENTE`/`ACEITA`/`REJEITADA`/`IGNORADA`/`EXPIRADA`) | `073-ai-suggestions.md` | `accept`/`reject`/`ignore` |
| **Leitura de Visão Computacional** | 3 estados (`PROCESSADA`/`CONFIRMADA`/`REJEITADA`) | `076-computer-vision.md` | `confirm`/`reject` |
| **Anomalia Detectada** | 3 estados (`ABERTA`/`INVESTIGADA`/`DESCARTADA`) | `075-ai-classifications.md` | `review` |
| **Export (Exportação)** | 3 estados (`PROCESSANDO`/`CONCLUIDA`/`FALHOU`) | `069-exports.md` | Nenhum — transição interna, assíncrona |
| **Analytical Snapshot** | 3 estados (`EM_PROCESSAMENTO`/`CONSOLIDADO`/`INVALIDO`) | `064-analytical-snapshots.md` | `POST` só inicia; resto interno |
| **Webhook** | 3 estados (`ATIVO`/`INATIVO`/`SUSPENSO`) | `088-webhooks.md` | `activate`/`suspend` |
| **IntegrationConfig** | 3 estados (`ATIVA`/`INATIVA`/`COM_ERRO`) | `087-integrations.md` | `enable`/`disable` (`COM_ERRO` só derivado) |
| **Notification** | 2 estados (`NAO_LIDA`/`LIDA`) | `086-notifications.md` | `mark-read` |

**Verificação-chave**: nenhuma transição documentada em qualquer um dos 12 lotes existe sem
correspondência no Enum físico real — cada divergência encontrada durante a construção (Assinatura
D241, Contas a Pagar/Receber D273, comandos ilustrativos do kickoff D216) foi corrigida contra a
fonte real antes do endpoint ser fechado, nunca depois.

**Resultado**: PASS.

---

## Seção 7 — Idempotência

### Idempotency-Key (header HTTP, `components/parameters.md#/IdempotencyKeyHeader`)

11 operações — todas as que criam efeito financeiro/operacional relevante ou são passíveis de
retry de rede:

| Endpoint | Método | Motivo |
|---|---|---|
| `/viagens` | `POST` | Criação de Viagem — retry não pode duplicar |
| `/viagens/{id}/commands/finish` | `POST` | Encerramento — efeito amplo (dispara fiscal/financeiro) |
| `/viagens/{id}/commands/interromper` | `POST` | Muda estado operacional |
| `/viagens/{id}/commands/cancelar` | `POST` | Efeito terminal |
| `/viagens/{id}/entregas/{entregaId}/canhoto` | `POST` | Registro de comprovante — nunca duplicado |
| `/viagens/{id}/commands/reallocate-resources` | `POST` | Pacote atômico (D188) |
| `/viagens/{id}/occurrences` | `POST` | Registro de ocorrência |
| `/analytics/snapshots` | `POST` | D211 — consolidar o mesmo período duas vezes não pode gerar dois snapshots |
| `/reporting/exports` | `POST` | D211/D307 — evita duas exportações idênticas |
| `/ai/suggestions/{id}/commands/accept` | `POST` | Decisão de IA — recomendado |
| `/jobs/commands/trigger` | `POST` | D211 — evita disparo duplicado por retry |

### Idempotência de domínio (D111 — chave funcional distinta do `Idempotency-Key` HTTP)

| Fluxo | Chave de idempotência | Onde |
|---|---|---|
| CT-e / MDF-e | `protocolo_sefaz` | `039-cte.md`/`040-mdfe.md` |
| CIOT | `protocolo_antt` (`codigo_antt`) | `041-ciot.md` |
| Sincronização Mobile | `identificador_local_unico`/`sequencia_local` | `060-driver-sync.md` (D298) |
| Webhook (entrega ao consumidor do tenant) | `event_id` por tentativa | `domain/010-administracao.md` (D111), consumido pelo endpoint externo do tenant, não por esta API |

**Resultado**: PASS — toda operação crítica identificada tem uma chave de idempotência definida, HTTP
ou de domínio, nunca dependendo só do UUID interno (D111).

---

## Seção 8 — Paginação

Classificação decidida pela Categoria Física de `TABLES.md` (`PAGINATION.md`, D191): Master Data/
Transactional → offset; Time Series/History/alto volume → cursor. Nenhum endpoint inventou um
esquema de paginação próprio — confirmado, toda coleção usa `PageParam`/`LimitParam`
(`components/parameters.md`) ou o par `cursor`/`next_cursor`.

| Tipo | Contagem | Uso |
|---|---|---|
| Offset (`PageParam`) | 62 ocorrências | Cadastros, configurações, relatórios, coleções Master Data/Transactional |
| Cursor (`name: cursor` + `next_cursor`) | 15 endpoints | Ver lista abaixo |

### Os 15 endpoints cursor-paginados

`/ai/inferences`, `/ciots/{id}/status-history`, `/contas-bancarias/{id}/extrato`,
`/ctes/{id}/status-history`, `/fiscal/events`, `/jobs`, `/mdfes/{id}/status-history`,
`/ordens-servico/{id}/historico-status`, `/tracking/equipment/{id}/heartbeats`,
`/tracking/events`, `/vehicles/{vehicleId}/tracking/history`,
`/vehicles/{vehicleId}/tracking/positions`, `/vehicles/{vehicleId}/tracking/telemetry`,
`/veiculos/{id}/odometro/leituras`, `/viagens/{id}/timeline`.

Todos são Time Series, Histórico (`*_status_history`), ou log técnico de alto volume — nenhuma
coleção Master Data/Transactional usa cursor, nenhuma coleção Time Series/Histórica usa offset.

**Resultado**: PASS.

---

## Seção 9 — Multi-Tenant

| Verificação | Resultado |
|---|---|
| Parâmetro de path/query chamado `tenant_id` em qualquer endpoint | **0** |
| Propriedade `tenant_id` aceita em qualquer `requestBody` | **0** |
| Header customizado de tenant (`X-Tenant-Id` ou similar) | **0** — `bearerAuth`/`apiKeyAuth` são os únicos mecanismos, tenant sempre resolvido do contexto autenticado (D208/D218) |
| `GET /auth/me` retorna o tenant do contexto | Sim — só como **saída** (`TenantContext`, `readOnly`), nunca como entrada |

### Exceção cross-tenant

`RBAC_MATRIX.md` §7.26 (`platform.*`) é a única seção desenhada para acesso cross-tenant
(`platform.cross_tenant_access.grant`, criticidade Crítica, Aprovação Administrador SaaS) — mas,
confirmado na Seção 1, **nenhum endpoint deste bounded context foi construído** nesta sprint. Não
há, portanto, nenhuma exceção cross-tenant ativa na superfície atual da API — quando o admin
tooling da plataforma for modelado, ele herda essa permissão já reservada.

**Resultado**: PASS — nenhum endpoint permite escolher outro tenant, em nenhuma camada da requisição.

---

## Seção 10 — Dados Sensíveis

### Autorização por campo (3 ocorrências, todas já mapeadas na Seção 4)

| Campo | Permissão | Endpoint |
|---|---|---|
| `predicted_cost`/`actual_cost` (OS) | `maintenance.work_order.view_cost` | `026-maintenance-orders.md` |
| Valores previsto/realizado/margem da Viagem | `financial.trip_predicted_value.view`/`.trip_actual_value.view`/`.trip_margin.view` | `038-financial-trip.md` |
| `cost` (Inferência de IA) | `ai.inference.view_cost` | `072-ai-inferences.md` |

### Segredos — nunca retornados em texto claro após a criação

| Segredo | Tratamento |
|---|---|
| `signing_secret` (Webhook) | Só na resposta do `POST` de criação, nunca reexibido (`088-webhooks.md`) |
| `credential_file_id` (Integração) | Sempre referência a Storage, nunca texto claro (`087-integrations.md`) |
| `certificate_file_id` (Fiscal) | D279, mesma disciplina desde o Lote 8 |
| `token_hash`/senha | Nunca expostos por nenhum schema (herdado do Lote 2) |

### Dados classificados (LGPD/Confidencial no Dictionary) expostos por algum endpoint

CPF/CNPJ (`Motorista`/`Cliente`/`Tenant`), localização/telemetria (`tracking.*`, gated por
`.position.view`/`.telemetry.view`), dados fiscais (`documents.*.view` gates o recurso inteiro —
**sem** autorização por campo dentro de CT-e/MDF-e/CIOT, confirmado explicitamente no Lote 8, não
uma omissão).

**Resultado**: PASS — todo campo identificado como sensível tem autorização de recurso, e os três
casos que precisam de granularidade adicional já têm autorização de campo própria.

---

## Seção 11 — Storage

| Verificação | Resultado |
|---|---|
| Campos `base64`/`binary`/`blob` em qualquer schema | **0** |
| Campos `*_file_id` (referência lógica ao Storage) | 43 ocorrências, 12 nomes distintos |
| Endpoint que serve o binário diretamente (stream) | **0** — leitura é sempre via `078-storage.md`'s `download-url` (URL assinada temporária) |
| Metadado de arquivo sem tabela física | **0** — `File`/`arquivos` criada nesta sprint (D324) fecha o único gap identificado |

**Resultado**: PASS — API → `arquivo_id`/`file_id` → Storage, nunca API → binário, em toda a
superfície.

---

## Seção 12 — Read Models

Endpoints exclusivamente de leitura de projeção, sem nenhum comando de escrita:

| Read Model | Endpoint | Fonte |
|---|---|---|
| Disponibilidade de Veículo | `025-vehicle-availability.md` | Composta, sem tabela própria (D247) |
| Timeline Universal (Viagem) | `019-trip-timeline.md` | Anexos+Comentários+histórico+eventos (D187/D318) |
| Histórico de Rastreamento | `053-tracking-history.md` | Posição+Telemetria+Evento (D290) |
| Financeiro da Viagem | `038-financial-trip.md` | Viagem continua dona dos valores (D262) |
| Indicador Consolidado | `063-consolidated-indicators.md` | Zero verbo de escrita, confirmado por RBAC |
| Evento Fiscal | `044-eventos-fiscais.md` | Log técnico, só leitura |
| Inferência de IA | `072-ai-inferences.md` | Log técnico, só leitura |
| Predição de IA | `074-ai-predictions.md` | Nasce de Inferência, só leitura |

**Nota de precisão**: `Dashboard` (`066-dashboards.md`) **não** é um read model puro — tem
`POST`/`PATCH`/`DELETE`/`commands/share` para sua própria *configuração* (layout, widgets,
compartilhamento). O read model real é o **valor** exibido (Indicador Consolidado/Métrica), que o
Dashboard só referencia (`metric_id`/`indicator_id`), nunca armazena (D152) — distinção
explicitada aqui para não confundir "Dashboard é read model" com a realidade (Dashboard é
configuração; o dado que ele mostra é que é read model).

**Resultado**: PASS — nenhum dos read models puros listados tem comando de escrita indevido.

---

## Seção 13 — Duplicações

### Verificação mecânica (100% dos 257 paths, 117 schemas, 90 tags)

| Verificação | Resultado |
|---|---|
| Dois endpoints com a mesma `path` | **0** |
| Dois schemas com o mesmo nome | **0** |
| Duas tags com o mesmo nome | **0** |

### Duplicação semântica — encontrada e reconciliada durante o próprio Lote 12

`084-reports.md`/`085-exports.md` descreviam, quase literalmente, o mesmo recurso já construído em
`068-saved-reports.md`/`069-exports.md` (Lote 11) — reconciliado via D076/D326 **antes** de qualquer
endpoint duplicado chegar ao `openapi.yaml`. Esta é a única duplicação real encontrada em todo o
sprint; nenhuma nova foi descoberta nesta auditoria de Freeze.

### Semelhanças verificadas e confirmadas como NÃO-duplicação

| Par | Por que não são a mesma coisa |
|---|---|
| `analytics.*_report.view` (relatórios pré-construídos) vs. `reporting.saved_report.*` (sistema flexível) | Superfícies deliberadamente diferentes — uma é canônica/fixa, outra é configurável pelo usuário (D313) |
| `019-trip-timeline.md` vs. `030-maintenance-history.md` | Timeline Universal (composta, multi-fonte) vs. histórico operacional puro de status (D241) |
| `maintenance.work_order.approve_cost`/`.reject_cost` vs. `cost_approval.approve`/`.reject` | Ambiguidade de granularidade da matriz, já registrada no Lote 6 como imprecisão a refinar — não uma duplicação de recurso, os dois pares nunca são usados ao mesmo tempo no mesmo endpoint |
| `storage.attachment.*` vs. `storage.file.*` | Anexo é o **vínculo** entidade↔arquivo; File é o **metadado** do arquivo em si (D315/D316) — complementares, não sobrepostos |

**Resultado**: PASS — uma duplicação real existia (084/085), já reconciliada antes do freeze;
nenhuma nova encontrada.

---

## Seção 14 — Lacunas Conhecidas

| # | Lacuna | Status | Documento origem | Impacto | Implementar agora |
|---|---|---|---|---|---|
| 1 | `POST /onboarding/signup` (cadastro self-service de novo Tenant) | A validar | `002-tenants.md`, `RBAC_MATRIX.md` §7.20 | Alto — sem ele, não há caminho de aquisição self-service via API | Não |
| 2 | `GET /audit-logs` (consulta da trilha de auditoria via API) | Futuro | `relational/010-administracao.md`, RBAC §7.21 | Médio — trilha existe e é populada, só não é consultável via API ainda | Não |
| 3 | CRUD de `pricing` (Tabela de Preço/Cotação/Contrato de Frete) | Fora de escopo | `relational/003-operacao.md` | Baixo — consumido por FK dentro de `freight`, nunca pedido como lote próprio | Não |
| 4 | CRUD de `routing` (Rota Padrão/Trecho/Praça de Pedágio) | Fora de escopo | `relational/003-operacao.md` | Baixo — idem | Não |
| 5 | `support` (Ticket de Suporte) | Fora de escopo | `domain/010-administracao.md` (D076) | Baixo — adiado desde a concepção do módulo | Não |
| 6 | Administração da Plataforma (`platform.*`, cross-tenant) | Fora de escopo | `RBAC_MATRIX.md` §7.26 | N/A — produto interno distinto, não desta OpenAPI | Não |
| 7 | Checklist de Execução (`checklists`/`itens_checklist`) | A validar | D305, Lote 10 | Médio — Fluxo/RBAC completos, estrutura de "Modelo de Checklist" nunca detalhada | Não |
| 8 | Ingestão de Rastreamento (posição manual, webhook/polling de provedor) | Futuro | D286/D291, Lote 9 | Médio — contrato de arquitetura de ingestão ainda não decidido | Não |
| 9 | Histórico de tentativas de entrega de Webhook | Futuro | `088-webhooks.md` | Baixo — só o estado atual é consultável, não o histórico individual | Não |
| 10 | Adiantamento/Haver do Motorista | Fora de escopo | D190 | Baixo — RBAC existe, sem tabela física | Não |
| 11 | Pneu/Recapagem/Posicionamento (fluxo de pneus) | Fora de escopo | Lote 6 | Baixo — fluxo próprio nunca convertido em API | Não |
| 12 | Peça em Estoque/Movimentação de Estoque/Solicitação de Peça | Fora de escopo | Lote 6 | Baixo — RBAC existe, sem endpoint | Não |
| 13 | Seguradora/Apólice/Licenciamento de Veículo | Fora de escopo | Lote 5 | Baixo — RBAC existe, sem endpoint | Não |
| 14 | `Vehicle.tracking_reference` nunca preenchido | A validar | D250, Lote 5/9 | Baixo — API de Tracking existe desde o Lote 9, `020-vehicles.md` não foi reaberto | Não |
| 15 | Retrofit de FK em `*_arquivo_id` existentes (~15 colunas) | Fora de escopo (decisão deliberada) | D324 | Baixo — referência lógica continua suficiente | Não |
| 16 | Evento de decisão de Sugestão de IA não catalogado | A validar | D313 | Baixo — não há `flows/0NN-IA.md` ainda para nomear o evento corretamente | Não |
| 17 | Rotação de `signing_secret` de Webhook via comando próprio | Futuro | `088-webhooks.md` | Baixo — hoje só recriando o webhook | Não |
| 18 | Contrato de upload multipart direto (sem URL assinada) | Futuro | `078-storage.md` | Baixo — URL assinada já cobre o caso principal | Não |
| 19 | Granularidade por comando em `ai.suggestion.decide` | Futuro | Lote 11 | Baixo — hoje um único código cobre `accept`/`reject`/`ignore` | Não |
| 20 | Ativação de Anexo/Comentário para donos além de Viagem | Futuro (mecânico) | `080`/`081`, D316 | Baixo — padrão já documentado, replicação é direta quando pedida | Não |

Nenhuma das 20 lacunas acima será implementada como parte deste Freeze — listadas para que a
transição ao Backend comece com escopo honesto, não silencioso.

---

## Seção 15 — Métricas do Freeze

Todos os números abaixo foram extraídos mecanicamente (`@redocly/cli stats`, `grep`/`awk` sobre os
arquivos reais) em 2026-07-31 — nenhuma estimativa.

| Métrica | Valor |
|---|---|
| Endpoints (paths distintos) | **257** |
| Operações (path × método) | **380** (179 `GET`, 128 `POST`, 47 `PATCH`, 26 `DELETE`) |
| Schemas (`components/schemas`) | **117** |
| Security Schemes | **2** (`bearerAuth`, `apiKeyAuth` — este último declarado para a futura API Pública, ainda sem uso, D213-adjacente) |
| Permissões RBAC (`RBAC_MATRIX.md`, recontadas — D330) | **404** |
| Bounded contexts com RBAC definido | **25** |
| Bounded contexts com pelo menos 1 endpoint | **19** |
| Entidades de Domain catalogadas (`ENTITY_CATALOG.md`, corrigido — D331) | **177** |
| Eventos referenciados (`EVENT_MAP.md`) | **87** |
| Endpoints públicos (sem `bearerAuth`) | **6** |
| Endpoints autenticados sem RBAC além da sessão | **4** |
| Endpoints com RBAC próprio | **352** |
| Endpoints com RBAC delegado (busca) | **1** |
| Endpoints idempotentes (`Idempotency-Key`) | **11** |
| Endpoints paginados — offset | **62** |
| Endpoints paginados — cursor | **15** |
| Tags | **90** |
| Lotes concluídos | **12** (Fundação → Recursos Transversais) |
| Decisões registradas (`DECISIONS.md`) | **331** (D001–D331) |
| Erros de lint (`@redocly/cli lint`) | **0** |
| Warnings de lint | **386** (`operationId` ausente — gap conhecido e aceito desde o Lote 2, nunca bloqueante) |

---

## Seção 16 — Resultado

```
Domain ↔ API              PASS
Dictionary ↔ API          PASS
Relational ↔ API          PASS
RBAC ↔ API                PASS  (correção de contagem aplicada, D330 — sem mudança de contrato)
Events ↔ API              PASS
State Machines ↔ API      PASS
Multi-Tenant ↔ API        PASS
Storage ↔ API             PASS
Read Models                PASS
Duplications                PASS  (1 duplicação real, já reconciliada no Lote 12, D326)
Known Gaps                  DOCUMENTED (20 itens, nenhum bloqueante, nenhum implementado agora)
OpenAPI 3.1 Validation      PASS  (0 erros, 386 warnings aceitos)
```

## OPENAPI FREEZE STATUS: **PASS**

Duas correções de índice/contagem foram aplicadas como parte desta auditoria (D330 — total de
permissões RBAC, 379 → 404; D331 — total de entidades, 175 → 177) — nenhuma delas altera o
contrato da API, ambas são correções de documentos de suporte (`RBAC_MATRIX.md`/
`ENTITY_CATALOG.md`) que haviam ficado dessincronizados de sua própria fonte real. Nenhum endpoint,
schema, permissão ou evento foi criado, removido ou alterado por este documento.

A partir da aprovação deste Freeze, **D329** entra em vigor: nenhuma alteração incompatível pode
ser feita em `docs/api/openapi.yaml` (ou nos documentos que o alimentam) sem uma decisão explícita
de versionamento registrada em `DECISIONS.md`.

## Próximo passo

**Sprint 11 — Backend**, iniciando pelo Core/Identity, conforme a sequência acordada. Nenhuma
mudança de contrato será feita nesta transição — o Backend implementa exatamente o que está
congelado aqui.
