# TABLES.md — Catálogo Mestre do Banco

Não repete o DDL (já está em [`relational/`](./relational/)) nem o diagrama (já está em
[`DER.md`](./DER.md)) — este é o índice tabela-a-tabela, uma linha por tabela física, para consulta
rápida sem abrir os 12 arquivos relacionais.

**135 tabelas**, confirmado por contagem literal de `CREATE TABLE` nos 12 arquivos `relational/`
(excluindo declarações de partição, que são filhas físicas da tabela-mãe, não tabelas novas — ex:
`posicoes_veiculo_2026_01 PARTITION OF posicoes_veiculo`). Nota: essa contagem só ficou correta de
fato depois de D194/D196/D222 — `logs_auditoria`, `funcionarios` e `usuarios_papeis` eram
referenciadas/documentadas em detalhe (ou, no caso de `usuarios_papeis`, uma relação N:N do próprio
Domain Model) mas nunca tinham `CREATE TABLE` real antes destas preparações (ver seções
Administração e Core abaixo e [`DECISIONS.md`](../product/DECISIONS.md) D193–D206/D222). Sprint 10
Lote 7 (API de Financeiro) encontrou o mesmo padrão pela sétima vez: `assinaturas_status_history`
— D017/D018 exige histórico para `assinaturas.status`, nunca materializado — corrigida como D269.

## Legenda

**Tipo**:

| Tipo | Significado |
|---|---|
| Mestre | Dados cadastrais/de referência do tenant — baixa frequência de mudança, consultado o tempo todo |
| Transacional | Registra uma operação/decisão de negócio — o volume cresce com a operação do dia a dia |
| Histórica | Log técnico ou de transição de status, append-only, nunca `UPDATE`/`DELETE` |
| Read Model | Estado atual materializado, escrito só por consumidor de evento — nunca por rota de API de escrita direta |
| Time Series | Leitura de sensor/telemetria em alta frequência, padrão físico único D191 |
| Configuração | Parâmetro/preferência que molda comportamento, não é o próprio dado operacional |
| Junção | Tabela N:N pura — chave primária composta pelas duas FKs, sem coluna de negócio própria |
| Referência | Platform Reference Data (D046) — catálogo compartilhado por toda a plataforma, sem `tenant_id` |

**Categoria Física** (opcional, sugerida em revisão — complementa o Tipo com a natureza física para
fins de manutenção/backup/retenção/particionamento; uma tabela recebe exatamente uma categoria,
pela característica dominante, não pelo módulo de negócio):

| Categoria Física | Significado | Implicação operacional |
|---|---|---|
| Core | Identidade do tenant e do seu plano/assinatura, infraestrutura polimórfica compartilhada (`anexos`/`comentarios`/`enderecos`) | Backup mais crítico, retenção indefinida |
| Security | Identidade de usuário, RBAC, autenticação, sessão, auditoria | Backup crítico, retenção por exigência legal/compliance, acesso restrito |
| Master Data | Cadastros de baixa volatilidade (clientes, motoristas, veículos, etc.) | Backup padrão, retenção indefinida, baixa taxa de crescimento |
| Transactional | Operação do dia a dia | Backup padrão, retenção longa, cresce com o volume de negócio |
| History | Log de transição de status, append-only | Retenção por política (ex: 5 anos fiscal), candidata a arquivamento frio |
| Time Series | Sensor/telemetria em alta frequência (padrão D191) | Particionamento obrigatório, retenção curta com agregação/arquivamento |
| Read Model | Materializado por consumidor de evento | Pode ser reconstruído a partir do event stream — backup é otimização, não fonte de verdade |
| Configuration | Parâmetro que molda comportamento | Baixo volume, backup crítico apesar do tamanho pequeno |
| Integration | Webhook, token, sincronização mobile, job assíncrono | Segredos/credenciais possivelmente envolvidos, retenção curta em alguns casos |
| Analytics | BI — sempre derivado, nunca fonte de verdade (D090) | Reconstruível a partir das tabelas operacionais, backup é otimização |
| AI | Inferência/sugestão/predição de IA | Retenção pensada para auditoria de modelo e retraining, não só operação |

**Tenant**: `Sim` = toda linha tem `tenant_id NOT NULL`. `Não` = Platform Reference Data ou a
própria raiz (`tenants`). `Sim*` = `tenant_id` existe mas é opcional — nulo representa "recurso da
plataforma", não um esquecimento (`modelos_ia`, `execucoes_job`); ver nota em cada tabela no arquivo
relational correspondente.

**Particionada**: `Sim` = particionada desde a primeira migration (D179), nunca retrofit.

**Histórico**: `Sim` = a tabela em si é um registro histórico/append-only (Tipo Histórica ou Time
Series) — não confundir com a coluna "Histórico" do Data Dictionary Funcional, que descreve atributo
por atributo.

**Aggregate**: a raiz de agregação (DDD) a que a tabela pertence, no vocabulário já fixado no
[Domain Model](../domain/ENTITY_CATALOG.md). Tabelas compartilhadas/polimórficas (D186) marcam
"Compartilhado".

---

## Core (14) — [`relational/001-core.md`](./relational/001-core.md)

| Tabela | Módulo | Tipo | Categoria Física | Aggregate | Tenant | Particionada | Histórico | Documento |
|---|---|---|---|---|---|---|---|---|
| `tenants` | Core | Mestre | Core | Tenant | Não | Não | Não | [001-core.md](./relational/001-core.md) |
| `usuarios` | Core | Mestre | Security | Usuário | Sim | Não | Não | [001-core.md](./relational/001-core.md) |
| `papeis` | Core | Mestre | Security | Papel | Sim | Não | Não | [001-core.md](./relational/001-core.md) |
| `permissoes` | Core | Referência | Security | Permissão | Não | Não | Não | [001-core.md](./relational/001-core.md) |
| `papel_permissao` | Core | Junção | Security | Papel | Não | Não | Não | [001-core.md](./relational/001-core.md) |
| `usuarios_papeis` | Core | Junção | Security | Usuário (D222) | Não | Não | Não | [001-core.md](./relational/001-core.md) |
| `planos` | Core | Configuração | Core | Plano | Não | Não | Não | [001-core.md](./relational/001-core.md) |
| `itens_plano` | Core | Configuração | Core | Plano | Não | Não | Não | [001-core.md](./relational/001-core.md) |
| `assinaturas` | Core | Transacional | Core | Assinatura | Sim | Não | Não | [001-core.md](./relational/001-core.md) |
| `assinaturas_status_history` | Core | Histórico | History | Assinatura | Sim | Não | Não | [001-core.md](./relational/001-core.md) |
| `cobrancas_recorrentes` | Core | Transacional | Core | Assinatura | Sim | Não | Não | [001-core.md](./relational/001-core.md) |
| `recursos_habilitados_tenant` | Core | Configuração | Core | Tenant | Sim | Não | Não | [001-core.md](./relational/001-core.md) |
| `filiais` | Core | Mestre | Core | Filial | Sim | Não | Não | [001-core.md](./relational/001-core.md) |
| `configuracoes_regionais_tenant` | Core | Configuração | Core | Tenant | Sim | Não | Não | [001-core.md](./relational/001-core.md) |
| `configuracoes_personalizacao` | Core | Configuração | Core | Tenant | Sim | Não | Não | [001-core.md](./relational/001-core.md) |

## Cadastros (8) — [`relational/002-cadastros.md`](./relational/002-cadastros.md)

| Tabela | Módulo | Tipo | Categoria Física | Aggregate | Tenant | Particionada | Histórico | Documento |
|---|---|---|---|---|---|---|---|---|
| `enderecos` | Cadastros | Mestre | Core | Endereço (D182, compartilhado) | Sim | Não | Não | [002-cadastros.md](./relational/002-cadastros.md) |
| `clientes` | Cadastros | Mestre | Master Data | Cliente | Sim | Não | Não | [002-cadastros.md](./relational/002-cadastros.md) |
| `contatos_cliente` | Cadastros | Mestre | Master Data | Cliente | Sim | Não | Não | [002-cadastros.md](./relational/002-cadastros.md) |
| `motoristas` | Cadastros | Mestre | Master Data | Motorista | Sim | Não | Não | [002-cadastros.md](./relational/002-cadastros.md) |
| `documentos_motorista` | Cadastros | Mestre | Master Data | Motorista (D183) | Sim | Não | Não | [002-cadastros.md](./relational/002-cadastros.md) |
| `funcionarios` | Cadastros | Mestre | Master Data | Funcionário (D196) | Sim | Não | Não | [002-cadastros.md](./relational/002-cadastros.md) |
| `fornecedores` | Cadastros | Mestre | Master Data | Fornecedor | Sim | Não | Não | [002-cadastros.md](./relational/002-cadastros.md) |
| `centros_custo` | Cadastros | Mestre | Master Data | Centro de Custo | Sim | Não | Não | [002-cadastros.md](./relational/002-cadastros.md) |

## Operação (19) — [`relational/003-operacao.md`](./relational/003-operacao.md)

`anexos`/`comentarios` são infraestrutura compartilhada (D186) criada aqui por origem do arquivo,
usada por qualquer entidade do sistema via `entidade_tipo`/`entidade_id` — não são exclusivas da
Operação.

| Tabela | Módulo | Tipo | Categoria Física | Aggregate | Tenant | Particionada | Histórico | Documento |
|---|---|---|---|---|---|---|---|---|
| `anexos` | Compartilhado | Mestre | Core | Compartilhado (D186, polimórfico) | Sim | Não | Não | [003-operacao.md](./relational/003-operacao.md) |
| `comentarios` | Compartilhado | Mestre | Core | Compartilhado (D186, polimórfico) | Sim | Não | Não | [003-operacao.md](./relational/003-operacao.md) |
| `viagens` | Operação | Transacional | Transactional | Viagem | Sim | Não | Não | [003-operacao.md](./relational/003-operacao.md) |
| `viagem_status_history` | Operação | Histórica | History | Viagem | Sim | Sim | Sim | [003-operacao.md](./relational/003-operacao.md) |
| `alocacoes_recurso_viagem` | Operação | Transacional | Transactional | Viagem (D188) | Sim | Não | Não | [003-operacao.md](./relational/003-operacao.md) |
| `pontos_parada_viagem` | Operação | Transacional | Transactional | Viagem | Sim | Não | Não | [003-operacao.md](./relational/003-operacao.md) |
| `entregas` | Operação | Transacional | Transactional | Entrega | Sim | Não | Não | [003-operacao.md](./relational/003-operacao.md) |
| `janelas_entrega` | Operação | Transacional | Transactional | Entrega | Sim | Não | Não | [003-operacao.md](./relational/003-operacao.md) |
| `coletas` | Operação | Transacional | Transactional | Coleta | Sim | Não | Não | [003-operacao.md](./relational/003-operacao.md) |
| `ocorrencias` | Operação | Transacional | Transactional | Ocorrência | Sim | Não | Não | [003-operacao.md](./relational/003-operacao.md) |
| `romaneios` | Operação | Transacional | Transactional | Romaneio | Sim | Não | Não | [003-operacao.md](./relational/003-operacao.md) |
| `itens_carga` | Operação | Transacional | Transactional | Romaneio | Sim | Não | Não | [003-operacao.md](./relational/003-operacao.md) |
| `canhotos` | Operação | Transacional | Transactional | Canhoto | Sim | Não | Não | [003-operacao.md](./relational/003-operacao.md) |
| `contratos_frete` | Operação | Mestre | Master Data | Contrato de Frete | Sim | Não | Não | [003-operacao.md](./relational/003-operacao.md) |
| `cotacoes` | Operação | Transacional | Transactional | Cotação | Sim | Não | Não | [003-operacao.md](./relational/003-operacao.md) |
| `itens_cotacao` | Operação | Transacional | Transactional | Cotação | Sim | Não | Não | [003-operacao.md](./relational/003-operacao.md) |
| `solicitacoes_frete` | Operação | Transacional | Transactional | Solicitação de Frete | Sim | Não | Não | [003-operacao.md](./relational/003-operacao.md) |
| `tabelas_preco` | Operação | Configuração | Configuration | Tabela de Preço | Sim | Não | Não | [003-operacao.md](./relational/003-operacao.md) |
| `itens_tabela_preco` | Operação | Configuração | Configuration | Tabela de Preço | Sim | Não | Não | [003-operacao.md](./relational/003-operacao.md) |

## Frota (12) — [`relational/004-frota.md`](./relational/004-frota.md)

| Tabela | Módulo | Tipo | Categoria Física | Aggregate | Tenant | Particionada | Histórico | Documento |
|---|---|---|---|---|---|---|---|---|
| `categorias_veiculo` | Frota | Configuração | Configuration | Categoria de Veículo | Sim | Não | Não | [004-frota.md](./relational/004-frota.md) |
| `veiculos_tracionadores` | Frota | Mestre | Master Data | Veículo Tracionador | Sim | Não | Não | [004-frota.md](./relational/004-frota.md) |
| `implementos` | Frota | Mestre | Master Data | Implemento | Sim | Não | Não | [004-frota.md](./relational/004-frota.md) |
| `composicoes_veiculares` | Frota | Mestre | Master Data | Composição Veicular | Sim | Não | Não | [004-frota.md](./relational/004-frota.md) |
| `composicoes_veiculares_implementos` | Frota | Junção | Master Data | Composição Veicular | Não | Não | Não | [004-frota.md](./relational/004-frota.md) |
| `fichas_tecnicas_veiculo` | Frota | Mestre | Master Data | Veículo Tracionador | Sim | Não | Não | [004-frota.md](./relational/004-frota.md) |
| `documentos_veiculo` | Frota | Mestre | Master Data | Veículo Tracionador | Sim | Não | Não | [004-frota.md](./relational/004-frota.md) |
| `seguradoras` | Frota | Mestre | Master Data | Seguradora | Sim | Não | Não | [004-frota.md](./relational/004-frota.md) |
| `apolices_seguro_veicular` | Frota | Mestre | Master Data | Veículo Tracionador | Sim | Não | Não | [004-frota.md](./relational/004-frota.md) |
| `licenciamentos_veiculo` | Frota | Mestre | Master Data | Veículo Tracionador | Sim | Não | Não | [004-frota.md](./relational/004-frota.md) |
| `leituras_hodometro` | Frota | Time Series | Time Series | Veículo Tracionador | Sim | Sim | Sim | [004-frota.md](./relational/004-frota.md) |
| `disponibilidade_veiculo` | Frota | Read Model | Read Model | Veículo Tracionador | Sim | Não | Não | [004-frota.md](./relational/004-frota.md) |

## Manutenção (9) — [`relational/005-manutencao.md`](./relational/005-manutencao.md)

| Tabela | Módulo | Tipo | Categoria Física | Aggregate | Tenant | Particionada | Histórico | Documento |
|---|---|---|---|---|---|---|---|---|
| `tipos_servico` | Manutenção | Configuração | Configuration | Tipo de Serviço | Sim | Não | Não | [005-manutencao.md](./relational/005-manutencao.md) |
| `planos_manutencao_preventiva` | Manutenção | Configuração | Configuration | Plano de Manutenção Preventiva | Sim | Não | Não | [005-manutencao.md](./relational/005-manutencao.md) |
| `ordens_servico` | Manutenção | Transacional | Transactional | Ordem de Serviço | Sim | Não | Não | [005-manutencao.md](./relational/005-manutencao.md) |
| `ordens_servico_status_history` | Manutenção | Histórica | History | Ordem de Serviço | Sim | Não | Sim | [005-manutencao.md](./relational/005-manutencao.md) |
| `itens_ordem_servico` | Manutenção | Transacional | Transactional | Ordem de Serviço | Sim | Não | Não | [005-manutencao.md](./relational/005-manutencao.md) |
| `aprovacoes_custo` | Manutenção | Transacional | Transactional | Ordem de Serviço | Sim | Não | Não | [005-manutencao.md](./relational/005-manutencao.md) |
| `solicitacoes_peca` | Manutenção | Transacional | Transactional | Ordem de Serviço | Sim | Não | Não | [005-manutencao.md](./relational/005-manutencao.md) |
| `pecas_estoque` | Manutenção | Mestre | Master Data | Peça de Estoque | Sim | Não | Não | [005-manutencao.md](./relational/005-manutencao.md) |
| `movimentacoes_estoque` | Manutenção | Transacional | Transactional | Peça de Estoque | Sim | Não | Não | [005-manutencao.md](./relational/005-manutencao.md) |

## Financeiro (14) — [`relational/006-financeiro.md`](./relational/006-financeiro.md)

| Tabela | Módulo | Tipo | Categoria Física | Aggregate | Tenant | Particionada | Histórico | Documento |
|---|---|---|---|---|---|---|---|---|
| `formas_pagamento` | Financeiro | Configuração | Configuration | Forma de Pagamento | Sim | Não | Não | [006-financeiro.md](./relational/006-financeiro.md) |
| `plano_contas` | Financeiro | Configuração | Configuration | Plano de Contas (D184) | Sim | Não | Não | [006-financeiro.md](./relational/006-financeiro.md) |
| `contas_bancarias` | Financeiro | Mestre | Master Data | Conta Bancária (D189) | Sim | Não | Não | [006-financeiro.md](./relational/006-financeiro.md) |
| `faturas` | Financeiro | Transacional | Transactional | Fatura | Sim | Não | Não | [006-financeiro.md](./relational/006-financeiro.md) |
| `contas_receber` | Financeiro | Transacional | Transactional | Conta a Receber | Sim | Não | Não | [006-financeiro.md](./relational/006-financeiro.md) |
| `contas_receber_status_history` | Financeiro | Histórica | History | Conta a Receber | Sim | Não | Sim | [006-financeiro.md](./relational/006-financeiro.md) |
| `contas_pagar` | Financeiro | Transacional | Transactional | Conta a Pagar | Sim | Não | Não | [006-financeiro.md](./relational/006-financeiro.md) |
| `contas_pagar_status_history` | Financeiro | Histórica | History | Conta a Pagar | Sim | Não | Sim | [006-financeiro.md](./relational/006-financeiro.md) |
| `aprovacoes_despesa` | Financeiro | Transacional | Transactional | Conta a Pagar | Sim | Não | Não | [006-financeiro.md](./relational/006-financeiro.md) |
| `rateios_despesa` | Financeiro | Transacional | Transactional | Conta a Pagar | Sim | Não | Não | [006-financeiro.md](./relational/006-financeiro.md) |
| `lancamentos_extrato_bancario` | Financeiro | Transacional | Transactional | Conta Bancária | Sim | Não | Não | [006-financeiro.md](./relational/006-financeiro.md) |
| `conciliacoes_bancarias` | Financeiro | Transacional | Transactional | Conta Bancária | Sim | Não | Não | [006-financeiro.md](./relational/006-financeiro.md) |
| `estornos_financeiros` | Financeiro | Transacional | Transactional | Conta a Receber / Conta a Pagar | Sim | Não | Não | [006-financeiro.md](./relational/006-financeiro.md) |
| `posicoes_caixa` | Financeiro | Read Model | Read Model | Posição de Caixa | Sim | Não | Não | [006-financeiro.md](./relational/006-financeiro.md) |

## Fiscal (11) — [`relational/007-fiscal.md`](./relational/007-fiscal.md)

| Tabela | Módulo | Tipo | Categoria Física | Aggregate | Tenant | Particionada | Histórico | Documento |
|---|---|---|---|---|---|---|---|---|
| `configuracoes_fiscais_tenant` | Fiscal | Configuração | Configuration | Tenant | Sim | Não | Não | [007-fiscal.md](./relational/007-fiscal.md) |
| `ctes` | Fiscal | Transacional | Transactional | CT-e | Sim | Não | Não | [007-fiscal.md](./relational/007-fiscal.md) |
| `ctes_status_history` | Fiscal | Histórica | History | CT-e | Sim | Não | Sim | [007-fiscal.md](./relational/007-fiscal.md) |
| `mdfes` | Fiscal | Transacional | Transactional | MDF-e | Sim | Não | Não | [007-fiscal.md](./relational/007-fiscal.md) |
| `mdfes_ctes` | Fiscal | Junção | Transactional | MDF-e | Não | Não | Não | [007-fiscal.md](./relational/007-fiscal.md) |
| `mdfes_status_history` | Fiscal | Histórica | History | MDF-e | Sim | Não | Sim | [007-fiscal.md](./relational/007-fiscal.md) |
| `ciots` | Fiscal | Transacional | Transactional | CIOT | Sim | Não | Não | [007-fiscal.md](./relational/007-fiscal.md) |
| `ciots_status_history` | Fiscal | Histórica | History | CIOT | Sim | Não | Sim | [007-fiscal.md](./relational/007-fiscal.md) |
| `cartas_correcao` | Fiscal | Transacional | Transactional | CT-e | Sim | Não | Não | [007-fiscal.md](./relational/007-fiscal.md) |
| `nfe_referenciadas` | Fiscal | Transacional | Transactional | CT-e | Sim | Não | Não | [007-fiscal.md](./relational/007-fiscal.md) |
| `eventos_fiscais` | Fiscal | Histórica | History | CT-e / MDF-e / CIOT (polimórfico) | Sim | Sim | Sim | [007-fiscal.md](./relational/007-fiscal.md) |

## Rastreamento (9) — [`relational/008-rastreamento.md`](./relational/008-rastreamento.md)

| Tabela | Módulo | Tipo | Categoria Física | Aggregate | Tenant | Particionada | Histórico | Documento |
|---|---|---|---|---|---|---|---|---|
| `provedores_rastreamento` | Rastreamento | Mestre | Master Data | Provedor de Rastreamento | Sim | Não | Não | [008-rastreamento.md](./relational/008-rastreamento.md) |
| `equipamentos_rastreamento` | Rastreamento | Mestre | Master Data | Equipamento de Rastreamento | Sim | Não | Não | [008-rastreamento.md](./relational/008-rastreamento.md) |
| `origens_localizacao` | Rastreamento | Referência | Master Data | Origem de Localização | Não | Não | Não | [008-rastreamento.md](./relational/008-rastreamento.md) |
| `posicoes_veiculo` | Rastreamento | Time Series | Time Series | Veículo Tracionador | Sim | Sim | Sim | [008-rastreamento.md](./relational/008-rastreamento.md) |
| `leituras_telemetria` | Rastreamento | Time Series | Time Series | Veículo Tracionador | Sim | Sim | Sim | [008-rastreamento.md](./relational/008-rastreamento.md) |
| `heartbeats` | Rastreamento | Time Series | Time Series | Equipamento de Rastreamento | Sim | Sim | Sim | [008-rastreamento.md](./relational/008-rastreamento.md) |
| `cercas_eletronicas` | Rastreamento | Mestre | Master Data | Cerca Eletrônica | Sim | Não | Não | [008-rastreamento.md](./relational/008-rastreamento.md) |
| `eventos_rastreamento` | Rastreamento | Histórica | History | Veículo Tracionador | Sim | Sim | Sim | [008-rastreamento.md](./relational/008-rastreamento.md) |
| `configuracoes_limite_velocidade` | Rastreamento | Configuração | Configuration | Veículo Tracionador | Sim | Não | Não | [008-rastreamento.md](./relational/008-rastreamento.md) |

## App Motorista (5) — [`relational/009-app_motorista.md`](./relational/009-app_motorista.md)

| Tabela | Módulo | Tipo | Categoria Física | Aggregate | Tenant | Particionada | Histórico | Documento |
|---|---|---|---|---|---|---|---|---|
| `sessoes_mobile` | App Motorista | Transacional | Integration | Sessão Mobile | Sim | Não | Não | [009-app_motorista.md](./relational/009-app_motorista.md) |
| `dispositivos_mobile` | App Motorista | Mestre | Integration | Dispositivo Mobile | Sim | Não | Não | [009-app_motorista.md](./relational/009-app_motorista.md) |
| `filas_sincronizacao` | App Motorista | Transacional | Integration | Fila de Sincronização | Sim | Não | Não | [009-app_motorista.md](./relational/009-app_motorista.md) |
| `registros_sincronizacao` | App Motorista | Histórica | Integration | Fila de Sincronização | Sim | Não | Sim | [009-app_motorista.md](./relational/009-app_motorista.md) |
| `assinaturas_digitais` | App Motorista | Mestre | Security | Assinatura Digital | Sim | Não | Não | [009-app_motorista.md](./relational/009-app_motorista.md) |

## Administração (13) — [`relational/010-administracao.md`](./relational/010-administracao.md)

8 entidades adicionais deste módulo (`Tenant`, `Plano`, `Item de Plano`, `Assinatura`, `Cobrança
Recorrente`, `Configuração Regional do Tenant`, `Configuração de Personalização`, `Recurso
Habilitado do Tenant`) já aparecem acima, em Core — não duplicadas aqui.

| Tabela | Módulo | Tipo | Categoria Física | Aggregate | Tenant | Particionada | Histórico | Documento |
|---|---|---|---|---|---|---|---|---|
| `grupos_usuarios` | Administração | Mestre | Security | Grupo de Usuários | Sim | Não | Não | [010-administracao.md](./relational/010-administracao.md) |
| `grupos_usuarios_usuarios` | Administração | Junção | Security | Grupo de Usuários | Não | Não | Não | [010-administracao.md](./relational/010-administracao.md) |
| `convites` | Administração | Transacional | Security | Convite | Sim | Não | Não | [010-administracao.md](./relational/010-administracao.md) |
| `fatores_autenticacao` | Administração | Mestre | Security | Usuário | Sim | Não | Não | [010-administracao.md](./relational/010-administracao.md) |
| `configuracoes_numeracao` | Administração | Configuração | Configuration | Tenant | Sim | Não | Não | [010-administracao.md](./relational/010-administracao.md) |
| `parametros_tenant` | Administração | Configuração | Configuration | Tenant | Sim | Não | Não | [010-administracao.md](./relational/010-administracao.md) |
| `sessoes_acesso` | Administração | Transacional | Security | Usuário | Sim | Não | Não | [010-administracao.md](./relational/010-administracao.md) |
| `tokens_api` | Administração | Mestre | Security | Token de API | Sim | Não | Não | [010-administracao.md](./relational/010-administracao.md) |
| `bloqueios_acesso` | Administração | Transacional | Security | Usuário | Sim | Não | Não | [010-administracao.md](./relational/010-administracao.md) |
| `configuracoes_integracao` | Administração | Configuração | Integration | Tenant | Sim | Não | Não | [010-administracao.md](./relational/010-administracao.md) |
| `webhooks` | Administração | Mestre | Integration | Webhook | Sim | Não | Não | [010-administracao.md](./relational/010-administracao.md) |
| `execucoes_job` | Administração | Histórica | Integration | Job | Sim* | Sim | Sim | [010-administracao.md](./relational/010-administracao.md) |
| `logs_auditoria` | Administração | Histórica | Security | Log de Auditoria | Sim | Sim | Sim | [010-administracao.md](./relational/010-administracao.md) |

## BI (12) — [`relational/011-bi.md`](./relational/011-bi.md)

Módulo somente-leitura (D090) — nenhuma tabela aqui é escrita por rota de negócio, só por
consumidor/agregador assíncrono.

| Tabela | Módulo | Tipo | Categoria Física | Aggregate | Tenant | Particionada | Histórico | Documento |
|---|---|---|---|---|---|---|---|---|
| `metricas` | BI | Configuração | Analytics | Métrica | Sim | Não | Não | [011-bi.md](./relational/011-bi.md) |
| `indicadores_consolidados` | BI | Read Model | Analytics | Indicador Consolidado | Sim | Não | Não | [011-bi.md](./relational/011-bi.md) |
| `snapshots_analiticos` | BI | Read Model | Analytics | Snapshot Analítico | Sim | Não | Não | [011-bi.md](./relational/011-bi.md) |
| `snapshots_analiticos_indicadores` | BI | Junção | Analytics | Snapshot Analítico | Não | Não | Não | [011-bi.md](./relational/011-bi.md) |
| `cubos_analiticos` | BI | Configuração | Analytics | Cubo Analítico | Sim | Não | Não | [011-bi.md](./relational/011-bi.md) |
| `cubos_analiticos_metricas` | BI | Junção | Analytics | Cubo Analítico | Não | Não | Não | [011-bi.md](./relational/011-bi.md) |
| `dashboards_personalizados` | BI | Mestre | Analytics | Dashboard Personalizado | Sim | Não | Não | [011-bi.md](./relational/011-bi.md) |
| `filtros_favoritos` | BI | Mestre | Analytics | Filtro Favorito | Sim | Não | Não | [011-bi.md](./relational/011-bi.md) |
| `relatorios_salvos` | BI | Mestre | Analytics | Relatório Salvo | Sim | Não | Não | [011-bi.md](./relational/011-bi.md) |
| `relatorios_salvos_metricas` | BI | Junção | Analytics | Relatório Salvo | Não | Não | Não | [011-bi.md](./relational/011-bi.md) |
| `exportacoes_geradas` | BI | Transacional | Analytics | Exportação Gerada | Sim | Não | Não | [011-bi.md](./relational/011-bi.md) |
| `agendamentos_atualizacao` | BI | Configuração | Analytics | Agendamento de Atualização | Sim | Não | Não | [011-bi.md](./relational/011-bi.md) |

## IA (8) — [`relational/012-ia.md`](./relational/012-ia.md)

| Tabela | Módulo | Tipo | Categoria Física | Aggregate | Tenant | Particionada | Histórico | Documento |
|---|---|---|---|---|---|---|---|---|
| `modelos_ia` | IA | Configuração | AI | Modelo de IA | Sim* | Não | Não | [012-ia.md](./relational/012-ia.md) |
| `inferencias_ia` | IA | Histórica | AI | Inferência de IA | Sim | Sim | Sim | [012-ia.md](./relational/012-ia.md) |
| `sugestoes_ia` | IA | Transacional | AI | Sugestão de IA | Sim | Não | Não | [012-ia.md](./relational/012-ia.md) |
| `predicoes_ia` | IA | Transacional | AI | Predição de IA | Sim | Não | Não | [012-ia.md](./relational/012-ia.md) |
| `classificacoes_ia` | IA | Transacional | AI | Classificação de IA | Sim | Não | Não | [012-ia.md](./relational/012-ia.md) |
| `anomalias_detectadas` | IA | Transacional | AI | Anomalia Detectada | Sim | Não | Não | [012-ia.md](./relational/012-ia.md) |
| `leituras_visao_computacional` | IA | Transacional | AI | Leitura de Visão Computacional | Sim | Não | Não | [012-ia.md](./relational/012-ia.md) |
| `feedbacks_ia` | IA | Transacional | AI | Feedback de IA (D192) | Sim | Não | Não | [012-ia.md](./relational/012-ia.md) |

---

## Totais por Tipo

| Tipo | Quantidade |
|---|---|
| Mestre | 37 |
| Transacional | 45 |
| Histórica | 14 |
| Read Model | 4 |
| Time Series | 4 |
| Configuração | 21 |
| Junção | 8 |
| Referência | 2 |
| **Total** | **135** |

Nota de reconciliação: `planos`/`itens_plano` são Platform Reference Data quanto a `tenant_id`
(D046 — sem `tenant_id`) mas são classificadas como **Configuração**, não Referência (que fica só
com `permissoes` e `origens_localizacao`), porque seu conteúdo é definido pela operadora da
plataforma e muda com o roadmap comercial (novos planos), não é um catálogo geográfico/normativo
estático. Distinção de Tipo (o que a tabela representa) é ortogonal à de Tenant (quem é dono da
linha) — mantidas separadas de propósito.

## Totais por Categoria Física

| Categoria Física | Quantidade |
|---|---|
| Core | 12 |
| Security | 14 |
| Master Data | 23 |
| Transactional | 32 |
| History | 10 |
| Time Series | 4 |
| Read Model | 2 |
| Configuration | 11 |
| Integration | 7 |
| Analytics | 12 |
| AI | 8 |
| **Total** | **135** |

## Totais por Módulo

| Módulo | Tabelas |
|---|---|
| Core | 15 |
| Cadastros | 8 |
| Operação (incl. `anexos`/`comentarios` compartilhados) | 19 |
| Frota | 12 |
| Manutenção | 9 |
| Financeiro | 14 |
| Fiscal | 11 |
| Rastreamento | 9 |
| App Motorista | 5 |
| Administração (excl. as 8 já contadas em Core) | 13 |
| BI | 12 |
| IA | 8 |
| **Total** | **135** |

## Como este documento cresce

Estável enquanto o Modelo Relacional não muda. Qualquer nova tabela criada num `relational/NNN.md`
precisa ganhar uma linha aqui na mesma revisão — nunca um índice deixado para depois (mesmo cuidado
já aplicado a `ENTITY_CATALOG.md`/`HIGH_VOLUME_ENTITIES.md`). Próximo documento da sequência:
[`FOREIGN_KEYS.md`](./FOREIGN_KEYS.md), agrupado por módulo.
