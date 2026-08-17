# INDEXES.md — Catálogo de Índices do Modelo Relacional

Todo índice físico dos 12 arquivos `relational/`, verificado por extração literal (não por
memória), organizado por **propósito** — não alfabeticamente — para permitir avaliar de uma vez
cobertura de FK, regras de unicidade, padrões de busca e as categorias mais especializadas
(Time Series, PostGIS, JSONB). A mesma auditoria contra a DDL real que gerou D193–D196 encontrou
mais dois gaps ao preparar este documento (D197 PostGIS, D198 JSONB) — corrigidos antes deste
catálogo ser escrito, não depois.

## Método do índice

Toda coluna abaixo indica o método físico — a esmagadora maioria é `BTREE` (padrão implícito do
PostgreSQL quando `USING` não é declarado), mas o projeto já prevê PostGIS, JSONB e Time Series, e
documentar o método desde já facilita a evolução (full text, vetorial/IA) sem precisar re-auditar
tudo depois.

| Método | Quando se aplica | Uso neste projeto hoje |
|---|---|---|
| `BTREE` | Igualdade, faixa, ordenação — o caso geral | Todo PK, toda FK, toda UNIQUE, toda busca operacional |
| `GIN` | Contém/sobreposição em estruturas compostas (`JSONB`, array, full text) | `webhooks.eventos_assinados` (D198) |
| `GiST` | Proximidade/contenção espacial, também full text/`ranges` | `posicoes_veiculo.localizacao`, `cercas_eletronicas.centro`/`.poligono` (D197) |
| `SP-GiST` | Espacial não-balanceado (pontos dispersos, k-d tree) | Não usado — `GiST` já atende o volume atual; reavaliar só se `posicoes_veiculo` mostrar gargalo real |
| `BRIN` | Colunas fisicamente correlacionadas à ordem de inserção (ex: timestamp em tabela append-only grande) | Não usado ainda — candidato natural para as Time Series já particionadas (`capturado_em` dentro de cada partição mensal já é quase sequencial); avaliar em `PARTITIONING.md`, não decidido aqui |
| `Hash` | Igualdade pura, sem faixa/ordenação | Não usado — `BTREE` já cobre igualdade sem desvantagem relevante no volume atual |
| `HNSW` / `IVFFlat` | Busca vetorial (embeddings) | Não usado — nenhuma coluna `VECTOR` existe hoje; `pgvector` não foi decidido (D171 trata IA como inferência estruturada, não busca semântica); revisitar apenas se/quando isso mudar |

---

## 1. PK (Primary Key)

Todas as 133 tabelas têm PK própria — `BTREE`, sempre. Padrão universal (D175): `id UUID PRIMARY KEY
DEFAULT gen_random_uuid()`. Três formas de exceção, todas já documentadas nos arquivos de origem,
nenhuma nova aqui:

| Padrão | Quantidade | Exemplo |
|---|---|---|
| `id UUID PRIMARY KEY DEFAULT gen_random_uuid()` (padrão) | 125 | `viagens`, `contas_receber`, `ctes`, … |
| Chave composta pelas duas FKs (tabela de junção pura) | 8 | `papel_permissao`, `usuarios_papeis` (D222), `mdfes_ctes`, `composicoes_veiculares_implementos`, `grupos_usuarios_usuarios`, `snapshots_analiticos_indicadores`, `cubos_analiticos_metricas`, `relatorios_salvos_metricas` |
| PK é a própria FK (1:1, read model) | 1 | `disponibilidade_veiculo.veiculo_tracionador_id` |

`125 + 8 + 1 = 134` — confere com o total de `TABLES.md`.

## 2. FK (índices para JOIN)

A maioria das FKs de alto tráfego já nasceu com índice dedicado nos lotes anteriores — não é preciso
criar nada novo aqui, só confirmar. Padrão dominante: filha consultada por pai vira
`idx_<filha>_<pai>_id`, ex.: `idx_documentos_motorista_motorista_id`,
`idx_itens_carga_romaneio_id`, `idx_nfe_referenciadas_cte_id`, `idx_rateios_despesa_conta_pagar_id`,
`idx_registros_sincronizacao_sessao_mobile_id`. Quando a FK já é a coluna líder de uma composta de
busca operacional (categoria 4) ou de uma `UNIQUE` (categoria 3), conta como coberta — não precisa
de um índice extra só para a mesma coluna.

**FKs sem nenhum índice de suporte hoje** (nem dedicado, nem como coluna líder de outro índice) —
levantamento honesto, não uma lista de ações obrigatórias: todas são tabelas de volume atualmente
baixo (poucas linhas por tenant), então adicionar índice especulativo sem dado real de consulta
violaria o mesmo princípio de "não inventar sem necessidade justificada" (D076) aplicado à camada
física. Registrado para revisão quando o volume real ou o padrão de consulta do backend justificar:

| Tabela | Coluna sem cobertura | Nota |
|---|---|---|
| `usuarios` | `motorista_id`, `funcionario_id` | Baixíssima cardinalidade de uso (login por e-mail já coberto); revisitar se o app mobile passar a buscar Usuário por Motorista com frequência |
| `assinaturas` | `plano_id` | Poucas dezenas de planos possíveis, nunca um gargalo |
| `centros_custo` | `filial_id` | Poucos Centros de Custo por tenant |
| `romaneios` | `viagem_id` | Candidato mais forte da lista — se `romaneios` crescer como as demais tabelas de `viagens`, promover para `idx_romaneios_viagem_id` |
| `contratos_frete` | `cliente_id`, `tabela_preco_id` | Poucos contratos ativos por tenant |
| `cotacoes` | `cliente_id`, `contrato_frete_id` | Idem |
| `solicitacoes_frete` | `cliente_id` | Idem |
| `tabelas_preco` | `cliente_id` | Idem |
| `alocacoes_recurso_viagem` | `motorista_id`, `veiculo_tracionador_id`, `implemento_id` | Uma linha "vigente" por Viagem (D188) — volume baixo por natureza |

Nenhuma dessas é tratada como bug (diferente de D193/D194/D196/D197/D198) — são omissões
conscientes, não gaps de especificação, e ficam explícitas aqui em vez de escondidas.

## 3. UNIQUE (regras de unicidade de negócio)

69 constraints `UNIQUE` inline, uma por regra de negócio — nunca uma tabela sem justificativa de
domínio. Agrupado por módulo:

### Core

| Tabela | Colunas | Regra |
|---|---|---|
| `tenants` | `codigo` | Código único na plataforma |
| `tenants` | `cnpj` | CNPJ único na plataforma |
| `usuarios` | `tenant_id, codigo` | Código único por tenant |
| `usuarios` | `tenant_id, email` | E-mail único por tenant (login) |
| `papeis` | `tenant_id, nome` | Nome de Papel único por tenant |
| `permissoes` | `codigo` | Código de Permissão único na plataforma (D057, nunca editado) |
| `planos` | `nome` | Nome de Plano único na plataforma |
| `itens_plano` | `plano_id, chave_feature` | Feature única por Plano |
| `recursos_habilitados_tenant` | `tenant_id, chave_feature` | Feature única por tenant |
| `filiais` | `tenant_id, codigo` | Código de Filial único por tenant |
| `configuracoes_regionais_tenant` | `tenant_id` | 1:1 com Tenant |
| `configuracoes_personalizacao` | `tenant_id` | 1:1 com Tenant |

### Cadastros

| Tabela | Colunas | Regra |
|---|---|---|
| `clientes` | `tenant_id, codigo` | Código único por tenant |
| `clientes` | `tenant_id, cnpj_cpf` | CNPJ/CPF único por tenant |
| `motoristas` | `tenant_id, codigo` | Código único por tenant |
| `motoristas` | `tenant_id, cpf` | CPF único por tenant |
| `funcionarios` | `tenant_id, codigo` | Código único por tenant (D196) |
| `fornecedores` | `tenant_id, codigo` | Código único por tenant |
| `fornecedores` | `tenant_id, cnpj` | CNPJ único por tenant |
| `centros_custo` | `tenant_id, codigo` | Código único por tenant |
| `centros_custo` | `tenant_id, codigo_contabil` | Código contábil único por tenant |

### Operação

| Tabela | Colunas | Regra |
|---|---|---|
| `viagens` | `tenant_id, codigo` | Código único por tenant |
| `pontos_parada_viagem` | `viagem_id, ordem` | Ordem de parada única por Viagem |
| `entregas` | `viagem_id, ordem` | Ordem de entrega única por Viagem |
| `janelas_entrega` | `entrega_id` | 1:1 com Entrega |
| `canhotos` | `entrega_id` | 1:1 com Entrega |
| `contratos_frete` | `tenant_id, codigo` | Código único por tenant |
| `cotacoes` | `tenant_id, codigo` | Código único por tenant |

### Frota

| Tabela | Colunas | Regra |
|---|---|---|
| `categorias_veiculo` | `tenant_id, nome` | Nome único por tenant |
| `veiculos_tracionadores` | `tenant_id, codigo` | Código único por tenant |
| `veiculos_tracionadores` | `tenant_id, placa` | Placa única por tenant |
| `veiculos_tracionadores` | `tenant_id, renavam` | RENAVAM único por tenant |
| `implementos` | `tenant_id, codigo` | Código único por tenant |
| `implementos` | `tenant_id, placa` | Placa única por tenant |
| `fichas_tecnicas_veiculo` | `veiculo_tracionador_id` | 1:1 com Veículo Tracionador |
| `fichas_tecnicas_veiculo` | `chassi` | Chassi único na plataforma |
| `seguradoras` | `tenant_id, cnpj` | CNPJ único por tenant |
| `licenciamentos_veiculo` | `veiculo_tracionador_id, exercicio` | Um licenciamento por exercício/veículo |

### Manutenção

| Tabela | Colunas | Regra |
|---|---|---|
| `tipos_servico` | `tenant_id, nome` | Nome único por tenant |
| `ordens_servico` | `tenant_id, codigo` | Código único por tenant |

### Financeiro

| Tabela | Colunas | Regra |
|---|---|---|
| `formas_pagamento` | `tenant_id, nome` | Nome único por tenant |
| `plano_contas` | `tenant_id, codigo_contabil` | Código contábil único por tenant |
| `contas_bancarias` | `tenant_id, numero_conta` | Conta única por tenant (D189) |
| `faturas` | `tenant_id, numero_fatura` | Número único por tenant |
| `contas_receber` | `fatura_id, numero_parcela` | Parcela única por Fatura |
| `conciliacoes_bancarias` | `lancamento_extrato_id` | 1:1 com Lançamento de Extrato |
| `posicoes_caixa` | `tenant_id, data_referencia` | Uma posição por dia/tenant (read model) |

### Fiscal

| Tabela | Colunas | Regra |
|---|---|---|
| `configuracoes_fiscais_tenant` | `tenant_id` | 1:1 com Tenant |
| `ctes` | `tenant_id, serie, numero` | Numeração fiscal única por tenant |
| `ctes` | `chave_acesso` | Chave de acesso única na plataforma (regra da SEFAZ) |
| `mdfes` | `tenant_id, serie, numero` | Numeração fiscal única por tenant |
| `mdfes` | `chave_acesso` | Chave de acesso única na plataforma |
| `ciots` | `codigo_ciot` | Código CIOT único na plataforma (regra ANTT) |
| `cartas_correcao` | `cte_id, numero_sequencial` | Sequência única por CT-e |

### Rastreamento

| Tabela | Colunas | Regra |
|---|---|---|
| `provedores_rastreamento` | `tenant_id, nome` | Nome único por tenant |
| `equipamentos_rastreamento` | `identificador_serial` | Serial único na plataforma (número de série físico) |
| `cercas_eletronicas` | `tenant_id, nome` | Nome único por tenant |

### App Motorista

| Tabela | Colunas | Regra |
|---|---|---|
| `dispositivos_mobile` | `identificador_dispositivo` | Identificador único na plataforma |
| `filas_sincronizacao` | `sessao_mobile_id, identificador_local_unico` | Idempotência de sincronização (D111) |
| `filas_sincronizacao` | `sessao_mobile_id, sequencia_local` | Sequência única por sessão |

### Administração

| Tabela | Colunas | Regra |
|---|---|---|
| `grupos_usuarios` | `tenant_id, nome` | Nome único por tenant |
| `fatores_autenticacao` | `usuario_id, tipo` | Um fator de cada tipo por Usuário |
| `configuracoes_numeracao` | `tenant_id, tipo_entidade` | Uma configuração por tipo/tenant |
| `tokens_api` | `token_hash` | Hash de token único na plataforma (nunca reutilizado, D084) |

### BI

| Tabela | Colunas | Regra |
|---|---|---|
| `cubos_analiticos` | `tenant_id, nome` | Nome único por tenant |
| `dashboards_personalizados` | `usuario_id, nome` | Nome único por Usuário |
| `filtros_favoritos` | `usuario_id, nome` | Nome único por Usuário |
| `relatorios_salvos` | `usuario_id, nome` | Nome único por Usuário |

### IA

| Tabela | Colunas | Regra |
|---|---|---|
| `modelos_ia` | `nome, versao` | Versão única por Modelo |

Todo `UNIQUE` acima é `BTREE` — método padrão do PostgreSQL para essa constraint, nunca outro.

## 4. Busca operacional

Índices compostos que sustentam o padrão de consulta real da aplicação — quase sempre
`(tenant_id, <coluna de filtro>)`, porque toda tela lista "os registros deste tenant, filtrados por
X" (TENANCY_MODEL.md). `BTREE` em todos.

| Tabela | Índice | Suporta |
|---|---|---|
| `tenants` | `(status) WHERE excluido_em IS NULL` | Listagem de tenants ativos |
| `usuarios` | `(tenant_id, email) WHERE excluido_em IS NULL` | Login |
| `permissoes` | `(modulo)` | Agrupamento por módulo na tela de RBAC |
| `filiais` | `(tenant_id) WHERE esta_matriz UNIQUE` | Garantir uma matriz por tenant (também é regra de unicidade — dupla função) |
| `enderecos` | `(entidade_tipo, entidade_id) WHERE excluido_em IS NULL` | Buscar endereços de uma entidade-dona |
| `clientes` | `(tenant_id, cnpj_cpf)`, `(tenant_id, razao_social)`, `(tenant_id, status)` (todos `WHERE excluido_em IS NULL`) | Busca/listagem de Cliente |
| `motoristas` | `(tenant_id, cpf)`, `(tenant_id, status_aptidao)` (`WHERE excluido_em IS NULL`) | Busca/listagem de Motorista |
| `documentos_motorista` | `(data_validade) WHERE status = 'VALIDO'` | Alerta de vencimento de documento |
| `funcionarios` | `(tenant_id, status) WHERE excluido_em IS NULL` | Listagem de Funcionário |
| `fornecedores` | `(tenant_id, cnpj) WHERE excluido_em IS NULL` | Busca de Fornecedor |
| `viagens` | `(tenant_id, status_operacional)`, `(tenant_id, motorista_id)`, `(tenant_id, veiculo_tracionador_id)`, `(tenant_id, data_programada)`, `(tenant_id, cliente_id)`, `(tenant_id, encerrada)` (todos `WHERE excluido_em IS NULL`) | Painel operacional — a tabela mais consultada do sistema |
| `ocorrencias` | `(tenant_id, tipo)` | Listagem por tipo de ocorrência |
| `veiculos_tracionadores` | `(tenant_id, status) WHERE excluido_em IS NULL` | Listagem de frota |
| `ordens_servico` | `(tenant_id, veiculo_tracionador_id)`, `(tenant_id, status)` (`WHERE excluido_em IS NULL`), `(data_inicio_execucao)`, `(data_conclusao)`, `(fornecedor_executor_id)`, `(tenant_id, tipo)` | Painel de manutenção |
| `plano_contas` | `(categoria_pai_id)` | Navegação da árvore hierárquica (D184) |
| `faturas` | `(tenant_id, cliente_id)` | Listagem de faturas por cliente |
| `contas_receber` | `(tenant_id, status)`, `(data_vencimento) WHERE status IN ('PENDENTE','VENCIDA')` | Painel financeiro (contas a receber) |
| `contas_pagar` | `(tenant_id, status)`, `(fornecedor_id)` | Painel financeiro (contas a pagar) |
| `ctes` | `(tenant_id, status)`, `(viagem_id)` | Painel fiscal |
| `equipamentos_rastreamento` | *(ver categoria 3 — coberto por UNIQUE parcial)* | — |
| `sessoes_mobile` | `(motorista_id, status)` | App Motorista — sessão ativa do motorista |
| `filas_sincronizacao` | `(tenant_id, status) WHERE status IN ('PENDENTE','FALHOU','CONFLITO')`, `(entidade_destino_tipo, entidade_destino_id)` | Fila de sincronização pendente |
| `assinaturas_digitais` | `(documento_tipo, documento_id)` | Buscar assinaturas de um documento |
| `sessoes_acesso` | `(usuario_id, status)` | Sessões ativas de um Usuário |
| `webhooks` | `(tenant_id, status)` (D198) | Webhooks ativos do tenant |
| `logs_auditoria` | `(tenant_id, entidade_tipo, entidade_id, data_hora DESC)`, `(id_correlacao)` | Timeline de auditoria de uma entidade; agrupar por transação |
| `indicadores_consolidados` | `(metrica_id, dimensao_tipo, dimensao_id, periodo_referencia)` | Consulta de indicador por dimensão/período |
| `exportacoes_geradas` | `(usuario_id, data_hora_solicitacao DESC)` | Histórico de exportações do usuário |
| `sugestoes_ia` | `(entidade_alvo_tipo, entidade_alvo_id)`, `(tenant_id, status)`, `(usuario_decisao_id)` | Sugestões pendentes de uma entidade |
| `predicoes_ia` | `(entidade_alvo_tipo, entidade_alvo_id)`, `(status, data_hora_validade_fim)` | Predições vigentes de uma entidade |
| `classificacoes_ia` | `(entidade_alvo_tipo, entidade_alvo_id, tipo_classificacao)` | Classificação de uma entidade |
| `anomalias_detectadas` | `(leitura_origem_tipo, leitura_origem_id)` | Anomalias de uma leitura de origem |
| `feedbacks_ia` | `(saida_ia_tipo, saida_ia_id)` | Feedback de uma saída de IA específica |

## 5. Time Series (padrão D191)

Toda tabela que segue o padrão físico único de D191 tem exatamente um índice
`(entidade_id, <timestamp> DESC)` — nunca mais, nunca menos, formato fixo. `BTREE` (o volume e o
padrão de acesso — sempre "últimas leituras desta entidade" — não pedem `BRIN`/`GiST` para esta
dimensão; `GiST` entra à parte, na coluna espacial, categoria 8).

| Tabela | Índice | Timestamp usado |
|---|---|---|
| `leituras_hodometro` | `(veiculo_tracionador_id, data_hora DESC)` | `data_hora` |
| `posicoes_veiculo` | `(veiculo_tracionador_id, capturado_em DESC)` | `capturado_em` (padrão D191) |
| `leituras_telemetria` | `(veiculo_tracionador_id, tipo_sensor, capturado_em DESC)` | `capturado_em` (padrão D191, + `tipo_sensor` pelo padrão EAV, D120) |
| `heartbeats` | *(sem índice dedicado de timestamp — coberto pela `UNIQUE` de idempotência, categoria 3)* | `recebido_em` (exceção D191 documentada) |
| `eventos_rastreamento` | `(veiculo_tracionador_id, tipo, data_hora DESC)` | `data_hora` (não segue D191 — é derivado/detectado, não capturado de fonte externa) |

## 6. Partições

10 tabelas particionadas desde a primeira migration (D179, nunca retrofit — a décima,
`inferencias_ia`, corrigida em D201 ao preparar `PARTITIONING.md`) — cada partição mensal herda
automaticamente todo índice declarado na tabela-mãe (comportamento nativo do PostgreSQL para
tabelas particionadas por `PARTITION BY RANGE`), então nenhum índice "local" precisa ser redeclarado
por partição.

| Tabela particionada | Partição por | Índices herdados por partição |
|---|---|---|
| `viagem_status_history` | `tenant_id` + `data_hora` (D179) | `(viagem_id, dimensao, data_hora)` |
| `leituras_hodometro` | `tenant_id` + `data_hora` (D179) | `(veiculo_tracionador_id, data_hora DESC)` |
| `eventos_fiscais` | `tenant_id` + `data_hora` (D179) | `(documento_tipo, documento_id)`, `UNIQUE (documento_tipo, documento_id, protocolo_externo)` |
| `posicoes_veiculo` | `capturado_em` (D191) | `(veiculo_tracionador_id, capturado_em DESC)`, `GiST (localizacao)` (D197) |
| `leituras_telemetria` | `capturado_em` (D191) | `(veiculo_tracionador_id, tipo_sensor, capturado_em DESC)` |
| `heartbeats` | `recebido_em` (exceção D191) | `UNIQUE (equipamento_rastreamento_id, protocolo_externo)` |
| `eventos_rastreamento` | `data_hora` | `(veiculo_tracionador_id, tipo, data_hora DESC)` |
| `execucoes_job` | `data_hora_inicio` | *(sem índice dedicado — volume técnico, consultado por job recente via `ORDER BY` simples)* |
| `logs_auditoria` | `data_hora` (D176/D194) | `(tenant_id, entidade_tipo, entidade_id, data_hora DESC)`, `(id_correlacao)` |
| `inferencias_ia` | `data_hora_inicio` (D201) | `(modelo_ia_id, data_hora_inicio DESC)`, `(tenant_id, status)` |

Detalhe de retenção/arquivamento/rotação automática de partição fica em `PARTITIONING.md` (próximo
da sequência, não decidido aqui).

## 7. JSONB

~15 colunas `JSONB` no sistema (auditadas ao preparar este documento). Só uma justifica `GIN` hoje:

| Tabela.Coluna | Índice | Por quê |
|---|---|---|
| `webhooks.eventos_assinados` | `GIN (eventos_assinados)` (D198) | Consultada pelo *conteúdo* em hot path — "quais webhooks assinam o evento X", toda vez que um domain event é publicado |

As demais (`viagens.cliente_snapshot`, `entregas.endereco_entrega`,
`solicitacoes_frete.origem`/`destinos`, `filas_sincronizacao.payload`, `logs_auditoria.dados_antes`/
`dados_depois`, `metricas.origem_dados`, `cubos_analiticos.dimensoes`,
`dashboards_personalizados.layout`/`widgets`/`filtros`/`preferencias`, `filtros_favoritos.criterios`,
`relatorios_salvos.filtros`, `exportacoes_geradas.filtros_utilizados`/`metricas_versoes`,
`inferencias_ia.entrada`/`saida`, `leituras_visao_computacional.regiao_analisada`/
`resultado_extraido`) são sempre lidas inteiras a partir de uma linha já localizada por outra chave
(`id`, `tenant_id`, FK) — nunca pesquisadas pelo valor interno. `GIN` nelas seria índice não
utilizado, o mesmo raciocínio já aplicado à decisão de não indexar `pontos_parada_viagem.localizacao`
(categoria 8).

## 8. PostGIS

3 índices `GiST` (D197 — gap real encontrado e corrigido ao preparar este documento; nenhum existia
antes, apesar de 5 colunas `GEOGRAPHY` já modeladas desde `003-operacao.md`/`008-rastreamento.md`):

| Tabela.Coluna | Índice | Por quê |
|---|---|---|
| `posicoes_veiculo.localizacao` | `GiST (localizacao)` | Base de toda consulta espacial de rastreamento — "veículos próximos de X", avaliação de geofence |
| `cercas_eletronicas.centro` | `GiST (centro) WHERE centro IS NOT NULL` | Geofence circular — consultada por contenção/proximidade a cada posição recebida |
| `cercas_eletronicas.poligono` | `GiST (poligono) WHERE poligono IS NOT NULL` | Geofence poligonal — mesmo motivo |

**Deliberadamente não indexadas**: `pontos_parada_viagem.localizacao`, `coletas.local` — ambas
`GEOGRAPHY(Point, 4326)`, mas sempre lidas por `viagem_id` (já indexado), nunca por
proximidade/contenção espacial. Mesma lógica de "não inventar sem necessidade" já aplicada à
categoria 2 e 7.

## 9. Full Text

Nenhum. Não há requisito de busca textual documentado em nenhum Flow/Domain/Dictionary — nenhuma
tela pede "buscar por palavra-chave em observações/descrições" hoje. Diferente de PostGIS (D173,
decisão explícita de fundação) e JSONB (tipo já usado em 15 colunas), Full Text nunca foi uma
decisão tomada, então não é fabricada aqui só para preencher a categoria. Se/quando um Flow futuro
pedir busca textual (candidato mais provável: `comentarios.texto` ou `ocorrencias.descricao`), o
padrão a aplicar é `GIN` sobre uma coluna `tsvector` gerada (`GENERATED ALWAYS AS
(to_tsvector('portuguese', texto)) STORED`, mesmo critério D185 de coluna computada de mesma linha)
— registrado aqui como o padrão futuro, não implementado agora.

## 10. Índices parciais (`WHERE`)

Provavelmente a categoria de maior retorno real de performance — cada um evita que o índice cresça
com linhas que a aplicação nunca consulta (excluídas logicamente, encerradas, não vigentes).

| Tabela | Índice parcial | Filtra fora |
|---|---|---|
| `tenants` | `(status) WHERE excluido_em IS NULL` | Tenants excluídos |
| `usuarios` | `(tenant_id, email) WHERE excluido_em IS NULL` | Usuários excluídos |
| `assinaturas` | `UNIQUE (tenant_id) WHERE status = 'ATIVA'` | Assinaturas não ativas — garante uma só `ATIVA` por tenant |
| `filiais` | `UNIQUE (tenant_id) WHERE esta_matriz AND excluido_em IS NULL` | Garante uma só matriz por tenant |
| `enderecos` | `(entidade_tipo, entidade_id) WHERE excluido_em IS NULL`; `UNIQUE (...) WHERE tipo_endereco = 'PRINCIPAL' AND excluido_em IS NULL` | Endereços excluídos; garante um só Principal vigente |
| `clientes`, `motoristas`, `funcionarios`, `fornecedores` | `(tenant_id, ...) WHERE excluido_em IS NULL` (múltiplos) | Registros excluídos (soft delete, D177) |
| `documentos_motorista` | `(data_validade) WHERE status = 'VALIDO'` | Documentos já vencidos |
| `viagens` | `(tenant_id, ...) WHERE excluido_em IS NULL` (6 índices) | Viagens excluídas |
| `alocacoes_recurso_viagem` | `UNIQUE (viagem_id) WHERE status = 'VIGENTE'` | Alocações históricas — garante uma vigente por Viagem (D188) |
| `veiculos_tracionadores` | `(tenant_id, status) WHERE excluido_em IS NULL` | Veículos excluídos |
| `composicoes_veiculares` | `UNIQUE (veiculo_tracionador_id) WHERE data_fim_vigencia IS NULL` | Composições encerradas — garante uma vigente por veículo |
| `planos_manutencao_preventiva` | `(veiculo_tracionador_id) WHERE status = 'ATIVO'` | Planos inativos |
| `ordens_servico` | `(tenant_id, ...) WHERE excluido_em IS NULL` (2 índices) | Ordens de Serviço excluídas |
| `contas_receber` | `(data_vencimento) WHERE status IN ('PENDENTE','VENCIDA')` | Contas já recebidas/canceladas — a tela de cobrança nunca olha para elas |
| `ctes`/`mdfes` | `UNIQUE (protocolo_sefaz) WHERE protocolo_sefaz IS NOT NULL` | Documentos ainda sem protocolo (idempotência, D111) |
| `ciots` | `UNIQUE (protocolo_antt) WHERE protocolo_antt IS NOT NULL` | Idem |
| `eventos_fiscais` | `UNIQUE (documento_tipo, documento_id, protocolo_externo) WHERE protocolo_externo IS NOT NULL` | Idem |
| `equipamentos_rastreamento` | `UNIQUE (veiculo_tracionador_id) WHERE tipo_equipamento = 'PRINCIPAL' AND data_fim_vigencia IS NULL` | Equipamentos removidos/backup — garante um Principal vigente por veículo (D128) |
| `heartbeats` | `UNIQUE (equipamento_rastreamento_id, protocolo_externo) WHERE protocolo_externo IS NOT NULL` | Idempotência (D111) |
| `cercas_eletronicas` | `GiST (centro)/(poligono) WHERE ... IS NOT NULL` (D197) | A metade das linhas que não usa aquela geometria (CIRCULO vs. POLIGONO) |
| `filas_sincronizacao` | `(tenant_id, status) WHERE status IN ('PENDENTE','FALHOU','CONFLITO')` | Itens já sincronizados com sucesso — a fila de trabalho nunca olha para eles |
| `convites` | `UNIQUE (tenant_id, email) WHERE status = 'PENDENTE'` | Convites já aceitos/expirados/revogados |
| `parametros_tenant` | `UNIQUE (tenant_id, chave) WHERE status = 'VIGENTE'` | Parâmetros históricos — garante um vigente por chave (D145) |
| `bloqueios_acesso` | `UNIQUE (usuario_id) WHERE status = 'VIGENTE'` | Bloqueios já removidos — garante um vigente por Usuário |

## Totais

| Categoria | Quantidade |
|---|---|
| PK | 133 |
| FK dedicado (não duplicado com categoria 3/4) | ~15 |
| UNIQUE | 69 |
| Busca operacional (composta, não parcial) | ~45 |
| Time Series (D191) | 4 |
| JSONB (`GIN`) | 1 |
| PostGIS (`GiST`) | 3 |
| Full Text | 0 |
| Índices parciais (`WHERE`, contados uma vez, já listados acima nas categorias que se aplicam) | 22 |

Os totais de FK/Busca operacional/Parciais se sobrepõem entre si (um índice pode ser
simultaneamente "busca operacional" e "parcial", ex.: `idx_viagens_tenant_id_status_operacional
WHERE excluido_em IS NULL`) — a soma bruta das categorias não é igual ao total de 112 `CREATE
INDEX` explícitos do sistema; cada índice aparece na(s) categoria(s) que melhor descrevem seu
propósito primário, não em uma partição estrita e disjunta.

## Como este documento cresce

Estável enquanto o Modelo Relacional não muda. Qualquer índice novo criado num `relational/NNN.md`
precisa ganhar uma linha na categoria correta aqui, com Método explícito, na mesma revisão. Próximo
documento da sequência: [`CONSTRAINTS.md`](./CONSTRAINTS.md), agrupado por categoria (Integridade/
Exclusividade/Estados/Temporalidade/Tenant/Idempotência/Confirmação Humana/Soft Delete) — muitas das
`UNIQUE`/parciais já catalogadas aqui reaparecem lá, mas descritas pela regra de negócio que
protegem, não pelo mecanismo físico.
