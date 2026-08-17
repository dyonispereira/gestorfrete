# TENANCY_MODEL.md — Modelo Multi-Tenant Físico

Implementação física de D005/D006 (isolamento lógico por `tenant_id`, não schema/database por
tenant — decisão tomada na fundação do projeto, antes mesmo do Modelo de Domínio existir) e D174.

## Regra (D174)

Toda tabela de negócio tem:

```sql
tenant_id UUID NOT NULL REFERENCES tenants(id)
```

Nunca opcional, nunca um valor sentinela para "sem tenant". Exemplo — tabela `motoristas`:

```sql
CREATE TABLE motoristas (
    id            UUID PRIMARY KEY,
    tenant_id     UUID NOT NULL REFERENCES tenants(id),
    codigo        TEXT NOT NULL,
    nome          TEXT NOT NULL,
    cpf           TEXT NOT NULL,
    status        motorista_status_enum NOT NULL,
    criado_em    TIMESTAMPTZ NOT NULL DEFAULT now(),
    criado_por    UUID NOT NULL,
    atualizado_em    TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_por    UUID NOT NULL,
    excluido_em    TIMESTAMPTZ,
    excluido_por    UUID
);
```

Nunca:

```sql
CREATE TABLE motoristas (
    id     UUID PRIMARY KEY,
    -- sem tenant_id — nunca aceito, mesmo "temporariamente"
    nome   TEXT NOT NULL
);
```

## Exceção única: Platform Reference Data (D046)

Tabelas que representam catálogos compartilhados por toda a plataforma — não pertencem a nenhum
tenant específico — **não têm** `tenant_id`. Já identificadas no Data Dictionary Funcional:

| Tabela física | Entidade | Fonte |
|---|---|---|
| `paises`, `estados`, `municipios` | Platform Reference Data original (D046) | [`../information-model/004-REFERENCE_DATA.md`](../information-model/004-REFERENCE_DATA.md) |
| `origens_localizacao` | `Origem de Localização` | [`../database/dictionary/008-rastreamento.md`](./dictionary/008-rastreamento.md) |
| `planos`, `itens_plano` | `Plano`, `Item de Plano` | [`../database/dictionary/010-administracao.md`](./dictionary/010-administracao.md) |
| `permissoes` | `Permissão` — catálogo fixo de RBAC, não pertence a um tenant | [`../database/dictionary/010-administracao.md`](./dictionary/010-administracao.md) |

`tenants` em si também não tem `tenant_id` — é a própria raiz da hierarquia, não um caso de
Platform Reference Data.

Toda nova tabela sem `tenant_id` **precisa** justificar explicitamente por que é Platform Reference
Data (D046) no arquivo `relational/NNN-categoria.md` correspondente — a ausência de `tenant_id`
nunca é um esquecimento, é sempre uma decisão documentada.

## Segunda exceção: tabelas de junção pura (D193)

Uma tabela de junção N:N cuja chave primária é **composta exclusivamente pelas duas FKs**
envolvidas (sem `id` próprio, sem nenhuma outra coluna de negócio além de metadados triviais como
`ordem`) não precisa de `tenant_id` próprio — o isolamento já é garantido pelos dois lados da
junção, ambos tabelas de negócio com `tenant_id` (e, na prática, ambos precisam pertencer ao mesmo
tenant para a FK fazer sentido). Exemplos: `papel_permissao`, `mdfes_ctes`,
`composicoes_veiculares_implementos`, `grupos_usuarios_usuarios`,
`snapshots_analiticos_indicadores`, `cubos_analiticos_metricas`, `relatorios_salvos_metricas`.

Esta exceção **não** se aplica a tabelas "filhas" que têm `id` próprio e são consultadas
diretamente (ex: itens de uma lista, histórico de status, aprovações) — essas sempre têm
`tenant_id` próprio, mesmo quando teoricamente derivável via join com o pai. Motivo: evita depender
de join para filtrar por tenant (toda tabela de negócio é indexável por tenant desde o primeiro
dia) e funciona como segunda camada de defesa caso a query erre o join. Esta distinção foi corrigida
retroativamente em 15 tabelas (D193) que haviam sido escritas sem `tenant_id` por engano durante o
Modelo Relacional (Sprint 09) — encontradas na auditoria feita ao preparar `TABLES.md`.

**`tenant_id` da tabela filha nunca é uma segunda origem da verdade.** Ele precisa permanecer
consistente com o `tenant_id` da entidade pai — na prática, garantido pela aplicação no momento da
escrita (o `tenant_id` da filha é sempre copiado do mesmo contexto de tenant que resolve o FK do
pai, nunca informado independentemente) e, opcionalmente, reforçável por trigger caso um `RLS` mais
rígido seja adotado no futuro. O pai continua sendo a única fonte de verdade sobre "de quem é este
registro" — o `tenant_id` da filha é uma cópia redundante por design (para performance de índice e
defesa em profundidade), não uma segunda decisão.

## Como o isolamento é garantido

Duas camadas, não uma só:

1. **Aplicação** (camada principal, D005/D006): toda query passa pelo `tenant_id` do contexto
   autenticado — nenhum repositório do backend lê/escreve sem esse filtro, reforçado por testes.
2. **PostgreSQL Row-Level Security** (camada de defesa adicional, avaliação por tabela): possível
   ativar `RLS` nas tabelas de maior sensibilidade (ex: `contas_pagar`, `contas_receber`, `usuarios`)
   como segunda barreira contra erro de aplicação — **não decidido globalmente ainda**; será avaliado
   tabela a tabela no Modelo Relacional, não é uma obrigação universal como o `tenant_id` em si.

## Índice obrigatório

Toda tabela de negócio tem `tenant_id` como primeiro componente de ao menos um índice composto (ex:
`idx_viagens_tenant_id_status_operacional`) — praticamente toda query do sistema filtra por tenant
primeiro, então o índice precisa refletir esse padrão de acesso desde a criação da tabela.

## Como este documento cresce

Regra geral estável. Exceções (Platform Reference Data) são listadas aqui conforme identificadas em
cada `relational/NNN-categoria.md` — nunca descobertas em produção.
