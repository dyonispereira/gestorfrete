# NAMING_CONVENTION.md — Convenção de Nomenclatura Física

Cumpre a promessa feita em D068 desde o Sprint 08: "nomenclatura técnica fica para a modelagem
física". Este é o documento que define, pela primeira vez, como um atributo funcional do dicionário
(ex: `VIAGEM.STATUS_OPERACIONAL`) vira um identificador físico real (`viagens.status_operacional`).

> Este arquivo substitui o antigo `NAMING.md` (placeholder vazio da fundação inicial do projeto,
> antes da metodologia sprint-a-sprint existir) — mesmo conteúdo pretendido, nome mais específico,
> consistente com os demais arquivos deste lote (`TENANCY_MODEL.md`, `AUDIT_MODEL.md`, etc.).

## Regra geral (D180)

Tudo em `snake_case`. Nunca `PascalCase`, `camelCase` ou `kebab-case` em identificador físico algum
— tabela, coluna, índice, constraint, enum, função.

## Tabelas

- **Plural**, no nome de negócio traduzido para `snake_case` — nunca o nome técnico/inglês do
  bounded context.
- Exemplo de tradução Dicionário Funcional → Tabela física:

| Entidade (Dicionário Funcional) | Tabela física |
|---|---|
| `Motorista` | `motoristas` |
| `Veículo Tracionador` | `veiculos_tracionadores` |
| `Ordem de Serviço` | `ordens_servico` |
| `Item de Ordem de Serviço` | `itens_ordem_servico` |
| `Posição de Veículo` | `posicoes_veiculo` |
| `Configuração Fiscal do Tenant` | `configuracoes_fiscais_tenant` |

- Entidades **Históricas** (D037) que representam o log append-only de outra (`ViagemStatusHistory`,
  D017/D018) viram tabela própria com sufixo `_status_history` ou nome de negócio direto quando já
  documentado como entidade própria (ex: `Registro de Recapagem` → `registros_recapagem`, não
  `pneu_status_history`) — segue o nome já estabelecido no Data Dictionary, nunca inventa um novo.
- Tabelas de associação N:N sem entidade de domínio própria (raras — a maioria dos relacionamentos
  N:N do GestorFrete já é uma entidade documentada, D085) seguem `<tabela_a>_<tabela_b>` no singular
  de cada lado, ex: `usuario_grupo`.

## Colunas

- **Singular**, `snake_case`, tradução direta do atributo funcional em maiúsculas com underscore
  (o Data Dictionary já usa esse formato, ex: `DATA_VENCIMENTO`) para minúsculas:

| Atributo (Dicionário Funcional) | Coluna física |
|---|---|
| `MOTORISTA.CNH_VALIDADE` | `cnh_validade` |
| `VIAGEM.STATUS_OPERACIONAL` | `status_operacional` |
| `FATURA.VALOR_TOTAL` | `valor_total` |

- Chaves estrangeiras: sempre `<entidade_singular>_id` — nunca só `id_motorista` ou `motorista`.
  Ex: `motorista_id`, `viagem_id`, `centro_custo_id`.
- Booleanos: prefixo `is_`/`possui_`/sufixo `_habilitado` conforme a semântica ficar mais legível —
  ex: `esta_matriz` (Filial, de `EH_MATRIZ`), `revisao_humana_necessaria` (Leitura por Visão
  Computacional). Decisão de legibilidade caso a caso, nunca uma regra rígida de prefixo único.
- Enums: coluna nomeada como o atributo (`status`, `tipo`, `categoria`), tipada como um `ENUM`
  físico do PostgreSQL nomeado `<tabela_singular>_<coluna>_enum` (ex: `viagem_status_operacional_
  enum`) — ver [`ENUMS.md`](./ENUMS.md) (a ser populado por categoria).
- Colunas universais (D069) têm nome físico fixo em toda tabela, sem exceção: `id`, `tenant_id`,
  `codigo`, `versao`, `criado_em`, `criado_por`, `atualizado_em`, `atualizado_por`, `status`,
  `excluido_em`, `excluido_por` (as três últimas detalhadas em `SOFT_DELETE_MODEL.md`/`AUDIT_MODEL.md`).

## Índices e constraints

- Índice: `idx_<tabela>_<colunas>` (ex: `idx_viagens_tenant_id_status_operacional`).
- Chave estrangeira (constraint): `fk_<tabela>_<coluna_fk>` (ex: `fk_viagens_motorista_id`).
- Unique constraint: `uq_<tabela>_<colunas>` (ex: `uq_veiculos_tracionadores_tenant_id_placa` — D076
  já estabelece que Placa é única por tenant, esta é a tradução física dessa regra).
- Check constraint: `ck_<tabela>_<regra>` (ex: `ck_item_ordem_servico_quantidade_positiva`).

## O que este documento não decide

- Tipos SQL concretos de cada coluna (`VARCHAR(n)` vs `TEXT`, `NUMERIC(p,s)` para Monetário, etc.) —
  isso é detalhado tabela a tabela no Modelo Relacional (`relational/NNN-categoria.md`), a partir dos
  Tipos Conceituais Padronizados já definidos em
  [`../database/dictionary/README.md`](./dictionary/README.md).
- Estratégia de particionamento — ver [`DATABASE_ARCHITECTURE.md`](./DATABASE_ARCHITECTURE.md).

## Como este documento cresce

Regras gerais estáveis, definidas de uma vez neste lote. Exceções específicas de uma tabela (se
surgirem) são registradas no arquivo `relational/NNN-categoria.md` correspondente, com justificativa,
nunca alterando a regra geral aqui sem uma decisão registrada em `DECISIONS.md`.
