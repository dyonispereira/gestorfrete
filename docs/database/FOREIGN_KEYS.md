# FOREIGN_KEYS.md — Chaves Estrangeiras do Modelo Relacional

Índice completo de toda `REFERENCES` física dos 12 arquivos `relational/` (verificado por
extração literal, não por memória — 271 FKs na base de 132 tabelas antes desta preparação, mais a
FK de `funcionarios` criada agora, D196). Agrupado por módulo, não alfabeticamente, para permitir
validar cascatas e ciclos dentro de cada domínio antes de olhar para as dependências cruzadas.

## Política de `ON DELETE`/`ON UPDATE` (D195)

Nenhuma das 271 FKs originais declarava `ON DELETE`/`ON UPDATE` explicitamente — nunca tinha sido
decidido, lote a lote. Antes de preencher as colunas abaixo, fixei uma política única, não ad-hoc:

**`ON UPDATE`: sempre `NO ACTION`.** `id` é `UUID` gerado uma vez e nunca alterado (D175) — a
cláusula nunca dispara na prática. Documentado por completude, não porque algo dependa dela.

**`ON DELETE`: três categorias**, nunca escolhida tabela a tabela sem critério:

| Categoria | Quando se aplica | Efeito |
|---|---|---|
| `RESTRICT` | Padrão para toda FK **obrigatória** a uma entidade independente — a linha filha não é "dona" do ciclo de vida do pai (ex: `viagens.cliente_id`, `contas_pagar.fornecedor_id`, `aprovacoes_custo.ator_id`, `tenant_id` em toda tabela, sempre, mesmo quando a coluna é opcional) | Bloqueia a exclusão do pai enquanto existir referência |
| `SET NULL` | Padrão para toda FK **opcional** (nullable) — exceto `tenant_id`, que nunca é `SET NULL` mesmo quando opcional (nulidade ali é decisão de escrita — "recurso de plataforma" — nunca efeito colateral de `DELETE`) | Remove só o vínculo, a linha filha continua existindo |
| `CASCADE` | Exceção explícita — linha cujo ciclo de vida é 100% possuído por um único pai, sem sentido isolada: histórico de status, item de lista, tabela de junção pura, registro que é "sobre" um usuário (não "feito por" um usuário — `fatores_autenticacao`, `sessoes_acesso`, `bloqueios_acesso`), artefato pessoal (`dashboards_personalizados`, `filtros_favoritos`, `relatorios_salvos`) | A linha filha desaparece junto com o pai |

Coerente com D001: nada é fisicamente excluído no fluxo normal da aplicação (soft delete sempre) —
`ON DELETE` aqui é defesa para o caso excepcional (purga administrativa, reset de ambiente de
teste/staging), não um mecanismo do dia a dia. A distinção "sobre" vs. "feito por" um usuário
importa especialmente para `usuario_id`: quando a linha existe *por causa* daquele usuário
especificamente (uma sessão, um fator de autenticação, um dashboard pessoal), é `CASCADE`; quando o
usuário é só quem *executou* uma ação sobre algo que tem valor independente dele (uma aprovação, um
comentário), é `RESTRICT` — apagar o ator não deveria apagar silenciosamente o registro da decisão.

`tenant_id` **nunca** é `CASCADE` em nenhuma tabela — um `tenant` nunca é fisicamente excluído no
fluxo normal (D001), e mesmo no caso excepcional de purga administrativa, cascatear a remoção de um
tenant automaticamente por FK seria o oposto do que D174/TENANCY_MODEL.md pedem: isolamento
auditável, nunca uma operação silenciosa em massa.

---

## Core (`relational/001-core.md`)

| Origem | Coluna | Destino | ON DELETE | ON UPDATE | Obrigatória |
|---|---|---|---|---|---|
| `usuarios` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `usuarios` | `motorista_id` | `motoristas(id)` | SET NULL | NO ACTION | Não |
| `usuarios` | `funcionario_id` | `funcionarios(id)` | SET NULL | NO ACTION | Não |
| `papeis` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `papel_permissao` | `papel_id` | `papeis(id)` | CASCADE | NO ACTION | Sim |
| `papel_permissao` | `permissao_id` | `permissoes(id)` | CASCADE | NO ACTION | Sim |
| `usuarios_papeis` | `usuario_id` | `usuarios(id)` | CASCADE | NO ACTION | Sim |
| `usuarios_papeis` | `papel_id` | `papeis(id)` | CASCADE | NO ACTION | Sim |
| `itens_plano` | `plano_id` | `planos(id)` | CASCADE | NO ACTION | Sim |
| `assinaturas` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `assinaturas` | `plano_id` | `planos(id)` | RESTRICT | NO ACTION | Sim |
| `assinaturas_status_history` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `assinaturas_status_history` | `assinatura_id` | `assinaturas(id)` | CASCADE | NO ACTION | Sim |
| `cobrancas_recorrentes` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `cobrancas_recorrentes` | `assinatura_id` | `assinaturas(id)` | CASCADE | NO ACTION | Sim |
| `recursos_habilitados_tenant` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `filiais` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `configuracoes_regionais_tenant` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `configuracoes_personalizacao` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |

`usuarios.funcionario_id` → `funcionarios(id)`: tabela criada agora em `002-cadastros.md` (D196) —
até esta preparação de `FOREIGN_KEYS.md`, essa FK apontava para uma tabela inexistente.

## Cadastros (`relational/002-cadastros.md`)

| Origem | Coluna | Destino | ON DELETE | ON UPDATE | Obrigatória |
|---|---|---|---|---|---|
| `enderecos` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `clientes` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `contatos_cliente` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `contatos_cliente` | `cliente_id` | `clientes(id)` | CASCADE | NO ACTION | Sim |
| `motoristas` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `documentos_motorista` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `documentos_motorista` | `motorista_id` | `motoristas(id)` | CASCADE | NO ACTION | Sim |
| `funcionarios` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `fornecedores` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `centros_custo` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `centros_custo` | `filial_id` | `filiais(id)` | SET NULL | NO ACTION | Não |

`enderecos.entidade_id`/`comentarios.entidade_id`/`anexos.entidade_id`/`logs_auditoria.entidade_id`
(e demais polimórficas do sistema) **não aparecem aqui** — são referências sem FK física por design
(PostgreSQL não suporta FK condicional), integridade garantida na aplicação, já documentado em cada
arquivo de origem. `FOREIGN_KEYS.md` lista só FKs físicas de verdade.

## Operação (`relational/003-operacao.md`)

| Origem | Coluna | Destino | ON DELETE | ON UPDATE | Obrigatória |
|---|---|---|---|---|---|
| `anexos` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `comentarios` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `comentarios` | `usuario_id` | `usuarios(id)` | RESTRICT | NO ACTION | Sim |
| `viagens` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `viagens` | `cliente_id` | `clientes(id)` | RESTRICT | NO ACTION | Sim |
| `viagens` | `motorista_id` | `motoristas(id)` | SET NULL | NO ACTION | Não |
| `viagens` | `veiculo_tracionador_id` | `veiculos_tracionadores(id)` | SET NULL | NO ACTION | Não |
| `viagem_status_history` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `viagem_status_history` | `viagem_id` | `viagens(id)` | CASCADE | NO ACTION | Sim |
| `alocacoes_recurso_viagem` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `alocacoes_recurso_viagem` | `viagem_id` | `viagens(id)` | CASCADE | NO ACTION | Sim |
| `alocacoes_recurso_viagem` | `motorista_id` | `motoristas(id)` | RESTRICT | NO ACTION | Sim |
| `alocacoes_recurso_viagem` | `veiculo_tracionador_id` | `veiculos_tracionadores(id)` | RESTRICT | NO ACTION | Sim |
| `alocacoes_recurso_viagem` | `implemento_id` | `implementos(id)` | SET NULL | NO ACTION | Não |
| `pontos_parada_viagem` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `pontos_parada_viagem` | `viagem_id` | `viagens(id)` | CASCADE | NO ACTION | Sim |
| `entregas` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `entregas` | `viagem_id` | `viagens(id)` | CASCADE | NO ACTION | Sim |
| `janelas_entrega` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `janelas_entrega` | `entrega_id` | `entregas(id)` | CASCADE | NO ACTION | Sim |
| `coletas` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `coletas` | `viagem_id` | `viagens(id)` | CASCADE | NO ACTION | Sim |
| `ocorrencias` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `ocorrencias` | `viagem_id` | `viagens(id)` | CASCADE | NO ACTION | Sim |
| `romaneios` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `romaneios` | `viagem_id` | `viagens(id)` | CASCADE | NO ACTION | Sim |
| `itens_carga` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `itens_carga` | `romaneio_id` | `romaneios(id)` | CASCADE | NO ACTION | Sim |
| `canhotos` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `canhotos` | `entrega_id` | `entregas(id)` | CASCADE | NO ACTION | Sim |
| `contratos_frete` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `contratos_frete` | `cliente_id` | `clientes(id)` | RESTRICT | NO ACTION | Sim |
| `contratos_frete` | `tabela_preco_id` | `tabelas_preco(id)` | SET NULL | NO ACTION | Não |
| `cotacoes` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `cotacoes` | `cliente_id` | `clientes(id)` | RESTRICT | NO ACTION | Sim |
| `cotacoes` | `contrato_frete_id` | `contratos_frete(id)` | SET NULL | NO ACTION | Não |
| `itens_cotacao` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `itens_cotacao` | `cotacao_id` | `cotacoes(id)` | CASCADE | NO ACTION | Sim |
| `solicitacoes_frete` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `solicitacoes_frete` | `cliente_id` | `clientes(id)` | RESTRICT | NO ACTION | Sim |
| `tabelas_preco` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `tabelas_preco` | `cliente_id` | `clientes(id)` | SET NULL | NO ACTION | Não |
| `itens_tabela_preco` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `itens_tabela_preco` | `tabela_preco_id` | `tabelas_preco(id)` | CASCADE | NO ACTION | Sim |

## Frota (`relational/004-frota.md`)

| Origem | Coluna | Destino | ON DELETE | ON UPDATE | Obrigatória |
|---|---|---|---|---|---|
| `categorias_veiculo` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `veiculos_tracionadores` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `veiculos_tracionadores` | `categoria_veiculo_id` | `categorias_veiculo(id)` | RESTRICT | NO ACTION | Sim |
| `veiculos_tracionadores` | `filial_id` | `filiais(id)` | SET NULL | NO ACTION | Não |
| `implementos` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `implementos` | `categoria_veiculo_id` | `categorias_veiculo(id)` | RESTRICT | NO ACTION | Sim |
| `composicoes_veiculares` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `composicoes_veiculares` | `veiculo_tracionador_id` | `veiculos_tracionadores(id)` | CASCADE | NO ACTION | Sim |
| `composicoes_veiculares_implementos` | `composicao_veicular_id` | `composicoes_veiculares(id)` | CASCADE | NO ACTION | Sim |
| `composicoes_veiculares_implementos` | `implemento_id` | `implementos(id)` | CASCADE | NO ACTION | Sim |
| `fichas_tecnicas_veiculo` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `fichas_tecnicas_veiculo` | `veiculo_tracionador_id` | `veiculos_tracionadores(id)` | CASCADE | NO ACTION | Sim |
| `documentos_veiculo` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `documentos_veiculo` | `veiculo_tracionador_id` | `veiculos_tracionadores(id)` | CASCADE | NO ACTION | Sim |
| `apolices_seguro_veicular` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `apolices_seguro_veicular` | `veiculo_tracionador_id` | `veiculos_tracionadores(id)` | CASCADE | NO ACTION | Sim |
| `apolices_seguro_veicular` | `seguradora_id` | `seguradoras(id)` | RESTRICT | NO ACTION | Sim |
| `seguradoras` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `licenciamentos_veiculo` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `licenciamentos_veiculo` | `veiculo_tracionador_id` | `veiculos_tracionadores(id)` | CASCADE | NO ACTION | Sim |
| `leituras_hodometro` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `leituras_hodometro` | `veiculo_tracionador_id` | `veiculos_tracionadores(id)` | CASCADE | NO ACTION | Sim |
| `leituras_hodometro` | `viagem_id` | `viagens(id)` | SET NULL | NO ACTION | Não |
| `disponibilidade_veiculo` | `veiculo_tracionador_id` | `veiculos_tracionadores(id)` | CASCADE | NO ACTION | Sim |
| `disponibilidade_veiculo` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `disponibilidade_veiculo` | `motorista_atual_id` | `motoristas(id)` | SET NULL | NO ACTION | Não |
| `disponibilidade_veiculo` | `implemento_atual_id` | `implementos(id)` | SET NULL | NO ACTION | Não |

`disponibilidade_veiculo.veiculo_tracionador_id` é `PRIMARY KEY REFERENCES` (1:1) — `CASCADE`
porque o read model não tem nenhum sentido sem o veículo que ele descreve.

## Manutenção (`relational/005-manutencao.md`)

| Origem | Coluna | Destino | ON DELETE | ON UPDATE | Obrigatória |
|---|---|---|---|---|---|
| `tipos_servico` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `planos_manutencao_preventiva` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `planos_manutencao_preventiva` | `veiculo_tracionador_id` | `veiculos_tracionadores(id)` | SET NULL | NO ACTION | Não |
| `planos_manutencao_preventiva` | `categoria_veiculo_id` | `categorias_veiculo(id)` | SET NULL | NO ACTION | Não |
| `planos_manutencao_preventiva` | `tipo_servico_id` | `tipos_servico(id)` | RESTRICT | NO ACTION | Sim |
| `ordens_servico` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `ordens_servico` | `veiculo_tracionador_id` | `veiculos_tracionadores(id)` | RESTRICT | NO ACTION | Sim |
| `ordens_servico` | `composicao_veicular_id` | `composicoes_veiculares(id)` | SET NULL | NO ACTION | Não |
| `ordens_servico` | `fornecedor_executor_id` | `fornecedores(id)` | SET NULL | NO ACTION | Não |
| `ordens_servico` | `mecanico_id` | `usuarios(id)` | SET NULL | NO ACTION | Não |
| `ordens_servico_status_history` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `ordens_servico_status_history` | `ordem_servico_id` | `ordens_servico(id)` | CASCADE | NO ACTION | Sim |
| `itens_ordem_servico` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `itens_ordem_servico` | `ordem_servico_id` | `ordens_servico(id)` | CASCADE | NO ACTION | Sim |
| `itens_ordem_servico` | `peca_estoque_id` | `pecas_estoque(id)` | SET NULL | NO ACTION | Não |
| `aprovacoes_custo` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `aprovacoes_custo` | `ordem_servico_id` | `ordens_servico(id)` | CASCADE | NO ACTION | Sim |
| `aprovacoes_custo` | `ator_id` | `usuarios(id)` | RESTRICT | NO ACTION | Sim |
| `solicitacoes_peca` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `solicitacoes_peca` | `ordem_servico_id` | `ordens_servico(id)` | CASCADE | NO ACTION | Sim |
| `solicitacoes_peca` | `fornecedor_id` | `fornecedores(id)` | RESTRICT | NO ACTION | Sim |
| `pecas_estoque` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `movimentacoes_estoque` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `movimentacoes_estoque` | `peca_estoque_id` | `pecas_estoque(id)` | RESTRICT | NO ACTION | Sim |
| `movimentacoes_estoque` | `ordem_servico_id` | `ordens_servico(id)` | SET NULL | NO ACTION | Não |

## Financeiro (`relational/006-financeiro.md`)

| Origem | Coluna | Destino | ON DELETE | ON UPDATE | Obrigatória |
|---|---|---|---|---|---|
| `formas_pagamento` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `plano_contas` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `plano_contas` | `categoria_pai_id` | `plano_contas(id)` | SET NULL | NO ACTION | Não |
| `contas_bancarias` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `faturas` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `faturas` | `viagem_id` | `viagens(id)` | SET NULL | NO ACTION | Não |
| `faturas` | `entrega_id` | `entregas(id)` | SET NULL | NO ACTION | Não |
| `faturas` | `cliente_id` | `clientes(id)` | RESTRICT | NO ACTION | Sim |
| `faturas` | `forma_pagamento_id` | `formas_pagamento(id)` | RESTRICT | NO ACTION | Sim |
| `contas_receber` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `contas_receber` | `fatura_id` | `faturas(id)` | RESTRICT | NO ACTION | Sim |
| `contas_receber_status_history` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `contas_receber_status_history` | `conta_receber_id` | `contas_receber(id)` | CASCADE | NO ACTION | Sim |
| `contas_pagar` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `contas_pagar` | `fornecedor_id` | `fornecedores(id)` | RESTRICT | NO ACTION | Sim |
| `contas_pagar` | `centro_custo_id` | `centros_custo(id)` | RESTRICT | NO ACTION | Sim |
| `contas_pagar` | `viagem_id` | `viagens(id)` | SET NULL | NO ACTION | Não |
| `contas_pagar` | `ordem_servico_id` | `ordens_servico(id)` | SET NULL | NO ACTION | Não |
| `contas_pagar` | `plano_contas_id` | `plano_contas(id)` | RESTRICT | NO ACTION | Sim |
| `contas_pagar_status_history` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `contas_pagar_status_history` | `conta_pagar_id` | `contas_pagar(id)` | CASCADE | NO ACTION | Sim |
| `aprovacoes_despesa` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `aprovacoes_despesa` | `conta_pagar_id` | `contas_pagar(id)` | CASCADE | NO ACTION | Sim |
| `aprovacoes_despesa` | `ator_id` | `usuarios(id)` | RESTRICT | NO ACTION | Sim |
| `rateios_despesa` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `rateios_despesa` | `conta_pagar_id` | `contas_pagar(id)` | CASCADE | NO ACTION | Sim |
| `rateios_despesa` | `centro_custo_id` | `centros_custo(id)` | SET NULL | NO ACTION | Não |
| `rateios_despesa` | `viagem_id` | `viagens(id)` | SET NULL | NO ACTION | Não |
| `lancamentos_extrato_bancario` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `lancamentos_extrato_bancario` | `conta_bancaria_id` | `contas_bancarias(id)` | RESTRICT | NO ACTION | Sim |
| `conciliacoes_bancarias` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `conciliacoes_bancarias` | `lancamento_extrato_id` | `lancamentos_extrato_bancario(id)` | CASCADE | NO ACTION | Sim |
| `conciliacoes_bancarias` | `conta_pagar_id` | `contas_pagar(id)` | SET NULL | NO ACTION | Não |
| `conciliacoes_bancarias` | `conta_receber_id` | `contas_receber(id)` | SET NULL | NO ACTION | Não |
| `estornos_financeiros` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `estornos_financeiros` | `fatura_id` | `faturas(id)` | SET NULL | NO ACTION | Não |
| `estornos_financeiros` | `conta_pagar_id` | `contas_pagar(id)` | SET NULL | NO ACTION | Não |
| `estornos_financeiros` | `conta_receber_id` | `contas_receber(id)` | SET NULL | NO ACTION | Não |
| `posicoes_caixa` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |

## Fiscal (`relational/007-fiscal.md`)

| Origem | Coluna | Destino | ON DELETE | ON UPDATE | Obrigatória |
|---|---|---|---|---|---|
| `configuracoes_fiscais_tenant` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `ctes` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `ctes` | `viagem_id` | `viagens(id)` | RESTRICT | NO ACTION | Sim |
| `ctes_status_history` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `ctes_status_history` | `cte_id` | `ctes(id)` | CASCADE | NO ACTION | Sim |
| `mdfes` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `mdfes` | `viagem_id` | `viagens(id)` | RESTRICT | NO ACTION | Sim |
| `mdfes_ctes` | `mdfe_id` | `mdfes(id)` | CASCADE | NO ACTION | Sim |
| `mdfes_ctes` | `cte_id` | `ctes(id)` | CASCADE | NO ACTION | Sim |
| `mdfes_status_history` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `mdfes_status_history` | `mdfe_id` | `mdfes(id)` | CASCADE | NO ACTION | Sim |
| `ciots` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `ciots` | `viagem_id` | `viagens(id)` | RESTRICT | NO ACTION | Sim |
| `ciots` | `motorista_id` | `motoristas(id)` | RESTRICT | NO ACTION | Sim |
| `ciots_status_history` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `ciots_status_history` | `ciot_id` | `ciots(id)` | CASCADE | NO ACTION | Sim |
| `cartas_correcao` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `cartas_correcao` | `cte_id` | `ctes(id)` | CASCADE | NO ACTION | Sim |
| `nfe_referenciadas` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `nfe_referenciadas` | `cte_id` | `ctes(id)` | CASCADE | NO ACTION | Sim |
| `eventos_fiscais` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |

`ctes`/`mdfes`/`ciots.viagem_id` são `RESTRICT`, não `CASCADE`, apesar de nascerem de uma Viagem —
documento fiscal emitido tem existência legal própria (retenção obrigatória por prazo fiscal,
independente do que acontece com a Viagem operacional); a Viagem nunca deveria poder "levar junto"
um CT-e já emitido. `eventos_fiscais.entidade_id` (CT-e/MDF-e/CIOT) é polimórfico, sem FK física —
mesma exceção documentada em `Cadastros` acima.

## Rastreamento (`relational/008-rastreamento.md`)

| Origem | Coluna | Destino | ON DELETE | ON UPDATE | Obrigatória |
|---|---|---|---|---|---|
| `provedores_rastreamento` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `equipamentos_rastreamento` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `equipamentos_rastreamento` | `provedor_rastreamento_id` | `provedores_rastreamento(id)` | RESTRICT | NO ACTION | Sim |
| `equipamentos_rastreamento` | `veiculo_tracionador_id` | `veiculos_tracionadores(id)` | SET NULL | NO ACTION | Não |
| `posicoes_veiculo` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `posicoes_veiculo` | `origem_localizacao_id` | `origens_localizacao(id)` | RESTRICT | NO ACTION | Sim |
| `leituras_telemetria` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `heartbeats` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `heartbeats` | `equipamento_rastreamento_id` | `equipamentos_rastreamento(id)` | CASCADE | NO ACTION | Sim |
| `cercas_eletronicas` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `cercas_eletronicas` | `cliente_id` | `clientes(id)` | SET NULL | NO ACTION | Não |
| `cercas_eletronicas` | `filial_id` | `filiais(id)` | SET NULL | NO ACTION | Não |
| `eventos_rastreamento` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `eventos_rastreamento` | `cerca_eletronica_id` | `cercas_eletronicas(id)` | SET NULL | NO ACTION | Não |
| `configuracoes_limite_velocidade` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `configuracoes_limite_velocidade` | `categoria_veiculo_id` | `categorias_veiculo(id)` | SET NULL | NO ACTION | Não |

`posicoes_veiculo`/`leituras_telemetria.veiculo_tracionador_id` não aparecem aqui porque a coluna é
`UUID NOT NULL` **sem** `REFERENCES` física — mesmo padrão de alta frequência já aceito para colunas
de Time Series (D191), integridade garantida pela aplicação/pipeline de ingestão, não pelo banco,
por custo de verificação de FK em volume "Muito Alto".

## App Motorista (`relational/009-app_motorista.md`)

| Origem | Coluna | Destino | ON DELETE | ON UPDATE | Obrigatória |
|---|---|---|---|---|---|
| `sessoes_mobile` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `sessoes_mobile` | `motorista_id` | `motoristas(id)` | RESTRICT | NO ACTION | Sim |
| `sessoes_mobile` | `veiculo_tracionador_id` | `veiculos_tracionadores(id)` | RESTRICT | NO ACTION | Sim |
| `sessoes_mobile` | `dispositivo_mobile_id` | `dispositivos_mobile(id)` | RESTRICT | NO ACTION | Sim |
| `sessoes_mobile` | `revogado_por` | `usuarios(id)` | SET NULL | NO ACTION | Não |
| `dispositivos_mobile` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `dispositivos_mobile` | `motorista_id` | `motoristas(id)` | RESTRICT | NO ACTION | Sim |
| `filas_sincronizacao` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `filas_sincronizacao` | `sessao_mobile_id` | `sessoes_mobile(id)` | CASCADE | NO ACTION | Sim |
| `registros_sincronizacao` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `registros_sincronizacao` | `sessao_mobile_id` | `sessoes_mobile(id)` | CASCADE | NO ACTION | Sim |
| `assinaturas_digitais` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |

## Administração (`relational/010-administracao.md`)

| Origem | Coluna | Destino | ON DELETE | ON UPDATE | Obrigatória |
|---|---|---|---|---|---|
| `grupos_usuarios` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `grupos_usuarios_usuarios` | `grupo_usuarios_id` | `grupos_usuarios(id)` | CASCADE | NO ACTION | Sim |
| `grupos_usuarios_usuarios` | `usuario_id` | `usuarios(id)` | CASCADE | NO ACTION | Sim |
| `convites` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `convites` | `papel_id` | `papeis(id)` | RESTRICT | NO ACTION | Sim |
| `fatores_autenticacao` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `fatores_autenticacao` | `usuario_id` | `usuarios(id)` | CASCADE | NO ACTION | Sim |
| `configuracoes_numeracao` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `parametros_tenant` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `sessoes_acesso` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `sessoes_acesso` | `usuario_id` | `usuarios(id)` | CASCADE | NO ACTION | Sim |
| `tokens_api` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `tokens_api` | `usuario_tecnico_id` | `usuarios(id)` | RESTRICT | NO ACTION | Sim |
| `bloqueios_acesso` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `bloqueios_acesso` | `usuario_id` | `usuarios(id)` | CASCADE | NO ACTION | Sim |
| `configuracoes_integracao` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `webhooks` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `webhooks` | `configuracao_integracao_id` | `configuracoes_integracao(id)` | SET NULL | NO ACTION | Não |
| `execucoes_job` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Não |
| `logs_auditoria` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |

`tokens_api.usuario_tecnico_id` é `RESTRICT`, não `CASCADE`, mesmo sendo "sobre" um usuário técnico
— um token de API concedido é uma credencial de acesso ativa; apagar o usuário não deveria revogar
silenciosamente por cascata, o fluxo correto é revogar o token explicitamente primeiro (a aplicação
decide, o banco não decide por ela). `execucoes_job.tenant_id` é a única exceção de obrigatoriedade
de `tenant_id` neste módulo (nulo = job de plataforma, D174 documentado) — ainda assim `RESTRICT`,
nunca `SET NULL`, pela mesma regra geral da política acima.

## BI (`relational/011-bi.md`)

| Origem | Coluna | Destino | ON DELETE | ON UPDATE | Obrigatória |
|---|---|---|---|---|---|
| `metricas` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Não |
| `indicadores_consolidados` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `indicadores_consolidados` | `metrica_id` | `metricas(id)` | RESTRICT | NO ACTION | Sim |
| `snapshots_analiticos` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `snapshots_analiticos` | `usuario_id` | `usuarios(id)` | SET NULL | NO ACTION | Não |
| `snapshots_analiticos_indicadores` | `snapshot_analitico_id` | `snapshots_analiticos(id)` | CASCADE | NO ACTION | Sim |
| `snapshots_analiticos_indicadores` | `indicador_consolidado_id` | `indicadores_consolidados(id)` | CASCADE | NO ACTION | Sim |
| `cubos_analiticos` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `cubos_analiticos_metricas` | `cubo_analitico_id` | `cubos_analiticos(id)` | CASCADE | NO ACTION | Sim |
| `cubos_analiticos_metricas` | `metrica_id` | `metricas(id)` | CASCADE | NO ACTION | Sim |
| `dashboards_personalizados` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `dashboards_personalizados` | `usuario_id` | `usuarios(id)` | CASCADE | NO ACTION | Sim |
| `filtros_favoritos` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `filtros_favoritos` | `usuario_id` | `usuarios(id)` | CASCADE | NO ACTION | Sim |
| `relatorios_salvos` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `relatorios_salvos` | `usuario_id` | `usuarios(id)` | CASCADE | NO ACTION | Sim |
| `relatorios_salvos_metricas` | `relatorio_salvo_id` | `relatorios_salvos(id)` | CASCADE | NO ACTION | Sim |
| `relatorios_salvos_metricas` | `metrica_id` | `metricas(id)` | CASCADE | NO ACTION | Sim |
| `exportacoes_geradas` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `exportacoes_geradas` | `relatorio_salvo_id` | `relatorios_salvos(id)` | SET NULL | NO ACTION | Não |
| `exportacoes_geradas` | `usuario_id` | `usuarios(id)` | RESTRICT | NO ACTION | Sim |
| `agendamentos_atualizacao` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `agendamentos_atualizacao` | `metrica_id` | `metricas(id)` | SET NULL | NO ACTION | Não |
| `agendamentos_atualizacao` | `cubo_analitico_id` | `cubos_analiticos(id)` | SET NULL | NO ACTION | Não |

`dashboards_personalizados`/`filtros_favoritos`/`relatorios_salvos.usuario_id` são `CASCADE` —
artefatos pessoais, sem valor para ninguém além do usuário dono. `exportacoes_geradas.usuario_id` é
`RESTRICT` — é o registro de quem *pediu* uma exportação (auditoria de uso), não um artefato pessoal
editável.

## IA (`relational/012-ia.md`)

| Origem | Coluna | Destino | ON DELETE | ON UPDATE | Obrigatória |
|---|---|---|---|---|---|
| `modelos_ia` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Não |
| `inferencias_ia` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `inferencias_ia` | `modelo_ia_id` | `modelos_ia(id)` | RESTRICT | NO ACTION | Sim |
| `sugestoes_ia` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `sugestoes_ia` | `inferencia_ia_id` | `inferencias_ia(id)` | CASCADE | NO ACTION | Sim |
| `sugestoes_ia` | `usuario_decisao_id` | `usuarios(id)` | SET NULL | NO ACTION | Não |
| `predicoes_ia` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `predicoes_ia` | `inferencia_ia_id` | `inferencias_ia(id)` | CASCADE | NO ACTION | Sim |
| `classificacoes_ia` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `classificacoes_ia` | `inferencia_ia_id` | `inferencias_ia(id)` | CASCADE | NO ACTION | Sim |
| `anomalias_detectadas` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `anomalias_detectadas` | `inferencia_ia_id` | `inferencias_ia(id)` | CASCADE | NO ACTION | Sim |
| `leituras_visao_computacional` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `leituras_visao_computacional` | `inferencia_ia_id` | `inferencias_ia(id)` | CASCADE | NO ACTION | Sim |
| `leituras_visao_computacional` | `usuario_confirmacao_id` | `usuarios(id)` | SET NULL | NO ACTION | Não |
| `feedbacks_ia` | `tenant_id` | `tenants(id)` | RESTRICT | NO ACTION | Sim |
| `feedbacks_ia` | `usuario_id` | `usuarios(id)` | RESTRICT | NO ACTION | Sim |

`inferencias_ia.modelo_ia_id` é `RESTRICT` — um Modelo de IA é referência estável e versionada
(`modelo_ia_versao` já congela a versão usada, D166/D169); não faz sentido apagar um modelo que tem
histórico de inferências vinculado. `feedbacks_ia.usuario_id` é `RESTRICT`, não `CASCADE` — o
feedback é conteúdo de valor para retraining (D192, `RESULTADO_REAL`), não um artefato pessoal do
usuário que o deu.

---

## Totais

| Módulo | FKs próprias |
|---|---|
| Core | 17 |
| Cadastros | 11 |
| Operação | 44 |
| Frota | 27 |
| Manutenção | 25 |
| Financeiro | 39 |
| Fiscal | 21 |
| Rastreamento | 16 |
| App Motorista | 12 |
| Administração | 20 |
| BI | 24 |
| IA | 17 |
| **Total** | **273** |

Contagem exclui referências polimórficas sem FK física (`entidade_tipo`/`entidade_id`, por design,
listadas em cada módulo de origem) e as duas colunas de Time Series sem `REFERENCES`
(`posicoes_veiculo`/`leituras_telemetria.veiculo_tracionador_id`, D191).

## Como este documento cresce

Estável enquanto o Modelo Relacional não muda. Qualquer FK nova criada num `relational/NNN.md`
precisa ganhar uma linha aqui na mesma revisão, com `ON DELETE`/`ON UPDATE` decididos pela política
acima (D195), nunca improvisados. Próximo documento da sequência: [`INDEXES.md`](./INDEXES.md),
agrupado por propósito (PK/FK/UNIQUE/Busca/Time Series/JSONB/Full Text/PostGIS).
