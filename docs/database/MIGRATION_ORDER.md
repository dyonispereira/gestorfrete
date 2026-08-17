# MIGRATION_ORDER.md — Ordem Oficial de Migrations

## 1. Objetivo

Define a ordem oficial de criação do schema físico do GestorFrete — em que sequência cada
`CREATE TYPE`/`CREATE TABLE`/`ALTER TABLE ... ADD CONSTRAINT`/`CREATE INDEX` precisa rodar para que
nenhuma migration falhe por referenciar algo que ainda não existe. Não gera nenhum arquivo de
migration, SQL executável, Docker de banco ou seed real — fecha a **especificação** da ordem;
implementação é etapa futura (Backend). Baseado inteiramente no que já foi auditado e catalogado em
[`TABLES.md`](./TABLES.md), [`FOREIGN_KEYS.md`](./FOREIGN_KEYS.md), [`INDEXES.md`](./INDEXES.md),
[`CONSTRAINTS.md`](./CONSTRAINTS.md) e [`PARTITIONING.md`](./PARTITIONING.md) — nenhum dado novo é
inventado aqui, só ordenado.

## 2. Princípios

1. Toda dependência é criada antes do que depende dela — nunca a aplicação corrigindo depois.
2. Platform Reference Data (D046: `permissoes`, `planos`, `itens_plano`, `origens_localizacao`)
   nasce antes de qualquer tabela de tenant que a referencia, mesmo quando fisicamente documentada
   dentro de um módulo posterior (caso de `origens_localizacao`, ver nota na Onda 09).
3. Extensões PostgreSQL antes de qualquer tipo/coluna que dependa delas (`PostGIS` antes de
   `GEOGRAPHY`, D173).
4. `CREATE TYPE` (enum) sempre antes da coluna que o usa — nunca na mesma migration em ordem
   invertida.
5. Tabela-pai antes de qualquer FK que aponte para ela — com uma exceção explícita e documentada
   quando a dependência é circular por natureza (D203, seção 7).
6. Índice depois da tabela que ele indexa — sempre; `CREATE INDEX CONCURRENTLY` quando a tabela já
   tiver dados em produção (não relevante para a primeira criação de schema, relevante para
   evolução futura em produção).
7. Partição segue exatamente a estratégia de [`PARTITIONING.md`](./PARTITIONING.md) — nunca
   decidida de novo aqui.
8. Seed de dados só depois de toda a estrutura que ele referencia existir — conteúdo do seed fica
   em [`SEED_DATA.md`](./SEED_DATA.md) (próximo documento), aqui só a posição na ordem.
9. **D200 aplicado onda a onda**: nenhuma onda é considerada concluída sem comparar o que foi
   efetivamente criado contra a especificação desta onda — ver seção 12.

## 3. Pré-migration (Onda 00)

Tudo que precisa existir **antes** do primeiro `CREATE TABLE` de negócio:

| Item | O quê | Por quê | Estado |
|---|---|---|---|
| Extensão `pgcrypto` (ou `pg_uuid_ossp`, a confirmar na implementação) | `gen_random_uuid()` | Todo PK do sistema usa `DEFAULT gen_random_uuid()` (D175) | Necessária |
| Extensão `postgis` | Tipo `GEOGRAPHY` | `posicoes_veiculo`, `cercas_eletronicas`, `pontos_parada_viagem`, `coletas` (D173) | Necessária |
| Schemas adicionais | — | **Nenhum** — o projeto usa um único schema `public` (isolamento é por `tenant_id`, D005/D006, não por schema — decisão de fundação, anterior ao Modelo de Domínio) | Não aplicável |
| Functions auxiliares | — | Nenhuma function customizada foi decidida nesta sprint (colunas `GENERATED ALWAYS AS` cobrem todo cálculo derivado de mesma linha, D185) — se um trigger vier a ser necessário (ex: recálculo de `status_aptidao` do Motorista, `disponibilidade_veiculo`), é decisão de Backend/Evento-Processamento (`CONSTRAINTS.md` categoria 3), não uma function de banco definida aqui | Adiado para Backend |
| Triggers | — | Nenhum decidido nesta sprint, mesmo motivo acima | Adiado para Backend |
| Tipos auxiliares não-enum | — | Nenhum (`JSONB`/`GEOGRAPHY`/`UUID`/`TIMESTAMPTZ` são tipos nativos do PostgreSQL/PostGIS, não custom) | Não aplicável |
| `TimescaleDB` | — | Mencionada como caminho de compressão em `PARTITIONING.md` (D173, "TimescaleDB-ready") — **não assumida como obrigatória no primeiro deploy**; se adotada, sua ativação (`CREATE EXTENSION timescaledb` + conversão de tabela para hypertable) é uma migration própria, posterior, avaliada com dado de produção real | Futuro, não decidido agora |

Toda `CREATE TYPE` (enum) roda **dentro da mesma migration da tabela que a usa**, imediatamente
antes do `CREATE TABLE` correspondente — não centralizada numa migration "todos os enums", para que
cada onda continue sendo uma unidade independente e legível (padrão já seguido em todo
`relational/NNN.md`, mantido aqui).

## 4. Ondas de migration

| Onda | Módulo | Depende de |
|---|---|---|
| 00 | Infraestrutura (extensões) | — |
| 01 | Core | Onda 00 |
| 02 | Cadastros | Core |
| 03 | Administração | Core |
| 04 | Frota | Core, Cadastros |
| 05 | Operação | Core, Cadastros, Frota |
| 06 | Manutenção | Frota, Operação |
| 07 | Financeiro | Operação, Cadastros |
| 08 | Fiscal | Operação, Administração |
| 09 | Rastreamento | Frota |
| 10 | App Motorista (Mobile) | Operação, Administração |
| 11 | BI | Todas as anteriores (somente leitura, D090) |
| 12 | IA | Operação, Rastreamento, Manutenção, BI |

Idêntica à matriz "Dependências entre módulos" já fixada em [`DER.md`](./DER.md) — não redecidida
aqui, só confirmada. Auditoria tabela-a-tabela (não só módulo-a-módulo, D200) contra
[`FOREIGN_KEYS.md`](./FOREIGN_KEYS.md) confirma que esta ordem é suficiente para 268 das 271 FKs do
sistema — as 3 exceções (`usuarios.motorista_id`, `usuarios.funcionario_id`,
`leituras_hodometro.viagem_id`) são exatamente D203, tratadas explicitamente na seção 7, nunca
ignoradas.

## 5. Dentro de cada onda

Uma tabela por linha, agrupada por onda. "Depende de" lista só as tabelas fora da própria onda —
dependências dentro da mesma onda (ex.: `contatos_cliente` → `clientes`) já são garantidas pela
ordem de criação dentro do arquivo `relational/NNN.md` correspondente, não repetidas aqui. FKs,
índices e constraints de cada tabela já estão 100% catalogados em `FOREIGN_KEYS.md`/`INDEXES.md`/
`CONSTRAINTS.md` — não duplicados linha a linha aqui (D069); só uma tabela é anotada quando tem uma
observação que a ordem de migration precisa saber.

### Onda 01 — Core

| Tabela | Depende de (fora da onda) | Observação |
|---|---|---|
| `tenants` | — | Raiz de toda a hierarquia |
| `permissoes` | — | Platform Reference Data (D046) — sem `tenant_id` |
| `planos`, `itens_plano` | — | Platform Reference Data |
| `usuarios` | — | **Ver D203** — `motorista_id`/`funcionario_id` referenciam Onda 02, FK adicionada depois |
| `papeis`, `papel_permissao` | — | |
| `usuarios_papeis` | `usuarios`, `papeis` (mesma onda) | D222 — gap retroativo, junção N:N Usuário↔Papel |
| `assinaturas`, `cobrancas_recorrentes` | — | |
| `assinaturas_status_history` | `assinaturas` (mesma onda) | D269 — gap retroativo, histórico D017/D018 nunca materializado |
| `recursos_habilitados_tenant`, `filiais`, `configuracoes_regionais_tenant`, `configuracoes_personalizacao` | — | |

### Onda 02 — Cadastros

| Tabela | Depende de (fora da onda) | Observação |
|---|---|---|
| `enderecos` | — | Referência polimórfica sem FK física (D182) |
| `clientes`, `contatos_cliente` | — | |
| `motoristas` | — | **Ver D203** — alvo do FK adiado de `usuarios` |
| `documentos_motorista` | — | |
| `funcionarios` | — | **Ver D203** — alvo do FK adiado de `usuarios` (D196) |
| `fornecedores` | — | |
| `centros_custo` | `filiais` (Onda 01) | |

**Passo de fechamento da Onda 02**: `ALTER TABLE usuarios ADD CONSTRAINT fk_usuarios_motorista_id FOREIGN KEY (motorista_id) REFERENCES motoristas(id)`, idem para `funcionario_id` → `funcionarios(id)` — D203.

### Onda 03 — Administração

| Tabela | Depende de (fora da onda) | Observação |
|---|---|---|
| `grupos_usuarios`, `grupos_usuarios_usuarios` | `usuarios` (Onda 01) | |
| `convites` | `papeis` (Onda 01) | |
| `fatores_autenticacao`, `sessoes_acesso`, `tokens_api`, `bloqueios_acesso` | `usuarios` (Onda 01) | |
| `configuracoes_numeracao`, `parametros_tenant`, `configuracoes_integracao` | — | |
| `webhooks` | — | |
| `execucoes_job` | — | Particionada (ver seção 6) |
| `logs_auditoria` | — | Particionada (ver seção 6); D194 |

### Onda 04 — Frota

| Tabela | Depende de (fora da onda) | Observação |
|---|---|---|
| `categorias_veiculo` | — | |
| `veiculos_tracionadores` | `filiais` (Onda 01) | |
| `implementos` | — | |
| `composicoes_veiculares`, `composicoes_veiculares_implementos` | — | |
| `fichas_tecnicas_veiculo`, `documentos_veiculo`, `licenciamentos_veiculo` | — | |
| `seguradoras`, `apolices_seguro_veicular` | — | |
| `leituras_hodometro` | — | **Ver D203** — `viagem_id` referencia Onda 05, FK adicionada depois; particionada (seção 6) |
| `disponibilidade_veiculo` | `motoristas` (Onda 02) | Read model — nunca escrita por rota de API direta |

**Passo de fechamento da Onda 04**: nenhum (o FK adiado de `leituras_hodometro` fecha ao final da
Onda 05, não da 04 — ver Onda 05).

### Onda 05 — Operação

| Tabela | Depende de (fora da onda) | Observação |
|---|---|---|
| `anexos`, `comentarios` | `usuarios` (Onda 01) | Compartilhadas/polimórficas (D186) |
| `viagens` | `clientes` (Onda 02), `motoristas` (Onda 02), `veiculos_tracionadores` (Onda 04) | |
| `viagem_status_history` | — | Particionada (seção 6) |
| `alocacoes_recurso_viagem` | `motoristas` (Onda 02), `veiculos_tracionadores`/`implementos` (Onda 04) | |
| `pontos_parada_viagem`, `entregas`, `coletas`, `ocorrencias`, `romaneios` | — | |
| `janelas_entrega`, `canhotos` | — | |
| `itens_carga` | — | |
| `contratos_frete`, `cotacoes` | `clientes` (Onda 02) | |
| `itens_cotacao`, `solicitacoes_frete` | `clientes` (Onda 02) | |
| `tabelas_preco`, `itens_tabela_preco` | `clientes` (Onda 02) | |

**Passo de fechamento da Onda 05**: `ALTER TABLE leituras_hodometro ADD CONSTRAINT fk_leituras_hodometro_viagem_id FOREIGN KEY (viagem_id) REFERENCES viagens(id)` — D203, fecha o último FK pendente do sistema.

### Onda 06 — Manutenção

| Tabela | Depende de (fora da onda) | Observação |
|---|---|---|
| `tipos_servico` | — | |
| `planos_manutencao_preventiva` | `veiculos_tracionadores`/`categorias_veiculo` (Onda 04) | |
| `ordens_servico` | `veiculos_tracionadores`/`composicoes_veiculares` (Onda 04), `fornecedores` (Onda 02), `usuarios` (Onda 01) | |
| `ordens_servico_status_history`, `itens_ordem_servico`, `aprovacoes_custo`, `solicitacoes_peca` | — | |
| `pecas_estoque`, `movimentacoes_estoque` | — | |

### Onda 07 — Financeiro

| Tabela | Depende de (fora da onda) | Observação |
|---|---|---|
| `formas_pagamento`, `plano_contas`, `contas_bancarias` | — | |
| `faturas` | `viagens`/`entregas` (Onda 05), `clientes` (Onda 02) | |
| `contas_receber`, `contas_receber_status_history` | — | |
| `contas_pagar` | `fornecedores`/`centros_custo` (Onda 02), `viagens` (Onda 05), `ordens_servico` (Onda 06) | |
| `contas_pagar_status_history`, `aprovacoes_despesa`, `rateios_despesa` | `viagens` (Onda 05), `centros_custo` (Onda 02) | |
| `lancamentos_extrato_bancario`, `conciliacoes_bancarias`, `estornos_financeiros` | — | |
| `posicoes_caixa` | — | Read model |

### Onda 08 — Fiscal

| Tabela | Depende de (fora da onda) | Observação |
|---|---|---|
| `configuracoes_fiscais_tenant` | — | |
| `ctes`, `mdfes` | `viagens` (Onda 05) | |
| `mdfes_ctes` | — | |
| `ctes_status_history`, `mdfes_status_history` | — | |
| `ciots` | `viagens` (Onda 05), `motoristas` (Onda 02) | |
| `ciots_status_history`, `cartas_correcao`, `nfe_referenciadas` | — | |
| `eventos_fiscais` | — | Particionada (seção 6) |

### Onda 09 — Rastreamento

| Tabela | Depende de (fora da onda) | Observação |
|---|---|---|
| `origens_localizacao` | — | Platform Reference Data (D046) — **criada primeiro dentro desta onda**, antes de `posicoes_veiculo`, apesar de fisicamente documentada no mesmo arquivo/módulo (nota de ordenação intra-onda, não um problema de dependência entre ondas) |
| `provedores_rastreamento` | — | |
| `equipamentos_rastreamento` | `provedores_rastreamento` (mesma onda), `veiculos_tracionadores` (Onda 04) | |
| `posicoes_veiculo` | `origens_localizacao` (mesma onda, ver acima) | Particionada + `GiST` (seção 6, D197) |
| `leituras_telemetria` | `veiculos_tracionadores` (Onda 04) | Particionada (seção 6) |
| `heartbeats` | — | Particionada (seção 6) |
| `cercas_eletronicas` | `clientes` (Onda 02), `filiais` (Onda 01) | `GiST` (D197) |
| `eventos_rastreamento` | `veiculos_tracionadores` (Onda 04) | Particionada (seção 6) |
| `configuracoes_limite_velocidade` | `categorias_veiculo` (Onda 04) | |

### Onda 10 — App Motorista (Mobile)

| Tabela | Depende de (fora da onda) | Observação |
|---|---|---|
| `sessoes_mobile` | `motoristas` (Onda 02), `veiculos_tracionadores` (Onda 04), `usuarios` (Onda 01) | |
| `dispositivos_mobile` | `motoristas` (Onda 02) | |
| `filas_sincronizacao`, `registros_sincronizacao` | — | |
| `assinaturas_digitais` | — | |

### Onda 11 — BI

Somente leitura por natureza (D090) — nenhuma tabela desta onda é fonte de verdade, todas dependem
conceitualmente de "tudo que já existe", mas suas FKs físicas apontam só para `usuarios` (Onda 01) e
entre si.

| Tabela | Depende de (fora da onda) | Observação |
|---|---|---|
| `metricas` | — | `tenant_id` opcional (nulo = Platform Reference Data) |
| `indicadores_consolidados` | — | |
| `snapshots_analiticos`, `snapshots_analiticos_indicadores` | `usuarios` (Onda 01) | |
| `cubos_analiticos`, `cubos_analiticos_metricas` | — | |
| `dashboards_personalizados`, `filtros_favoritos`, `relatorios_salvos`, `relatorios_salvos_metricas` | `usuarios` (Onda 01) | |
| `exportacoes_geradas` | `usuarios` (Onda 01) | |
| `agendamentos_atualizacao` | — | |

### Onda 12 — IA

| Tabela | Depende de (fora da onda) | Observação |
|---|---|---|
| `modelos_ia` | — | `tenant_id` opcional (nulo = modelo de plataforma) |
| `inferencias_ia` | — | **Particionada (D201) + referenciada por FK de 5 tabelas desta mesma onda — ver D202 e seção 6/7** |
| `sugestoes_ia`, `predicoes_ia`, `classificacoes_ia`, `anomalias_detectadas`, `leituras_visao_computacional` | `usuarios` (Onda 01) | Todas com FK `NOT NULL` para `inferencias_ia` |
| `feedbacks_ia` | `usuarios` (Onda 01) | |

## 6. Tabelas particionadas

Para cada uma das 10 tabelas de [`PARTITIONING.md`](./PARTITIONING.md), o que a migration precisa
fazer na criação inicial (não redecidido aqui, só sequenciado):

| Tabela | Onda | 1ª partição criada | Partições futuras | Job habilitado | Aceita FK de outras tabelas? | Restrição PostgreSQL específica |
|---|---|---|---|---|---|---|
| `viagem_status_history` | 05 | Mês da migration + os 2 seguintes (look-ahead padrão, `PARTITIONING.md` seção 5) | Job de criação (seção 4 de `PARTITIONING.md`) habilitado ao final da Onda 05 | Ao final da Onda 05 | Não | Nenhuma — PK `id` simples, ninguém referencia esta tabela |
| `leituras_hodometro` | 04 | Idem | Idem, habilitado ao final da Onda 04 | Ao final da Onda 04 | Não | Nenhuma |
| `eventos_fiscais` | 08 | Idem | Idem, Onda 08 | Ao final da Onda 08 | Não | Nenhuma |
| `posicoes_veiculo` | 09 | Idem | Idem, Onda 09 | Ao final da Onda 09 | Não | Nenhuma |
| `leituras_telemetria` | 09 | Idem | Idem, Onda 09 | Ao final da Onda 09 | Não | Nenhuma |
| `heartbeats` | 09 | Idem (por `recebido_em`, exceção D191) | Idem, Onda 09 | Ao final da Onda 09 | Não | Nenhuma |
| `eventos_rastreamento` | 09 | Idem | Idem, Onda 09 | Ao final da Onda 09 | Não | Nenhuma |
| `execucoes_job` | 03 | Idem | Idem, Onda 03 | Ao final da Onda 03 | Não | Nenhuma |
| `logs_auditoria` | 03 | Idem | Idem, Onda 03 | Ao final da Onda 03 | Não | Nenhuma |
| `inferencias_ia` | 12 | Idem | Idem, Onda 12 | Ao final da Onda 12 | **Sim — 5 FKs `NOT NULL`** (`sugestoes_ia`, `predicoes_ia`, `classificacoes_ia`, `anomalias_detectadas`, `leituras_visao_computacional`, todas na própria Onda 12) | **Sim — ver D202/seção 7**: PK precisa incluir a coluna de partição (`data_hora_inicio`) para as 5 FKs serem válidas em PostgreSQL real; a forma exata (`PRIMARY KEY (id, data_hora_inicio)` + as 5 FKs referenciando `(id, data_hora_inicio)` em vez de só `id`, o que exigiria essas 5 tabelas também carregarem `data_hora_inicio` como parte da FK — impacto em cascata não trivial) **não é decidida aqui**, é o item central da seção 7 |

## 7. Problemas conhecidos (pendências técnicas antes da primeira migration)

Nunca resolvidos silenciosamente — cada um é uma decisão explícita ainda em aberto, com dono e
critério de resolução:

| # | Problema | Onda afetada | Resolução proposta | Decisão final |
|---|---|---|---|---|
| 1 | `inferencias_ia` é particionada e recebe FK `NOT NULL` de 5 tabelas na mesma onda — em PostgreSQL real, toda `UNIQUE`/PK de uma tabela particionada precisa incluir a coluna de partição, o que provavelmente obriga `PRIMARY KEY (id, data_hora_inicio)` em vez de só `id`, e as 5 FKs precisariam referenciar essa chave composta (não `id` isolado) | Onda 12 | Validar com um protótipo real (`psql`/ambiente de teste) antes de escrever a migration; se confirmado, as 5 tabelas dependentes carregam `data_hora_inicio` como coluna própria (redundante, mas exigida pela FK composta) — decisão de modelo físico, não de domínio (D202) | **A validar na implementação** — não decidida aqui |
| 2 | `usuarios.motorista_id`/`funcionario_id` (Onda 01) referenciam tabelas da Onda 02 | Onda 01→02 | FK adicionada via `ALTER TABLE` ao final da Onda 02 (D203) | **Resolvida** — ver Onda 02 |
| 3 | `leituras_hodometro.viagem_id` (Onda 04) referencia `viagens` (Onda 05) | Onda 04→05 | FK adicionada via `ALTER TABLE` ao final da Onda 05 (D203) | **Resolvida** — ver Onda 05 |
| 4 | Vigência sem sobreposição (ex.: dois registros de Tabela de Preço vigentes simultâneos para o mesmo Cliente) não tem `EXCLUDE` constraint — só `CHECK`/`UNIQUE` parcial (`CONSTRAINTS.md` categoria 4) | Onda 05 | Avaliar `EXCLUDE USING gist` com faixas de data como evolução futura, não bloqueante para a primeira migration | **Adiado**, não bloqueante |
| 5 | Nenhuma partição `DEFAULT` (rede de segurança) implementada ainda nas 10 tabelas particionadas (`PARTITIONING.md` seção 12) | Ondas 03/04/05/08/09/12 | Adicionar `PARTITION ... DEFAULT` em cada tabela particionada como parte da migration inicial de cada onda, antes de aceitar a primeira escrita real | **A decidir na implementação** — recomendado, não obrigatório |

## 8. Rollback

| Tipo de mudança | Rollback permitido? | Estratégia |
|---|---|---|
| Migration aditiva (nova tabela, nova coluna nullable, novo índice) | Sim, direto | `DROP TABLE`/`DROP COLUMN`/`DROP INDEX` reverte sem perda de dado pré-existente (porque não existia antes) |
| Migration que adiciona `NOT NULL`/`CHECK`/`UNIQUE` numa tabela já populada | Sim, mas exige a migration compensatória ter sido planejada (ver Zero Downtime, seção 9) | Reverter a constraint é seguro; os dados que a violavam (se a migration falhou) nunca chegaram a ser gravados |
| Migration destrutiva (`DROP TABLE`/`DROP COLUMN` com dado real) | **Nunca em produção sem backup validado e janela de confirmação explícita** — mesmo espírito de D001 (nada desaparece por acidente) aplicado à camada de schema, não só de linha | Sempre uma migration compensatória (recriar a partir de backup), nunca um rollback automático de `DROP` |
| Migration de particionamento (nova partição mensal) | Sim, `DROP TABLE <partição>` se vazia; se já tiver dado, tratado como qualquer `DROP` destrutivo acima | — |
| Ordem de onda em si (ex.: perceber depois que Onda 07 devia vir antes da 06) | Não se aplica um "rollback" — é uma nova decisão registrada em `DECISIONS.md`, com nova migration, nunca uma reescrita silenciosa do histórico já aplicado | — |

Regra geral: **toda migration reversível tem seu próprio "down" escrito e testado antes de ir para
produção** (Alembic gera o par `upgrade()`/`downgrade()` por revisão, ver seção 10) — nenhuma
migration é escrita só de ida.

## 9. Zero Downtime

Padrão para qualquer mudança estrutural em uma tabela já em produção (não relevante para a criação
inicial do schema, mas fixado agora para toda evolução futura):

```
1. Adicionar coluna nullable
        ↓
2. Migrar dados (backfill, em lote, fora do horário de pico se o volume exigir)
        ↓
3. Ativar uso (aplicação passa a ler/escrever a nova coluna)
        ↓
4. Tornar obrigatória (ALTER COLUMN ... SET NOT NULL, só depois do backfill 100% completo)
        ↓
5. Remover legado (coluna antiga, só depois de confirmar que nada mais a lê)
```

Nunca pular etapas — em particular, nunca `ALTER TABLE ... ADD COLUMN ... NOT NULL` direto numa
tabela com dado existente (bloqueia a tabela inteira e falha se houver uma única linha
incompatível). Migrations destrutivas (`DROP COLUMN`/`DROP TABLE` com dado real) só depois que a
etapa 5 confirma que nada depende mais do legado.

## 10. Controle de versão

**Alembic** — confirmado no repositório (`apps/api/alembic/`, `apps/api/alembic.ini`, scaffold já
existente) — não um segundo padrão inventado aqui. Alembic não ordena por nome de arquivo, ordena
pela cadeia `revision`/`down_revision` dentro de cada arquivo — a convenção adotada:

- Uma revisão Alembic por onda (`alembic revision --message "onda01_core"` → arquivo
  `<hash>_onda01_core.py`), nunca múltiplas ondas na mesma revisão nem uma onda partida em várias
  revisões.
- `down_revision` sempre aponta para a onda anterior na ordem da seção 4 — a cadeia de revisões
  **é** a ordem de migration, não apenas uma convenção de nome.
- O `slug` (`ondaNN_modulo`) existe para leitura humana ao navegar `alembic/versions/` — a garantia
  real de ordem é a cadeia, não o nome do arquivo.
- FKs adiadas (D203, seção 7) e a habilitação do job de partição (seção 6) são passos dentro da
  revisão da onda de fechamento, não revisões próprias separadas.

## 11. Validação

Toda onda segue o mesmo formato — pré-condição, execução, validação, pós-condição:

**Exemplo — Onda 05 (Operação)**

| Fase | Conteúdo |
|---|---|
| Pré | Onda 04 (Frota) aplicada e validada; `clientes`/`motoristas` (Onda 02) existentes |
| Executa | `anexos`, `comentarios`, `viagens`, `viagem_status_history`, `alocacoes_recurso_viagem`, `pontos_parada_viagem`, `entregas`, `janelas_entrega`, `coletas`, `ocorrencias`, `romaneios`, `itens_carga`, `canhotos`, `contratos_frete`, `cotacoes`, `itens_cotacao`, `solicitacoes_frete`, `tabelas_preco`, `itens_tabela_preco` — 19 tabelas (`TABLES.md`) |
| Valida | Toda FK resolvida (inclui o `ALTER TABLE leituras_hodometro ADD CONSTRAINT` de fechamento, D203); todo índice de `INDEXES.md` presente; toda constraint de `CONSTRAINTS.md` presente; partição de `viagem_status_history` criada com look-ahead correto |
| Pós | `viagens` disponível — Onda 06 (Manutenção) e Onda 07 (Financeiro) podem começar |

O mesmo formato se aplica às demais 12 ondas — não repetido tabela por tabela aqui para não
duplicar `TABLES.md`/`FOREIGN_KEYS.md`/`INDEXES.md`/`CONSTRAINTS.md` linha a linha (D069); a
validação de cada onda é sempre "toda tabela da seção 5 criada, toda FK/índice/constraint/partição
correspondente presente, nenhuma pendência da seção 7 sem uma decisão explícita".

## 12. Critério de conclusão

Uma migration (de uma onda, ou do schema completo) só é considerada concluída quando **todos** os
itens abaixo são verdadeiros — nunca apenas "o arquivo de migration rodou sem erro":

- [ ] DDL aplicada (toda tabela da onda existe)
- [ ] Constraints criadas (`CHECK`/`UNIQUE`/`NOT NULL` — `CONSTRAINTS.md`)
- [ ] FKs resolvidas, incluindo as adiadas por D203 quando a onda de fechamento correspondente for
      alcançada
- [ ] Índices criados (`INDEXES.md`)
- [ ] Partições criadas com o look-ahead correto (`PARTITIONING.md`), job de criação habilitado
- [ ] Seeds necessários executados (quando [`SEED_DATA.md`](./SEED_DATA.md) definir algum para
      aquela onda)
- [ ] Validações da seção 11 passaram (pré/execução/pós-condição)
- [ ] Documentação consistente — nenhum `relational/NNN.md`/`TABLES.md`/`FOREIGN_KEYS.md`/
      `INDEXES.md`/`CONSTRAINTS.md` ficou desatualizado pela migration real
- [ ] **Auditoria D200 executada** — a DDL de fato aplicada no banco (via `\d+`/`information_schema`
      ou equivalente) comparada literalmente contra a especificação desta onda, não assumida por
      coincidência de ter "rodado sem erro"

Este último item vale tanto quanto os outros: uma migration pode rodar sem erro e ainda divergir do
que foi especificado (nome de índice diferente, `ON DELETE` esquecido, etc.) — D200 continua valendo
depois que o SQL existe de verdade, não só enquanto é documentação.

## Como este documento cresce

Estável enquanto o Modelo Relacional não muda. Toda nova tabela/FK/índice/constraint/partição altera
primeiro `relational/NNN.md` e os catálogos correspondentes — só depois ganha uma linha aqui, na
onda certa, com a mesma auditoria D200 antes de considerar a atualização concluída. Próximo
documento da sequência: [`SEED_DATA.md`](./SEED_DATA.md).
