# 001 — Core (SaaS, Identidade, Configuração)

Primeiro arquivo do Modelo Relacional. Traduz para SQL as entidades de
[`../dictionary/001-cadastros.md`](../dictionary/001-cadastros.md) (Usuário, Papel, Permissão,
Filial) e uma parte de [`../dictionary/010-administracao.md`](../dictionary/010-administracao.md)
(Tenant, Plano, Item de Plano, Assinatura, Cobrança Recorrente, Recurso Habilitado do Tenant,
Configuração Regional do Tenant, Configuração de Personalização) — a base que todo o restante do
banco referencia. As 8 regras de [`../README.md`](../README.md) (Lote 1) já se aplicam a toda tabela
abaixo e não são repetidas coluna a coluna.

## Reconciliação antes de desenhar (D076 aplicado à camada física)

Três correções ao esboço original desta rodada, cada uma porque o Data Dictionary Funcional já
havia decidido diferente, por um motivo já registrado:

| Proposto nesta rodada | Decisão mantida | Por quê |
|---|---|---|
| `timezone` como coluna de `tenants` | `timezone` fica em `configuracoes_regionais_tenant`, tabela própria, 1:1 | `Configuração Regional do Tenant` foi deliberadamente separada de `Tenant` em `010-administracao.md` (D033/D034 — Tenant é identidade/status do cliente SaaS; regionalização é configuração, outro ciclo de vida) |
| `logo_storage_id` como coluna de `tenants` | Logo fica em `configuracoes_personalizacao`, tabela própria, 1:1 | Mesma razão — `Configuração de Personalização` (White Label) já existe como entidade própria, e D148 exige que personalização nunca se misture com dado operacional/identidade |
| `permissao.codigo` implicitamente por tenant | `permissoes` é Platform Reference Data (D046) — **sem** `tenant_id`, catálogo único da plataforma inteira | D057/D058 já estabeleciam código de permissão como imutável e versionado globalmente, não por tenant; `papeis` (antigo "papel_permissao" por tenant) é quem varia por tenant, não o catálogo de permissões em si |

Duas exceções à regra "toda tabela tem `tenant_id`" já eram esperadas
([`../TENANCY_MODEL.md`](../TENANCY_MODEL.md)): `permissoes` e `planos`/`itens_plano` são Platform
Reference Data.

## Escopo deste lote — o que fica para depois

Por pedido explícito, este arquivo cobre só o essencial do Bloco 1 (Plataforma SaaS) da fundação de
`010-administracao.md` + Usuário/Papel/Permissão/Filial de `001-cadastros.md`. **Adiado
explicitamente** (não esquecido — volta em `011-administracao.md`, Lote 11): Grupo de Usuários,
Convite, Fator de Autenticação, Sessão de Acesso, Token de API, Bloqueio de Acesso, Configuração de
Numeração, Parâmetro do Tenant, Configuração de Integração, Webhook, Execução de Job. `logs_auditoria`
já tem sua estrutura definida em [`../AUDIT_MODEL.md`](../AUDIT_MODEL.md) (Lote 1) — não repetida
aqui, mas toda tabela deste arquivo a alimenta normalmente.

---

## Diagrama de relacionamento

```
                    planos
                      │
                      │ 1:N
                      ▼
                 assinaturas ──── 1:N ──── cobrancas_recorrentes
                      │
                      │ 1:1 vigente
                      ▼
                   tenants
                      │
        ┌─────────────┼─────────────────┬──────────────────────┬───────────────────────┐
        │             │                 │                      │                        │
        │ 1:N         │ 1:N             │ 1:1                  │ 1:1                    │ 1:N
        ▼             ▼                 ▼                      ▼                        ▼
    usuarios       filiais    configuracoes_regionais  configuracoes_personalizacao  recursos_habilitados_tenant
        │
        │ N:N (via papel_permissao)
        ▼
      papeis ──── N:N ──── permissoes (Platform Reference Data, sem tenant_id)
```

## `tenants`

Implementação física de `Tenant` ([`../dictionary/010-administracao.md`](../dictionary/010-administracao.md)).

```sql
CREATE TYPE tenants_status_enum AS ENUM ('TRIAL', 'ATIVO', 'SUSPENSO', 'CANCELADO');

CREATE TABLE tenants (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo          TEXT NOT NULL,
    versao          INTEGER NOT NULL DEFAULT 1,
    razao_social    TEXT NOT NULL,
    cnpj            TEXT NOT NULL,
    status          tenants_status_enum NOT NULL DEFAULT 'TRIAL',
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    criado_por      UUID,
    atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_por  UUID,
    excluido_em     TIMESTAMPTZ,
    excluido_por    UUID,

    CONSTRAINT uq_tenants_codigo UNIQUE (codigo),
    CONSTRAINT uq_tenants_cnpj UNIQUE (cnpj)
);

CREATE INDEX idx_tenants_status ON tenants (status) WHERE excluido_em IS NULL;
```

`tenants` é a única tabela de negócio sem `tenant_id` que **não** é Platform Reference Data — ela é
a própria raiz do tenant (D174, exceção óbvia: um tenant não referencia a si mesmo).

## `usuarios`

Implementação física de `Usuário` ([`../dictionary/001-cadastros.md`](../dictionary/001-cadastros.md)).

```sql
CREATE TYPE usuarios_status_enum AS ENUM ('ATIVO', 'INATIVO', 'BLOQUEADO');

CREATE TABLE usuarios (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    codigo          TEXT NOT NULL,
    versao          INTEGER NOT NULL DEFAULT 1,
    nome            TEXT NOT NULL,
    email           TEXT NOT NULL,
    senha_hash      TEXT NOT NULL,
    status          usuarios_status_enum NOT NULL DEFAULT 'ATIVO',
    motorista_id    UUID REFERENCES motoristas(id),   -- opcional, D029-style, tabela em 002-cadastros.md
    funcionario_id  UUID REFERENCES funcionarios(id), -- opcional, tabela em 002-cadastros.md
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    criado_por      UUID,
    atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_por  UUID,
    excluido_em     TIMESTAMPTZ,
    excluido_por    UUID,

    CONSTRAINT uq_usuarios_tenant_id_codigo UNIQUE (tenant_id, codigo),
    CONSTRAINT uq_usuarios_tenant_id_email UNIQUE (tenant_id, email),
    CONSTRAINT ck_usuarios_motorista_xor_funcionario
        CHECK (NOT (motorista_id IS NOT NULL AND funcionario_id IS NOT NULL))
);

CREATE INDEX idx_usuarios_tenant_id_email ON usuarios (tenant_id, email) WHERE excluido_em IS NULL;
```

`motoristas`/`funcionarios` são tabelas de `002-cadastros.md` (próximo lote) — referenciadas aqui
por FK antecipada; a criação física respeita a ordem de dependência no momento das migrations
(`usuarios` só é criada depois de `motoristas`/`funcionarios` existirem, ou a FK é adicionada em
migration separada — decisão de ordem de migration, não de modelo).

## `papeis`

Implementação física de `Papel` — "Perfil" no vocabulário de negócio, mesmo conceito (D028).

```sql
CREATE TABLE papeis (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    codigo          TEXT NOT NULL,
    versao          INTEGER NOT NULL DEFAULT 1,
    nome            TEXT NOT NULL,
    descricao       TEXT,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    criado_por      UUID,
    atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_por  UUID,
    excluido_em     TIMESTAMPTZ,
    excluido_por    UUID,

    CONSTRAINT uq_papeis_tenant_id_nome UNIQUE (tenant_id, nome)
);
```

## `permissoes` (Platform Reference Data — sem `tenant_id`)

Implementação física de `Permissão`. Catálogo único da plataforma, imutável por versão (D057).

```sql
CREATE TABLE permissoes (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo      TEXT NOT NULL,           -- formato bounded_context.entidade.acao (D058)
    nome        TEXT NOT NULL,
    modulo      TEXT NOT NULL,
    criado_em   TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_permissoes_codigo UNIQUE (codigo)
    -- sem atualizado_em/atualizado_por/excluido_em/excluido_por: um código de permissão nunca é
    -- editado nem removido (D057) — uma permissão obsoleta é aposentada (marcada via nome/módulo,
    -- detalhe de aposentadoria a confirmar em 011-administracao.md), nunca apagada
);

CREATE INDEX idx_permissoes_modulo ON permissoes (modulo);
```

## `papel_permissao` (junção N:N)

```sql
CREATE TABLE papel_permissao (
    papel_id       UUID NOT NULL REFERENCES papeis(id),
    permissao_id   UUID NOT NULL REFERENCES permissoes(id),
    criado_em      TIMESTAMPTZ NOT NULL DEFAULT now(),
    criado_por     UUID,

    PRIMARY KEY (papel_id, permissao_id)
    -- sem tenant_id próprio: herdado de papel_id (papeis já tem tenant_id) — evita redundância
    -- sem soft delete: a revogação de uma permissão de um papel é um DELETE real nesta tabela de
    -- junção (o histórico de "quem teve o quê quando" vive em logs_auditoria, não aqui)
);
```

## `usuarios_papeis` (junção N:N — D222, gap retroativo)

Implementação física de `Usuário` ↔ `Papel` (N:N) — o Domain Model
([`../../domain/001-cadastros.md`](../../domain/001-cadastros.md), "Principais relacionamentos:
Papel (N:N)") sempre descreveu essa relação como N:N, mas nenhuma tabela de junção foi criada
durante o Lote 2 original — sem ela, não existe forma física de saber quais Papéis um Usuário tem.
Encontrado ao preparar o contrato de `GET/PATCH /users` (Sprint 10, API Lote 2), mesma natureza de
D194/D196/D201 (relação plenamente especificada no Domain, nunca materializada em DDL).

```sql
CREATE TABLE usuarios_papeis (
    usuario_id     UUID NOT NULL REFERENCES usuarios(id),
    papel_id       UUID NOT NULL REFERENCES papeis(id),
    criado_em      TIMESTAMPTZ NOT NULL DEFAULT now(),
    criado_por     UUID,

    PRIMARY KEY (usuario_id, papel_id)
    -- sem tenant_id próprio: herdado de usuario_id/papel_id, ambos já do mesmo tenant (D193 —
    -- junção pura)
    -- sem soft delete: remover um Papel de um Usuário é um DELETE real nesta tabela de junção,
    -- mesmo padrão de papel_permissao — histórico vive em logs_auditoria, não aqui
);
```

`(usuario_id, papel_id)`, não `(papel_id, usuario_id)` como em `papel_permissao` — ordem invertida
deliberada: a consulta mais frequente do sistema é "quais Papéis este Usuário tem" (resolvida em
toda requisição autenticada, para montar o contexto de RBAC), nunca o contrário ("quais Usuários
têm este Papel", só em telas administrativas ocasionais) — `usuario_id` como coluna líder da PK
serve a consulta quente sem precisar de índice adicional.

## `planos` (Platform Reference Data — sem `tenant_id`)

```sql
CREATE TYPE planos_status_enum AS ENUM ('ATIVO', 'DESCONTINUADO');

CREATE TABLE planos (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo          TEXT NOT NULL,
    versao          INTEGER NOT NULL DEFAULT 1,
    nome            TEXT NOT NULL,
    preco_base      NUMERIC(14,2) NOT NULL,
    status          planos_status_enum NOT NULL DEFAULT 'ATIVO',
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_planos_nome UNIQUE (nome)
);
```

## `itens_plano` (Platform Reference Data — sem `tenant_id`)

```sql
CREATE TABLE itens_plano (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plano_id        UUID NOT NULL REFERENCES planos(id),
    chave_feature   TEXT NOT NULL,   -- vocabulário extensível, ex: MAX_VEICULOS, WHITE_LABEL
    valor           TEXT NOT NULL,

    CONSTRAINT uq_itens_plano_plano_id_chave UNIQUE (plano_id, chave_feature)
);
```

## `assinaturas`

```sql
CREATE TYPE assinaturas_status_enum AS ENUM ('TRIAL', 'ATIVA', 'CANCELADA', 'SUSPENSA');

CREATE TABLE assinaturas (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),
    plano_id            UUID NOT NULL REFERENCES planos(id),
    status              assinaturas_status_enum NOT NULL DEFAULT 'TRIAL',
    data_inicio_trial   DATE,
    data_fim_trial      DATE,
    criado_em           TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_assinaturas_tenant_id_ativa
        UNIQUE (tenant_id, status) DEFERRABLE INITIALLY DEFERRED
        -- garante no máximo uma assinatura 'ATIVA' por tenant; a unicidade real (só quando
        -- status = 'ATIVA') é reforçada por índice parcial abaixo, não pela constraint composta
);

CREATE UNIQUE INDEX uq_assinaturas_tenant_id_status_ativa
    ON assinaturas (tenant_id) WHERE status = 'ATIVA';
```

## `assinaturas_status_history` (D260-audit, Sprint 10 Lote 7)

Por D017/D018, `assinaturas.status` nunca é sobrescrito sem deixar histórico — mesmo padrão físico
de `contas_pagar_status_history`/`ordens_servico_status_history`, ausente aqui até esta auditoria
(a tabela tinha `status` desde sempre, mas nenhuma tabela de histórico dedicada — gap da mesma
família de D194/D196/D201/D222/D239/D259). `TenantStatusHistory` (`tenants.status`, citada em
`flows/001-ONBOARDING.md`) é uma tabela **diferente**, ainda sem `CREATE TABLE` — gap relacionado
mas não corrigido aqui (fora do escopo do Lote 7 de API; fica registrado para quando `tenancy`/
`core` for revisitado).

```sql
CREATE TABLE assinaturas_status_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    assinatura_id   UUID NOT NULL REFERENCES assinaturas(id),
    status          TEXT NOT NULL,
    usuario_id      UUID,   -- nulo quando a transição é automática (ex: cobrança falhou)
    origem          TEXT NOT NULL,
    data_hora       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_assinaturas_status_history_assinatura_id ON assinaturas_status_history (assinatura_id, data_hora);
```

## `cobrancas_recorrentes`

```sql
CREATE TYPE cobrancas_recorrentes_status_enum AS ENUM ('PENDENTE', 'PAGA', 'FALHOU', 'CANCELADA');

CREATE TABLE cobrancas_recorrentes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),   -- D174/D193 — mesmo padrão de assinaturas, não apenas via FK
    assinatura_id   UUID NOT NULL REFERENCES assinaturas(id),
    valor           NUMERIC(14,2) NOT NULL,
    moeda           TEXT NOT NULL DEFAULT 'BRL',   -- D075 — campo existe desde já para multi-moeda futura
    data_vencimento DATE NOT NULL,
    status          cobrancas_recorrentes_status_enum NOT NULL DEFAULT 'PENDENTE',
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT now()

    -- integração futura com gateway (ex: ASAAS, citado nesta rodada) é campo de infraestrutura
    -- (referência de transação externa) — a confirmar em 011-administracao.md, não decidido aqui
);

CREATE INDEX idx_cobrancas_recorrentes_tenant_id_status
    ON cobrancas_recorrentes (tenant_id, status);
CREATE INDEX idx_cobrancas_recorrentes_assinatura_id_status
    ON cobrancas_recorrentes (assinatura_id, status);
```

## `recursos_habilitados_tenant`

Camada de **exceção** (D146) — nunca a consolidação final do que um tenant pode usar.

```sql
CREATE TYPE recursos_habilitados_tenant_tipo_excecao_enum AS ENUM
    ('HABILITA_ALEM_DO_PLANO', 'DESABILITA_APESAR_DO_PLANO');

CREATE TABLE recursos_habilitados_tenant (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),
    chave_feature       TEXT NOT NULL,
    tipo_excecao        recursos_habilitados_tenant_tipo_excecao_enum NOT NULL,
    data_fim_validade   DATE,
    criado_em           TIMESTAMPTZ NOT NULL DEFAULT now(),
    criado_por          UUID,

    CONSTRAINT uq_recursos_habilitados_tenant_id_chave UNIQUE (tenant_id, chave_feature)
);
```

## `filiais`

Implementação física de `Filial` ([`../dictionary/001-cadastros.md`](../dictionary/001-cadastros.md)).
**Sem coluna `endereco` própria (D231)** — endereço de Filial vive em `enderecos`
(`002-cadastros.md`, `entidade_tipo = 'FILIAL'`), mesmo padrão polimórfico de Cliente/Fornecedor
(D182). Esta tabela tinha uma coluna `endereco JSONB` embutida desde a criação original (antes de
`Endereço` existir como entidade própria) — nunca removida quando D182 estendeu o padrão
polimórfico para Filial; corrigido ao preparar a API de Endereços (Sprint 10, Lote 3).

```sql
CREATE TABLE filiais (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    codigo          TEXT NOT NULL,
    versao          INTEGER NOT NULL DEFAULT 1,
    nome            TEXT NOT NULL,
    esta_matriz     BOOLEAN NOT NULL DEFAULT FALSE,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    criado_por      UUID,
    atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_por  UUID,
    excluido_em     TIMESTAMPTZ,
    excluido_por    UUID,

    CONSTRAINT uq_filiais_tenant_id_codigo UNIQUE (tenant_id, codigo)
);

CREATE UNIQUE INDEX uq_filiais_tenant_id_matriz
    ON filiais (tenant_id) WHERE esta_matriz AND excluido_em IS NULL;
    -- reforça o invariante "exatamente uma Filial matriz por tenant"
```

## `configuracoes_regionais_tenant`

```sql
CREATE TABLE configuracoes_regionais_tenant (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    fuso_horario    TEXT NOT NULL DEFAULT 'America/Sao_Paulo',
    idioma          TEXT NOT NULL DEFAULT 'pt-BR',
    moeda_padrao    TEXT NOT NULL DEFAULT 'BRL',
    atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_configuracoes_regionais_tenant_id UNIQUE (tenant_id)
);
```

## `configuracoes_personalizacao`

Implementação física de White Label — tudo referência a Storage (D107), nunca binário (D148: só
apresentação, nunca lido por regra de negócio).

```sql
CREATE TABLE configuracoes_personalizacao (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                   UUID NOT NULL REFERENCES tenants(id),
    logo_arquivo_id             UUID,
    favicon_arquivo_id          UUID,
    cor_primaria                TEXT,
    cor_secundaria               TEXT,
    fonte                       TEXT,
    imagem_login_arquivo_id     UUID,
    nome_sistema_exibicao       TEXT,
    landing_arquivo_id          UUID,
    template_email_arquivo_id   UUID,
    status                      TEXT NOT NULL DEFAULT 'ATIVA',
    atualizado_em               TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_configuracoes_personalizacao_tenant_id UNIQUE (tenant_id)
);
```

## Índices de tenant obrigatórios (D174)

Toda tabela com `tenant_id` acima já tem `tenant_id` como primeira coluna de sua unique
constraint principal, que o PostgreSQL usa como índice — nenhuma tabela deste lote precisa de um
índice `tenant_id` solto adicional além dos já declarados.

## Como este arquivo cresce

Concluído para o escopo deste lote. Retomado em `011-administracao.md` para Grupo de Usuários,
Convite, Fator de Autenticação, Sessão de Acesso, Token de API, Bloqueio de Acesso, `logs_auditoria`
(já definida em `AUDIT_MODEL.md`), Configuração de Numeração, Parâmetro do Tenant, Configuração de
Integração, Webhook, Execução de Job.
