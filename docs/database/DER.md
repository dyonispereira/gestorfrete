# DER.md — Diagrama Entidade-Relacionamento Consolidado

Não repete o DDL já definido em [`relational/`](./relational/) (isso violaria o mesmo princípio de
"não duplicar" usado em toda a documentação, D069-style) — este documento é a **visão consolidada e
navegável** de como as ~135 tabelas físicas se relacionam, em dois níveis, como recomendado:

1. **DER Executivo** — só os agregados principais (~1 por módulo + as ligações entre módulos).
   Leitura para arquitetos/gestores, sem precisar abrir os 12 arquivos relacionais.
2. **DER Completo por módulo** — todas as tabelas de cada módulo, agrupadas exatamente como em
   `relational/NNN-categoria.md`, com o relacionamento resumido. Referência para quem vai
   implementar.

Contagem real: **135 tabelas**, confirmada por contagem literal de `CREATE TABLE` nos 12 arquivos
`relational/` (não "200+" — número honesto, mesmo princípio de não inflar contagem já seguido em
`ENTITY_CATALOG.md`/`RBAC_MATRIX.md`). Nota: `logs_auditoria` (D194), `funcionarios` (D196),
`usuarios_papeis` (D222) e `assinaturas_status_history` (D269, Sprint 10 Lote 7) só passaram a
existir fisicamente durante a preparação de `TABLES.md`/`FOREIGN_KEYS.md`/das APIs de Identidade e
Financeiro — todas eram citadas/especificadas em detalhe alhures (documentação ou o próprio Domain
Model) sem nunca terem `CREATE TABLE` real. Ver [`TABLES.md`](./TABLES.md) para o índice
tabela-a-tabela completo.

---

## 1. DER Executivo

```
                                        tenants
                                           │
      ┌───────────┬───────────┬───────────┼───────────┬───────────┬───────────┐
      │           │           │           │           │           │           │
   usuarios    filiais   assinaturas  parametros_  configuracoes_ recursos_  logs_
      │           │       (→planos)    tenant      personalizacao habilitados_ auditoria
      │           │                                                tenant
      │           └──────────────┐
      │                          ▼
      │                    centros_custo ◄──────────────────┐
      │                                                       │
      ▼                                                       │
   papeis ──N:N── permissoes                          rateios_despesa
                                                                │
   ═══════════════════════ CADASTROS ═══════════════════════  │
      clientes ── enderecos (polimórfico)                     │
      motoristas ── documentos_motorista                      │
      fornecedores                                             │
                                                                │
   ═══════════════════════ OPERAÇÃO (núcleo) ══════════════   │
      cotacoes ──► viagens ◄── motoristas, veiculos_tracionadores
                     │  │
                     │  ├── entregas ── canhotos
                     │  ├── ocorrencias
                     │  ├── viagem_status_history
                     │  ├── alocacoes_recurso_viagem
                     │  └── romaneios ── itens_carga
                     │
                     ├─────► ctes/mdfes/ciots (FISCAL)
                     ├─────► faturas → contas_receber (FINANCEIRO) ◄── rateios_despesa
                     ├─────► ordens_servico (MANUTENÇÃO, quando pane)
                     └─────► posicoes_veiculo/eventos_rastreamento (RASTREAMENTO, leitura)

   ═══════════════════════ FROTA ═══════════════════════════
      veiculos_tracionadores ── fichas_tecnicas_veiculo, documentos_veiculo,
                                  apolices_seguro_veicular, leituras_hodometro
      implementos ── composicoes_veiculares (N:N)
      disponibilidade_veiculo (read model, nunca fonte)

   ═══════════════════════ MANUTENÇÃO ═══════════════════════
      ordens_servico ── itens_ordem_servico, aprovacoes_custo
      planos_manutencao_preventiva ── veiculos_tracionadores

   ═══════════════════════ FINANCEIRO ═══════════════════════
      faturas ── contas_receber ── conciliacoes_bancarias
      contas_pagar ── aprovacoes_despesa, rateios_despesa
      plano_contas (hierárquico) ── contas_pagar

   ═══════════════════════ FISCAL ═══════════════════════════
      ctes ── mdfes (N:N via mdfes_ctes) ── ciots
      configuracoes_fiscais_tenant (numeração exclusiva)

   ═══════════════════════ RASTREAMENTO ══════════════════════
      equipamentos_rastreamento ── posicoes_veiculo, leituras_telemetria (Time Series)
      eventos_rastreamento (derivado) ── cercas_eletronicas

   ═══════════════════════ APP MOTORISTA ═════════════════════
      sessoes_mobile ── filas_sincronizacao ── registros_sincronizacao

   ═══════════════════════ ADMINISTRAÇÃO ═════════════════════
      convites, sessoes_acesso, tokens_api, webhooks, execucoes_job

   ═══════════════════════ BI (só lê, nunca escreve) ═════════
      metricas ── indicadores_consolidados ── snapshots_analiticos
      dashboards_personalizados (config apenas, nunca dado)

   ═══════════════════════ IA (só sugere, nunca decide) ══════
      modelos_ia ── inferencias_ia ── sugestoes_ia/predicoes_ia/
                                        classificacoes_ia/anomalias_detectadas
```

Infraestrutura compartilhada (D186), usada por praticamente todo módulo acima, omitida do diagrama
por clareza: `anexos`, `comentarios` (polimórficas, criadas em `003-operacao.md`).

---

## 2. DER Completo por módulo

### Core (14 tabelas) — [`relational/001-core.md`](./relational/001-core.md)

`tenants` → `usuarios`/`filiais`/`assinaturas`(→`planos`→`itens_plano`)/`configuracoes_regionais_tenant`/
`configuracoes_personalizacao`/`recursos_habilitados_tenant`. `papeis` N:N `permissoes` (via
`papel_permissao`). `usuarios` N:N `papeis` (via `usuarios_papeis`, D222 — gap retroativo, relação
já prevista no Domain Model desde sempre). `assinaturas` 1:N `cobrancas_recorrentes`.

### Cadastros (8 tabelas) — [`relational/002-cadastros.md`](./relational/002-cadastros.md)

`clientes`/`fornecedores`/`filiais` ← `enderecos` (polimórfico, 1:N). `clientes` 1:N
`contatos_cliente`. `motoristas` 1:N `documentos_motorista`. `centros_custo` N:1 `filiais`.
`funcionarios` (D196, gap retroativo) ← `usuarios.funcionario_id` (`001-core.md`), vínculo opcional
1:1 já existente desde o Lote 2 mas sem tabela física até esta correção.

### Operação (19 tabelas + 2 compartilhadas) — [`relational/003-operacao.md`](./relational/003-operacao.md)

`viagens` (aggregate root) ← `entregas` (1:N, cada uma com `canhotos` 1:1 e `janelas_entrega` 1:1) ←
`ocorrencias`, `coletas`, `pontos_parada_viagem`, `alocacoes_recurso_viagem`,
`viagem_status_history`, `romaneios` (→ `itens_carga`). `cotacoes` (→ `itens_cotacao`) e
`contratos_frete` → originam `viagens`. `tabelas_preco` (→ `itens_tabela_preco`) referenciada por
`cotacoes`/`contratos_frete`. `solicitacoes_frete` antecede `cotacoes`. Compartilhadas: `anexos`,
`comentarios`.

### Frota (12 tabelas) — [`relational/004-frota.md`](./relational/004-frota.md)

`veiculos_tracionadores` ← `fichas_tecnicas_veiculo` (1:1), `documentos_veiculo` (1:N),
`apolices_seguro_veicular` (1:N, → `seguradoras`), `licenciamentos_veiculo` (1:N),
`leituras_hodometro` (1:N, Time Series). `composicoes_veiculares` N:N `implementos` (via
`composicoes_veiculares_implementos`). `disponibilidade_veiculo` (read model, 1:1).
`categorias_veiculo` referenciada por `veiculos_tracionadores`/`implementos`.

### Manutenção (9 tabelas) — [`relational/005-manutencao.md`](./relational/005-manutencao.md)

`ordens_servico` (aggregate root) ← `itens_ordem_servico`, `aprovacoes_custo`,
`ordens_servico_status_history`, `solicitacoes_peca`. `planos_manutencao_preventiva` →
`veiculos_tracionadores`/`categorias_veiculo`. `pecas_estoque` ← `movimentacoes_estoque` (histórica).

### Financeiro (14 tabelas) — [`relational/006-financeiro.md`](./relational/006-financeiro.md)

`faturas` (→ `viagens`/`entregas`) ← `contas_receber` (1:N, parcelas) ← `contas_receber_status_history`.
`contas_pagar` ← `aprovacoes_despesa`, `rateios_despesa` (→ `centros_custo`/`viagens`),
`contas_pagar_status_history`. `plano_contas` hierárquico (auto-FK). `contas_bancarias` ←
`lancamentos_extrato_bancario` ← `conciliacoes_bancarias` (→ `contas_pagar`/`contas_receber`).
`estornos_financeiros` (→ um dos três lançamentos). `posicoes_caixa` (read model).

### Fiscal (11 tabelas) — [`relational/007-fiscal.md`](./relational/007-fiscal.md)

`configuracoes_fiscais_tenant` (numeração exclusiva) → `ctes`/`mdfes`. `ctes` ← `cartas_correcao`,
`nfe_referenciadas`, `ctes_status_history`. `mdfes` N:N `ctes` (via `mdfes_ctes`) ←
`mdfes_status_history`. `ciots` ← `ciots_status_history`. `eventos_fiscais` (técnico, polimórfico,
particionado).

### Rastreamento (9 tabelas) — [`relational/008-rastreamento.md`](./relational/008-rastreamento.md)

`provedores_rastreamento` → `equipamentos_rastreamento` (N:1 `veiculos_tracionadores`, múltiplos
papéis, D128) → `posicoes_veiculo`/`leituras_telemetria`/`heartbeats` (Time Series, D191,
particionadas). `eventos_rastreamento` (derivado) → `cercas_eletronicas`/
`configuracoes_limite_velocidade`.

### App Motorista (5 tabelas) — [`relational/009-app_motorista.md`](./relational/009-app_motorista.md)

`sessoes_mobile` (→ `motoristas`, `dispositivos_mobile`) ← `filas_sincronizacao` ←
`registros_sincronizacao` (nível de lote). `assinaturas_digitais` (polimórfico, → `canhotos` hoje).

### Administração (13 tabelas próprias + 8 já em Core/Lote 1) — [`relational/010-administracao.md`](./relational/010-administracao.md)

Novas: `grupos_usuarios` (N:N `usuarios`), `convites`, `fatores_autenticacao`,
`configuracoes_numeracao`, `parametros_tenant`, `sessoes_acesso`, `tokens_api`, `bloqueios_acesso`,
`configuracoes_integracao` → `webhooks`, `execucoes_job` (particionada), `logs_auditoria`
(particionada, D194 — gap retroativo, `CREATE TABLE` nunca existia antes desta correção). Já
existentes (Core/Lote 1): `tenants`, `planos`, `assinaturas`, `configuracoes_regionais_tenant`,
`configuracoes_personalizacao`, `recursos_habilitados_tenant`.

### BI (12 tabelas) — [`relational/011-bi.md`](./relational/011-bi.md)

`metricas` (versionada) → `indicadores_consolidados` → `snapshots_analiticos` (via junção,
imutável). `cubos_analiticos` N:N `metricas`. `dashboards_personalizados`/`filtros_favoritos`/
`relatorios_salvos` (→ `exportacoes_geradas`)/`agendamentos_atualizacao` — todos `reporting`, nunca
escrevem em tabela operacional (D090).

### IA (8 tabelas) — [`relational/012-ia.md`](./relational/012-ia.md)

`modelos_ia` (múltiplos ativos, D169) → `inferencias_ia` (observável) → `sugestoes_ia`/
`predicoes_ia`/`classificacoes_ia`/`anomalias_detectadas`/`leituras_visao_computacional`
(polimórficas quanto à entidade-alvo) ← `feedbacks_ia`.

---

## Convenções deste diagrama

- `→` referência viva (FK comum); `◄──` mesma coisa, direção invertida no desenho.
- `N:N` sempre via tabela de junção nomeada (nunca array/JSONB para relacionamento estruturado).
- Read models (`disponibilidade_veiculo`, `posicoes_caixa`) marcados explicitamente — nunca fonte
  de verdade, apenas consulta rápida.
- Tabelas técnicas/particionadas (Time Series, `*_status_history`, `eventos_*`, `execucoes_job`) não
  recebem símbolo especial no ASCII acima por limitação de formato — identificadas por nome
  (sufixo `_status_history`, prefixo `eventos_`/`posicoes_`/`leituras_`) e detalhadas em
  [`PARTITIONING.md`](./PARTITIONING.md) (próximo documento).

## Dependências entre módulos

Não duplica o DER — deixa explícita a ordem lógica de dependência que já está implícita nos `→` do
diagrama acima. Base direta para [`MIGRATION_ORDER.md`](./MIGRATION_ORDER.md) (mais adiante nesta
sequência).

| Módulo | Depende de |
|---|---|
| Core | — |
| Cadastros | Core |
| Administração | Core |
| Frota | Core, Cadastros |
| Operação | Core, Cadastros, Frota |
| Manutenção | Frota, Operação |
| Financeiro | Operação, Cadastros |
| Fiscal | Operação, Administração |
| Rastreamento | Frota |
| App Motorista | Operação, Administração |
| BI | Todos (somente leitura, D090 — nunca uma dependência de escrita) |
| IA | Operação, Rastreamento, Manutenção, BI |

## Como este documento cresce

Atualizado sempre que um novo lote relacional for aprovado — o Modelo Relacional (Sprint 09) está
completo, então este DER reflete o estado final; mudanças futuras (Sprint 10+, evolução do produto)
atualizam este arquivo junto com `relational/`.
