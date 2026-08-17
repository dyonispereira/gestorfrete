# SEED_DATA.md — Política de Dados Iniciais

Último documento da camada física antes de OpenAPI. Seed não é "`INSERT` de dados iniciais" — é uma
política com quatro categorias distintas, cada uma com dono, ambiente e regra de idempotência
próprios. Primeira coisa que a auditoria D200 encontrou aqui (seção "Achados") foi que uma das
categorias citadas na proposta original — Platform Reference Data geográfica (País/Estado/
Município) — não tem tabela física nenhuma; corrigido na especificação antes de escrever o resto
do documento, não depois.

## 1. Objetivo

Definir o que é populado automaticamente na criação do schema (ou no provisionamento de um novo
tenant), por quem, em que ordem, com que garantia de idempotência, e o que **nunca** deve ser
tratado como seed. Não gera nenhum script de seed real, fixture, ou dado de produção — fecha a
especificação, mesmo escopo de fechamento já aplicado em `MIGRATION_ORDER.md`.

## 2. O que é Seed Data

Dado que precisa existir **antes** da aplicação começar a operar, porque a própria aplicação (ou o
schema) depende dele para funcionar — não é conteúdo gerado pelo uso do sistema. Três testes que uma
tabela/linha precisa passar para ser Seed Data:

1. **Ela existe independente de qualquer tenant ter feito qualquer ação?** (`permissoes`,
   `origens_localizacao`) — ou é criada automaticamente quando um tenant novo é provisionado,
   antes do primeiro uso real (`Tenant Bootstrap`)?
2. **A ausência dela quebra a aplicação, não só deixa uma tela vazia?** (RBAC sem `permissoes`
   simplesmente não funciona; um Cliente vazio só significa que a transportadora ainda não
   cadastrou ninguém — isso não é seed, é operação normal)
3. **O valor é conhecido e estável antes do sistema rodar?** (código de permissão, nome de papel
   padrão) — valores que só existem depois de uma decisão de negócio externa ao código (preço de
   plano) não são Seed Data ainda, mesmo que a estrutura já exista.

## 3. O que NÃO é Seed Data

| Não é Seed Data | É, na verdade | Por quê |
|---|---|---|
| Valor de `ENUM` do PostgreSQL (`ATIVO`/`INATIVO`/`CANCELADO`, etc.) | Parte da definição de tipo (`CREATE TYPE`), migration | Um `ENUM` não tem linha para inserir — o valor já existe assim que o tipo é criado |
| Conteúdo de tabela de configuração **tenant-scoped** (`categorias_veiculo`, `tipos_servico`, `formas_pagamento`, `tabelas_preco`) | Dado operacional do próprio tenant, criado pelo usuário através do produto (ou, no máximo, sugerido como default no onboarding — Tenant Bootstrap, nunca inserido silenciosamente por uma migration global) | Cada transportadora tem sua própria frota/portfólio de serviços — não existe "o" conjunto certo de Categorias de Veículo para todas |
| Preço comercial de Plano | Decisão comercial, gerenciada fora do banco (ou por uma tela administrativa futura), nunca um valor fixo em migration | Ver seção 4.3 — preço não é estrutura |
| Dado de teste/desenvolvimento (transportadora fictícia, motorista fictício) | Fixture de ambiente de desenvolvimento — ver seção 8/9, nunca roda em produção |  |
| Linha criada por uma transação de negócio (uma Viagem, um CT-e) | Dado operacional puro | Seed nunca cria conteúdo transacional |

## Achado ao preparar este documento (D206)

Auditando a categoria "Platform Reference Data" (D046) contra a DDL real: `País`/`Estado`/
`Município` — os exemplos originais de `docs/information-model/004-REFERENCE_DATA.md`, escritos
antes do Modelo de Domínio existir — **nunca ganharam entidade no Domain Model, atributo no Data
Dictionary, nem `CREATE TABLE` físico**. `enderecos.uf`/`.cidade` (D182) são `TEXT` livre, uma
escolha deliberada já revisada em Sprint 09, não um esquecimento. Diferente de D194/D196/D201
(tabela plenamente especificada em outro lugar, só faltando o `CREATE TABLE`), aqui a especificação
em si nunca avançou além do exemplo conceitual inicial — criar as tabelas agora inventaria escopo
novo sem pedido (D076), não corrigiria um gap. Resolvido: este documento usa `origens_localizacao`
(a única tabela de Platform Reference Data física fora de `001-core.md`) como exemplo real da
categoria; País/Estado/Município permanecem citados só como ilustração conceitual do padrão D046,
explicitamente marcados "sem tabela física nesta sprint" — ver seção 11.

## 4. Categorias

### 4.1 Platform Reference Data

Sem `tenant_id`, compartilhado por toda a plataforma, nunca duplicado por tenant (D046).

| Tabela | Conteúdo real hoje |
|---|---|
| `permissoes` | 311 códigos de permissão (ver seção 10) — **categorizada aqui como estrutural, não comercial** |
| `origens_localizacao` | Lista fechada: GPS, GSM, Satélite, Wi-Fi, BLE, Manual, API Externa (`relational/008-rastreamento.md`) |
| `planos`, `itens_plano` (estrutura, não preço) | Ver seção 4.3 |
| *País, Estado, Município* | **Sem tabela física (D206)** — citados aqui só para registrar a decisão de não os inventar agora |

### 4.2 System Reference Data

A proposta original citava "Tipos de Combustível/Veículo/Carroceria/Documento/Sensor/Ocorrência/
Manutenção" como exemplos — auditando cada um contra a DDL real (mesmo cuidado que a revisão pediu
sobre Enums):

| Exemplo citado | O que é de fato no schema | Seed? |
|---|---|---|
| Tipo de Combustível | `fichas_tecnicas_veiculo_combustivel_enum` — `ENUM` | **Não é Seed Data** (seção 3) |
| Tipo de Documento (Motorista/Veículo) | `documentos_motorista_tipo_documento_enum`, equivalente em `documentos_veiculo` — `ENUM` | **Não é Seed Data** |
| Tipo de Sensor | `leituras_telemetria_tipo_sensor_enum` — `ENUM` extensível (D120) | **Não é Seed Data** — cresce por `ALTER TYPE ... ADD VALUE` (migration), nunca por seed |
| Tipo de Ocorrência | `ocorrencias_tipo_enum` — `ENUM` | **Não é Seed Data** |
| Categoria de Veículo, Tipo de Serviço, Forma de Pagamento | Tabelas reais, mas **`tenant_id NOT NULL`** — não são globais | **Não é System Reference Data** — são Tenant Bootstrap (seção 4.4) ou operação normal do tenant |

Conclusão honesta: **este schema não tem, hoje, nenhuma tabela de System Reference Data de fato**
(global, sem tenant, fora de RBAC/rastreamento) — todo candidato citado na proposta original ou é
`ENUM` (migration) ou é tabela tenant-scoped (Tenant Bootstrap). A categoria continua reservada na
estrutura deste documento para quando uma entidade futura genuinamente global (não-RBAC, não-Enum)
justificar uma tabela — não removida, só vazia por enquanto.

### 4.3 SaaS Default Data

| Dado | Estrutural (seed agora) | Comercial (não seed) |
|---|---|---|
| `planos` | Linha existe, `nome`/`id` estáveis | **Preço — a definir comercialmente.** Nenhum valor de `NUMERIC(14,2)` de mensalidade é gravado como seed nesta sprint; nenhum Plano é marcado "pronto para produção" até o preço ser uma decisão comercial formal, registrada em `DECISIONS.md` quando acontecer |
| `itens_plano` | Chaves de feature (`chave_feature`) por Plano — estrutural | Limites numéricos associados (ex.: "quantos veículos"), quando dependerem de precificação, mesma ressalva acima |
| `permissoes` | Todos os 311 códigos (seção 10) | Não aplicável — permissão não tem componente comercial |
| Papéis padrão (sugestão para novo tenant) | Nomes da hierarquia já documentada em `RBAC_MATRIX.md` seção 9 (`Administrador`, `Diretor`, `Gerente`, `Supervisor`, `Analista`, `Operacional`) — **usada como sugestão inicial de conjunto de Permissões ao criar um Papel, nunca herança automática** (a própria `RBAC_MATRIX.md` já registra isso) | — |
| Recursos habilitados por Plano (`recursos_habilitados_tenant`) | Depende de qual feature cada Plano inclui — decisão comercial ainda não formalizada | Mesmo ressalva de preço |

### 4.4 Tenant Bootstrap

Não é Seed Data global — é provisionamento, disparado no evento `TenantProvisionado`
(`flows/001-ONBOARDING.md`), uma vez por tenant novo:

```
Novo Tenant criado (tenants)
        │
        ▼
Configuração Regional do Tenant (default: fuso America/Sao_Paulo, moeda BRL, D075)
        │
        ▼
Configuração de Personalização (default: sem White Label — status INATIVA)
        │
        ▼
Papéis padrão sugeridos (estrutura da hierarquia, RBAC_MATRIX.md seção 9 — o tenant pode
renomear/remover/criar outros livremente, nunca travado)
        │
        ▼
Permissões associadas aos Papéis padrão (papel_permissao) — conjunto inicial sugerido, editável
        │
        ▼
Parâmetros do Tenant (parametros_tenant) com valor_sobrescrito_tenant vazio — usa
valor_padrao_plataforma até o tenant decidir sobrescrever (D145)
        │
        ▼
Recursos habilitados (recursos_habilitados_tenant) conforme o Plano contratado
        │
        ▼
Usuário Master (usuarios) — o responsável do cadastro (flows/001-ONBOARDING.md passo 9), único
usuário com Papel de permissão total no momento da criação
```

**Deliberadamente fora do Tenant Bootstrap** (o tenant começa vazio, nunca com dado de negócio
fictício): `categorias_veiculo`, `tipos_servico`, `formas_pagamento`, `tabelas_preco`, `centros_custo`
— toda tabela "Configuração" tenant-scoped que representa uma escolha de negócio da própria
transportadora, não uma convenção de plataforma.

## 5. Identificadores estáveis

Nenhum seed depende de `UUID` gerado aleatoriamente pela aplicação em tempo de execução — toda
linha de seed usa uma chave natural fixa no próprio script/migration:

| Seed | Chave estável usada | Nunca depende de |
|---|---|---|
| `permissoes` | `codigo` (`bounded_context.entidade.acao`, D058) — já `UNIQUE` (`INDEXES.md`) | Um `id` `UUID` gerado antes de rodar o seed |
| `origens_localizacao` | `nome` (já `UNIQUE`) | — |
| `planos` | `nome` (já `UNIQUE`) — considerar promover a um `codigo` funcional explícito se a comparação por nome se mostrar frágil (não decidido, nota para `SEED_DATA.md` evoluir se necessário) | — |
| Papéis padrão (Tenant Bootstrap) | `(tenant_id, nome)` (já `UNIQUE`) | — |
| Parâmetros do Tenant | `(tenant_id, chave)` (já `UNIQUE`, D145) | — |

Um `id UUID` ainda é gerado (é sempre a PK técnica, D175) — a diferença é que o **seed nunca
precisa saber ou fixar esse valor** para funcionar; ele resolve tudo pela chave natural.

## 6. Idempotência (D204)

**Todo Seed Data deve poder ser executado múltiplas vezes sem duplicar registros ou alterar
silenciosamente registros existentes.** Mecanismo:

```sql
INSERT INTO permissoes (codigo, nome, modulo)
VALUES ('freight.viagem.criar', 'Criar Viagem', 'freight')
ON CONFLICT (codigo) DO NOTHING;
```

`DO NOTHING`, não `DO UPDATE` — rodar o seed de novo nunca deve *sobrescrever* um valor que a
plataforma já ajustou manualmente (ex.: um `nome` de permissão corrigido via migration própria).
Alteração de um valor de seed já existente é sempre uma migration nomeada (D205), nunca um
re-`INSERT` silencioso. Equivalente em Alembic: o próprio corpo de `upgrade()` da revisão de seed
usa `INSERT ... ON CONFLICT`, nunca um script externo não versionado.

## 7. Ordem de Seed

Segue exatamente `MIGRATION_ORDER.md` — nenhum seed roda antes da tabela que ele popula existir, e
nenhum seed de FK roda antes do seed do pai:

```
Onda 01 (Core): planos → itens_plano
                permissoes → (papeis/papel_permissao ficam para o Tenant Bootstrap, Onda por-tenant)
Onda 09 (Rastreamento): origens_localizacao
```

Tenant Bootstrap (seção 4.4) roda **fora** das ondas de `MIGRATION_ORDER.md` — não é parte da
criação do schema, é um fluxo disparado por evento (`TenantProvisionado`) toda vez que um tenant
novo é criado, em produção, muito depois da Onda 12 já ter rodado uma única vez.

## 8. Seed por ambiente

| Ambiente | O que roda |
|---|---|
| **Development** | Platform Reference Data + SaaS Default (estrutural) + Dados sintéticos (seção 9) |
| **Test** | Platform Reference Data + SaaS Default (estrutural) — nunca dados sintéticos fixos (cada suite de teste cria seu próprio fixture isolado, evita teste dependente de estado global) |
| **Staging** | Idêntico a Production + Tenant Bootstrap de 1-2 tenants de homologação, claramente identificados (ex.: razão social prefixada `[HOMOLOGACAO]`) |
| **Production** | Só Platform Reference Data + SaaS Default (estrutural) — **nunca** dados sintéticos |

Nenhum dado de teste entra no seed de produção — a separação é por ambiente de execução (variável
de configuração do processo de seed), não por uma flag dentro do dado em si.

## 9. Dados sintéticos (Development)

Explicitamente marcados como dado de desenvolvimento, nunca confundidos com Tenant Bootstrap real:

- Transportadora fictícia (tenant de desenvolvimento, razão social claramente fictícia, ex.:
  `[DEV] Transportadora Exemplo LTDA`)
- Clientes, motoristas, veículos fictícios associados a esse tenant de desenvolvimento
- Sempre isolados por `tenant_id` — nunca misturados com um tenant real, mesmo em ambiente de
  Development compartilhado entre desenvolvedores

Conteúdo exato (quantos motoristas, quais placas) não é decidido aqui — é fixture de
desenvolvimento, evolui com a necessidade do time, não é parte da especificação do banco.

## 10. Seed de permissões

As 311 permissões de [`RBAC_MATRIX.md`](../product/RBAC_MATRIX.md) (confirmado nesta preparação —
contagem ainda bate) são o seed mais crítico do sistema: sem elas, nenhum RBAC funciona.

- Código estável (`codigo`, `bounded_context.entidade.acao`, D058) é a chave — nunca o `id`.
- **Regra explícita**: uma permissão nunca é removida silenciosamente do banco porque desapareceu
  de um arquivo de seed. Remoção de permissão é sempre uma migration nomeada e deliberada (D205) —
  o seed só adiciona (`ON CONFLICT DO NOTHING`), nunca sincroniza por diff/remoção automática.
- Permissão "aposentada" (código que não deve mais ser usado por um Perfil novo) é marcada por
  convenção de nome/módulo — já decidido em `001-core.md`/`permissoes` (D057) — nunca apagada.
- Seed roda na Onda 01, junto da criação de `permissoes` — antes de qualquer Papel/Tenant Bootstrap
  poder associar uma permissão.

## 11. Seed de Platform Reference Data (estratégia especial)

Reconciliado com D206: **não há hoje uma tabela de geografia normalizada** (País/Estado/Município)
para aplicar uma estratégia de atualização sem quebrar referência histórica — a estratégia abaixo é
registrada como o padrão **a seguir se/quando essa tabela vier a existir** (mesmo raciocínio de
"documentar o padrão futuro" já usado em `INDEXES.md` categoria 9, Full Text):

- Nunca `UPDATE`/`DELETE` num código já referenciado por outra linha (ex.: um código de município
  usado num Endereço) — mudança de nome (ex.: um município renomeado por lei) vira uma nova versão
  lógica, nunca sobrescreve a antiga silenciosamente (mesmo princípio de D073, snapshot/versão).
  `origens_localizacao` já segue esse espírito hoje (nenhuma linha é removida, só marcada obsoleta
  se necessário) mesmo sendo uma lista fixa de 7 valores.
- Código IBGE (quando existir) é a chave estável, nunca o nome (nomes têm acentuação/grafia
  inconsistente entre fontes, código não).

## 12. Reexecução

| Tipo | O que é | Idempotente via |
|---|---|---|
| Seed inicial | Primeira execução, schema recém-criado | `INSERT ... ON CONFLICT DO NOTHING` |
| Seed incremental | Nova permissão/plano adicionado depois, sistema já em produção | Mesma revisão Alembic de sempre — nova migration, `INSERT ... ON CONFLICT DO NOTHING`, nunca um script ad-hoc fora do versionamento |
| Seed de correção | Um valor de seed foi gravado errado (ex.: nome de permissão com typo) | Migration nomeada com `UPDATE` explícito, direcionada, nunca um re-seed geral (D205 — isso é alteração de dado existente, responsabilidade de Migration) |
| Seed de atualização | Mudança legítima de um valor estrutural (ex.: renomear um Papel padrão sugerido) | Mesma via de correção — migration nomeada |

**Nunca `TRUNCATE`** em nenhum cenário — nem para "recomeçar limpo": `TRUNCATE` apaga histórico
(violaria D001/D109 se qualquer linha real já tiver referência) e não é idempotente no sentido que
este documento define (idempotente é "rodar de novo não muda o resultado final", não "resetar e
começar de novo").

## 13. Auditoria

**Padrão adotado**: seed estrutural inicial (Onda de migration, schema recém-criado) **não gera**
`logs_auditoria` — é operação de infraestrutura, sem um `ator_id` humano real por trás (a coluna
`ator_id` de `logs_auditoria` é nullable exatamente para "ações automáticas", `AUDIT_MODEL.md`).
Alterações posteriores feitas por um Usuário/Administrador (ex.: editar uma permissão via tela
administrativa futura, ajustar um Papel padrão depois que o tenant já existe) **geram** log de
auditoria normalmente — são ações de negócio, não infraestrutura. Tenant Bootstrap fica no meio:
tecnicamente disparado por evento (`TenantProvisionado`), mas seu resultado (Papéis/Parâmetros/
Usuário Master do tenant) é dado de negócio do tenant desde o primeiro instante — **gera auditoria**,
com `origem = 'SISTEMA'` (`logs_auditoria_origem_enum`, já existente) e `ator_id` nulo.

## 14. Validação

Ao final de qualquer execução de seed (inicial ou incremental):

- [ ] Contagem esperada: `permissoes` = 311 (ou o número vigente, se `RBAC_MATRIX.md` tiver
      crescido — sempre comparado contra a fonte, nunca um número fixo assumido de memória, mesmo
      espírito de D200)
- [ ] Toda FK de seed resolvida (`itens_plano.plano_id`, `papel_permissao.papel_id`/`permissao_id`)
- [ ] Nenhuma duplicata por chave estável (`UNIQUE` já garante fisicamente, seed só confirma)
- [ ] Tenants isolados — nenhuma linha de Tenant Bootstrap vazou `tenant_id` para outro tenant
- [ ] Todas as 311 permissões existem e resolvem para pelo menos um Papel padrão sugerido
- [ ] Dados globais (`permissoes`, `origens_localizacao`, `planos`) presentes e sem `tenant_id`

## 15. Catálogo final

| Seed | Tabela | Categoria | Chave Estável | Tenant | Ambiente | Idempotente | Obrigatório |
|---|---|---|---|---|---|---|---|
| Permissões RBAC | `permissoes` | Platform Reference / SaaS Default (estrutural) | `codigo` | Não | Todos | Sim | Sim |
| Origens de Localização | `origens_localizacao` | Platform Reference | `nome` | Não | Todos | Sim | Sim |
| Planos (estrutura) | `planos` | SaaS Default (estrutural) | `nome` | Não | Todos | Sim | Sim |
| Itens de Plano (features) | `itens_plano` | SaaS Default (estrutural) | `(plano_id, chave_feature)` | Não | Todos | Sim | Sim |
| Preço de Plano | `planos`/`itens_plano` (colunas comerciais) | SaaS Default (comercial) | — | Não | — | — | **Não — a definir comercialmente** |
| Papéis padrão sugeridos | `papeis` | Tenant Bootstrap | `(tenant_id, nome)` | Sim | Production/Staging (por tenant real) | Sim | Sim, por tenant |
| Permissões dos Papéis padrão | `papel_permissao` | Tenant Bootstrap | `(papel_id, permissao_id)` | Sim (via papel) | Production/Staging | Sim | Sim, por tenant |
| Configuração Regional default | `configuracoes_regionais_tenant` | Tenant Bootstrap | `tenant_id` (1:1) | Sim | Production/Staging | Sim | Sim, por tenant |
| Configuração de Personalização default | `configuracoes_personalizacao` | Tenant Bootstrap | `tenant_id` (1:1) | Sim | Production/Staging | Sim | Sim, por tenant |
| Parâmetros do Tenant (default = plataforma) | `parametros_tenant` | Tenant Bootstrap | `(tenant_id, chave)` | Sim | Production/Staging | Sim | Sim, por tenant |
| Recursos Habilitados (por Plano) | `recursos_habilitados_tenant` | Tenant Bootstrap | `(tenant_id, chave_feature)` | Sim | Production/Staging | Sim | Sim, por tenant |
| Usuário Master | `usuarios` | Tenant Bootstrap | `(tenant_id, email)` | Sim | Production/Staging | Sim (não recria se já existe) | Sim, por tenant |
| Categorias de Veículo/Tipo de Serviço/Forma de Pagamento/Tabela de Preço | — | **Não é seed** — operação normal do tenant | — | Sim | — | — | Não |
| Tenant + dados fictícios de desenvolvimento | `tenants` + Cadastros/Frota/Operação fictícios | Dados sintéticos | Prefixo `[DEV]` no nome | Sim (isolado) | **Development apenas** | Sim (recriável) | Não (só Development) |
| País/Estado/Município | — | **Sem tabela física (D206)** | — | — | — | — | Não |

## Como este documento cresce

Estável enquanto o Modelo Relacional e o Tenant Bootstrap não mudam. Nova permissão/plano/parâmetro
padrão ganha uma linha no catálogo da seção 15 na mesma revisão que o cria — mesma disciplina de
índice sempre atualizado já aplicada a `TABLES.md`/`ENTITY_CATALOG.md`. Com este documento,
encerra-se a especificação física do banco (Domain → Dictionary → Modelo Relacional → DER → Tables
→ Foreign Keys → Indexes → Constraints → Partitioning → Migration Order → Seed Data). Próxima
etapa: Sprint 10 — OpenAPI 3.1, primeira vez que esta documentação vira contrato de API antes do
Backend.
