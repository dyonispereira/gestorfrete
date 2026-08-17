# 010 — Administração (Plataforma)

Traduz para SQL o restante das 20 entidades de
[`../dictionary/010-administracao.md`](../dictionary/010-administracao.md). As 8 regras de
[`../README.md`](../README.md) já se aplicam a toda tabela.

## Reconciliação — o que já existe, o que falta

**8 das 20 entidades já têm tabela física**, criadas nos Lotes 1/2 por dependência direta (mesmo
critério já usado várias vezes nesta sprint — não recriadas aqui):

| Entidade | Tabela | Onde foi criada |
|---|---|---|
| Tenant | `tenants` | Lote 2 (`001-core.md`) |
| Plano, Item de Plano | `planos`, `itens_plano` | Lote 2 |
| Assinatura, Cobrança Recorrente | `assinaturas`, `cobrancas_recorrentes` | Lote 2 |
| Configuração Regional do Tenant | `configuracoes_regionais_tenant` | Lote 2 |
| Configuração de Personalização | `configuracoes_personalizacao` | Lote 2 |
| Recurso Habilitado do Tenant | `recursos_habilitados_tenant` | Lote 2 |

**Correção (D193)**: `Log de Auditoria` estava listado aqui como "já criada em Lote 1
(`AUDIT_MODEL.md`)", mas `AUDIT_MODEL.md` é documentação da fundação (Lote 1), não um arquivo
`relational/NNN.md` — nunca existiu um `CREATE TABLE logs_auditoria` de fato em nenhum dos 12
arquivos. Gap real, encontrado na mesma auditoria de `tenant_id` que motivou D193. Corrigido abaixo,
nesta categoria (Administração), consistente com o texto de `AUDIT_MODEL.md`: "particionamento
físico exato fica no Modelo Relacional de Administração".

**12 entidades restantes** (11 novas + `Log de Auditoria`), organizadas nos grupos pedidos
(Identidade / Configuração do Tenant / Segurança / Integração-Administração da Plataforma /
Auditoria):

---

# Identidade

## `grupos_usuarios`

```sql
CREATE TABLE grupos_usuarios (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    nome            TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'ATIVO',

    CONSTRAINT uq_grupos_usuarios_tenant_id_nome UNIQUE (tenant_id, nome)
);

CREATE TABLE grupos_usuarios_usuarios (
    grupo_usuarios_id  UUID NOT NULL REFERENCES grupos_usuarios(id),
    usuario_id          UUID NOT NULL REFERENCES usuarios(id),

    PRIMARY KEY (grupo_usuarios_id, usuario_id)
    -- puramente organizacional (D076) — nunca uma segunda via de RBAC além de papel_permissao
);
```

## `convites`

```sql
CREATE TYPE convites_status_enum AS ENUM ('PENDENTE', 'ACEITO', 'EXPIRADO', 'REVOGADO');

CREATE TABLE convites (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    email           TEXT NOT NULL,
    papel_id        UUID NOT NULL REFERENCES papeis(id),
    data_expiracao  TIMESTAMPTZ NOT NULL,
    status          convites_status_enum NOT NULL DEFAULT 'PENDENTE',
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX uq_convites_tenant_id_email_pendente
    ON convites (tenant_id, email) WHERE status = 'PENDENTE';
```

## `fatores_autenticacao`

```sql
CREATE TYPE fatores_autenticacao_tipo_enum AS ENUM ('TOTP', 'SMS', 'EMAIL', 'BIOMETRIA');

CREATE TABLE fatores_autenticacao (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),   -- D174/D193
    usuario_id      UUID NOT NULL REFERENCES usuarios(id),
    tipo            fatores_autenticacao_tipo_enum NOT NULL,
    status          TEXT NOT NULL DEFAULT 'ATIVO',

    CONSTRAINT uq_fatores_autenticacao_usuario_id_tipo UNIQUE (usuario_id, tipo)
);

CREATE INDEX idx_fatores_autenticacao_tenant_id ON fatores_autenticacao (tenant_id);
```

---

# Configuração do Tenant

## `configuracoes_numeracao`

```sql
CREATE TABLE configuracoes_numeracao (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),
    tipo_entidade       TEXT NOT NULL,   -- 'VIAGEM'/'ORDEM_SERVICO'/... — nunca documento fiscal (D110)
    prefixo             TEXT,
    proximo_numero      BIGINT NOT NULL DEFAULT 1,

    CONSTRAINT uq_configuracoes_numeracao_tenant_id_tipo UNIQUE (tenant_id, tipo_entidade)
);
```

## `parametros_tenant`

Formaliza o que já vinha sendo referenciado desde `004-manutencao.md` (alçada de aprovação) e
`009-app_motorista.md` (evidência de conclusão exigida). Histórico via vigência (D143/D144), padrão
× sobrescrita no mesmo registro (D145).

```sql
CREATE TABLE parametros_tenant (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                   UUID NOT NULL REFERENCES tenants(id),
    chave                       TEXT NOT NULL,
    tipo_valor                  TEXT NOT NULL,   -- 'MONETARIO'/'BOOLEANO'/'INTEIRO'/'DECIMAL'/'TEXTO'
    categoria                   TEXT NOT NULL,
    valor_padrao_plataforma     TEXT NOT NULL,
    valor_sobrescrito_tenant    TEXT,
    data_inicio_vigencia        TIMESTAMPTZ NOT NULL DEFAULT now(),
    data_fim_vigencia           TIMESTAMPTZ,
    status                      TEXT NOT NULL DEFAULT 'VIGENTE',

    CONSTRAINT ck_parametros_tenant_vigencia
        CHECK (data_fim_vigencia IS NULL OR data_fim_vigencia > data_inicio_vigencia)   -- D199
);

CREATE UNIQUE INDEX uq_parametros_tenant_vigente
    ON parametros_tenant (tenant_id, chave) WHERE status = 'VIGENTE';
```

---

# Segurança

## `sessoes_acesso`

Equivalente administrativo de `sessoes_mobile` (Lote 10) — mesma disciplina D140/D060/D132.

```sql
CREATE TYPE sessoes_acesso_status_enum AS ENUM ('ATIVA', 'EXPIRADA', 'ENCERRADA');

CREATE TABLE sessoes_acesso (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                   UUID NOT NULL REFERENCES tenants(id),
    usuario_id                  UUID NOT NULL REFERENCES usuarios(id),
    data_hora_inicio             TIMESTAMPTZ NOT NULL DEFAULT now(),
    data_hora_expiracao_prevista TIMESTAMPTZ NOT NULL,
    motivo_encerramento          TEXT,
    status                       sessoes_acesso_status_enum NOT NULL DEFAULT 'ATIVA'
    -- sem coluna de permissão: RBAC sempre resolvido ao vivo (D060), mesmo princípio de sessoes_mobile
);

CREATE INDEX idx_sessoes_acesso_usuario_id_status ON sessoes_acesso (usuario_id, status);
```

## `tokens_api`

```sql
CREATE TYPE tokens_api_status_enum AS ENUM ('ATIVO', 'REVOGADO');

CREATE TABLE tokens_api (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id),
    usuario_tecnico_id       UUID NOT NULL REFERENCES usuarios(id),
    token_hash               TEXT NOT NULL,
    data_hora_ultimo_uso      TIMESTAMPTZ,
    status                    tokens_api_status_enum NOT NULL DEFAULT 'ATIVO',
    criado_em                 TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_tokens_api_token_hash UNIQUE (token_hash)
);
```

## `bloqueios_acesso`

```sql
CREATE TYPE bloqueios_acesso_tipo_enum AS ENUM ('AUTOMATICO', 'ADMINISTRATIVO');
CREATE TYPE bloqueios_acesso_status_enum AS ENUM ('VIGENTE', 'REMOVIDO');

CREATE TABLE bloqueios_acesso (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    usuario_id      UUID NOT NULL REFERENCES usuarios(id),
    tipo            bloqueios_acesso_tipo_enum NOT NULL,
    motivo          TEXT,   -- obrigatório (aplicação) quando tipo = ADMINISTRATIVO (D010)
    status          bloqueios_acesso_status_enum NOT NULL DEFAULT 'VIGENTE'
);

CREATE UNIQUE INDEX uq_bloqueios_acesso_usuario_vigente
    ON bloqueios_acesso (usuario_id) WHERE status = 'VIGENTE';
```

---

# Integração / Administração da Plataforma

Bounded context `integration` — deliberadamente distinto de `settings` (as duas seções acima), por
lidar com sistemas de terceiros, não configuração interna.

## `configuracoes_integracao`

```sql
CREATE TYPE configuracoes_integracao_status_enum AS ENUM ('ATIVA', 'INATIVA', 'COM_ERRO');

CREATE TABLE configuracoes_integracao (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id),
    tipo                    TEXT NOT NULL,
    credencial_arquivo_id    UUID NOT NULL,   -- D107 — cofre de segredos, nunca texto claro
    status                   configuracoes_integracao_status_enum NOT NULL DEFAULT 'ATIVA'
);
```

## `webhooks`

```sql
CREATE TYPE webhooks_status_enum AS ENUM ('ATIVO', 'INATIVO', 'SUSPENSO');

CREATE TABLE webhooks (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                   UUID NOT NULL REFERENCES tenants(id),
    configuracao_integracao_id   UUID REFERENCES configuracoes_integracao(id),
    url_destino                  TEXT NOT NULL,
    eventos_assinados            JSONB NOT NULL,
    segredo_hmac_arquivo_id       UUID NOT NULL,   -- D107
    status                        webhooks_status_enum NOT NULL DEFAULT 'ATIVO'
);

CREATE INDEX idx_webhooks_tenant_id_status ON webhooks (tenant_id, status);
CREATE INDEX idx_webhooks_eventos_assinados ON webhooks USING GIN (eventos_assinados);   -- D198
```

## `execucoes_job`

```sql
CREATE TYPE execucoes_job_resultado_enum AS ENUM ('SUCESSO', 'FALHA');

CREATE TABLE execucoes_job (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID REFERENCES tenants(id),   -- opcional — ausente quando job é de plataforma
    tipo_job            TEXT NOT NULL,
    data_hora_inicio     TIMESTAMPTZ NOT NULL,
    data_hora_fim        TIMESTAMPTZ,
    resultado            execucoes_job_resultado_enum
)
PARTITION BY RANGE (data_hora_inicio);

CREATE TABLE execucoes_job_2026_01 PARTITION OF execucoes_job
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
```

Particionada por mês — job assíncrono é, por natureza, alto volume técnico e append-only, mesma
categoria de `eventos_fiscais`/`logs_auditoria`.

---

# Auditoria

## `logs_auditoria`

Implementação física de `Log de Auditoria` ([`../dictionary/010-administracao.md`](../dictionary/010-administracao.md))
e de D176/D007 — desenho já fixado em [`../AUDIT_MODEL.md`](../AUDIT_MODEL.md); esta é a primeira vez
que o `CREATE TABLE` de fato existe em um arquivo `relational/` (D193/D194 — gap encontrado na
auditoria de `tenant_id` feita ao preparar `TABLES.md`: o arquivo de fundação descrevia a tabela em
detalhe, mas nenhum lote nunca a criou de verdade).

```sql
CREATE TYPE logs_auditoria_acao_enum AS ENUM (
    'CRIACAO', 'ALTERACAO', 'EXCLUSAO_LOGICA', 'LOGIN', 'LOGOUT', 'TRANSICAO_STATUS'
    -- vocabulário extensível (D120-style) — novas ações via ALTER TYPE ... ADD VALUE
);

CREATE TYPE logs_auditoria_origem_enum AS ENUM ('WEB', 'MOBILE', 'API', 'SISTEMA');

CREATE TABLE logs_auditoria (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id            UUID NOT NULL REFERENCES tenants(id),
    entidade_tipo        TEXT NOT NULL,
    entidade_id          UUID NOT NULL,
    acao                 logs_auditoria_acao_enum NOT NULL,
    ator_id              UUID,                     -- nulo quando ACAO é de origem 'SISTEMA'
    ator_nome_snapshot   TEXT NOT NULL,             -- D147 — nunca depende do Usuário ainda existir
    origem                logs_auditoria_origem_enum NOT NULL,
    dados_antes          JSONB,
    dados_depois         JSONB,
    motivo               TEXT,
    id_correlacao        UUID NOT NULL,
    data_hora            TIMESTAMPTZ NOT NULL DEFAULT now()
    -- sem atualizado_em/atualizado_por/excluido_em/excluido_por: logs_auditoria nunca é
    -- atualizada nem excluída, nem logicamente (D001/D037/D109)
)
PARTITION BY RANGE (data_hora);

CREATE TABLE logs_auditoria_2026_01 PARTITION OF logs_auditoria
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE INDEX idx_logs_auditoria_tenant_id_entidade
    ON logs_auditoria (tenant_id, entidade_tipo, entidade_id, data_hora DESC);
CREATE INDEX idx_logs_auditoria_id_correlacao ON logs_auditoria (id_correlacao);
```

Particionada por `tenant_id` + `data_hora` na classificação de volume ("Muito Alto",
[`../../information-model/HIGH_VOLUME_ENTITIES.md`](../../information-model/HIGH_VOLUME_ENTITIES.md))
mas fisicamente só por `data_hora` (D179 permite range mensal simples quando o filtro por tenant já
é coberto pelo primeiro componente de todo índice de consulta, mesmo padrão de `execucoes_job`
acima).

---

# Storage — Arquivo (D324, Sprint 10/Lote 12)

Toda tabela do sistema com um atributo `Arquivo`/`Imagem` guarda apenas `*_arquivo_id UUID`, **sem
FK de banco** (D107) — o binário vive no MinIO/S3, fora do PostgreSQL
(`DATABASE_ARCHITECTURE.md` §2). Até este lote, porém, nenhuma tabela sequer registrava os
*metadados* do arquivo (nome, tipo MIME, tamanho, hash, versão) — apesar de D024 já especificar
exatamente esses atributos ("versão, autor, data, tamanho, tipo e hash do arquivo") desde a
primeira decisão do projeto. Mesmo padrão de gap da família D196/D222/D269/.../D313: documentado
desde a origem, nunca fisicamente traduzido. Corrigido agora, ao preparar
`docs/api/078-storage.md`/`079-files.md`.

## `arquivos`

```sql
CREATE TYPE arquivos_origem_enum AS ENUM ('UPLOAD_DIRETO', 'GERADO_PELO_SISTEMA', 'IMPORTADO');
CREATE TYPE arquivos_status_enum AS ENUM ('ATIVO', 'EXCLUIDO');

CREATE TABLE arquivos (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id),
    nome_original           TEXT NOT NULL,
    tipo_mime               TEXT NOT NULL,
    tamanho_bytes           BIGINT NOT NULL,
    hash_sha256             TEXT NOT NULL,
    versao                  INTEGER NOT NULL DEFAULT 1,
    arquivo_anterior_id     UUID REFERENCES arquivos(id),   -- versão anterior, quando aplicável
    origem                  arquivos_origem_enum NOT NULL,
    storage_key             TEXT NOT NULL,   -- bucket+chave do objeto físico no MinIO/S3 (D107) — nunca binário aqui
    status                  arquivos_status_enum NOT NULL DEFAULT 'ATIVO',
    criado_em               TIMESTAMPTZ NOT NULL DEFAULT now(),
    criado_por              UUID REFERENCES usuarios(id)
);

CREATE INDEX idx_arquivos_tenant_id ON arquivos (tenant_id);
```

**Escopo deliberadamente contido**: as dezenas de colunas `*_arquivo_id` já existentes em outras
tabelas (`anexos.arquivo_id`, `ctes.xml_arquivo_id`, `webhooks.segredo_hmac_arquivo_id`,
`configuracoes_integracao.credencial_arquivo_id`, etc., ~15 tabelas em 8 arquivos `relational/`)
**não** ganham uma FK física para `arquivos.id` nesta preparação — continuam exatamente como D107
sempre definiu, referência lógica sem FK de banco. Retrofitting de FK em módulos já publicados é
uma mudança estrutural ampla, fora do escopo de um lote de API (mesma disciplina de "arquitetura
congelada" já aplicada a `Vehicle.tracking_reference`, D250, Lote 5/9) — `arquivos` agora dá a essas
colunas um destino real de metadados para consultar via API, mas o vínculo permanece lógico, nunca
reforçado pelo banco.

---

# Notificações — Notificação, Preferência de Canal (D323, Sprint 10/Lote 12)

Traduz `Bloco 7` de [`../dictionary/010-administracao.md`](../dictionary/010-administracao.md) —
`RBAC_MATRIX.md` §7.24 já tinha os códigos, a entidade nunca existiu em Domain/DDL.

## `notificacoes`

```sql
CREATE TYPE notificacoes_canal_enum AS ENUM ('IN_APP', 'PUSH', 'EMAIL');
CREATE TYPE notificacoes_status_enum AS ENUM ('NAO_LIDA', 'LIDA');

CREATE TABLE notificacoes (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                   UUID NOT NULL REFERENCES tenants(id),
    usuario_destinatario_id     UUID NOT NULL REFERENCES usuarios(id),
    canal                       notificacoes_canal_enum NOT NULL,
    evento_origem_tipo          TEXT NOT NULL,   -- ex.: 'ViagemAtrasada' — nome do evento, nunca o evento em si (D320)
    entidade_tipo               TEXT,            -- referência opcional polimórfica, mesmo padrão de anexos/comentarios (D186)
    entidade_id                 UUID,
    titulo                      TEXT NOT NULL,
    mensagem                    TEXT NOT NULL,
    status                      notificacoes_status_enum NOT NULL DEFAULT 'NAO_LIDA',
    enviado_em                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    lido_em                     TIMESTAMPTZ
);

CREATE INDEX idx_notificacoes_usuario_destinatario_status
    ON notificacoes (usuario_destinatario_id, status, enviado_em DESC);
```

Não particionada nesta fundação — volume ainda não confirmado como "Alto" (D201: precisa de 3 dos 4
fatores — crescimento sustentado, origem automática, consulta sempre limitada por período, retenção
diferenciada — antes de forçar particionamento; revisitar quando houver dado real de volume).

## `preferencias_notificacao`

```sql
CREATE TABLE preferencias_notificacao (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    usuario_id      UUID NOT NULL REFERENCES usuarios(id),
    canal           notificacoes_canal_enum NOT NULL,
    habilitado      BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT uq_preferencias_notificacao_usuario_canal UNIQUE (usuario_id, canal)
);
```

---

## Constraints de integridade — resumo

| Regra de negócio | Constraint física |
|---|---|
| Convite pendente único por e-mail/tenant | `uq_convites_tenant_id_email_pendente` |
| No máximo um Parâmetro `VIGENTE` por chave/tenant (D145) | `uq_parametros_tenant_vigente` |
| No máximo um Bloqueio `VIGENTE` por Usuário | `uq_bloqueios_acesso_usuario_vigente` |
| Token de API nunca reutilizado (D084) | `uq_tokens_api_token_hash` |
| Grupo de Usuários nunca é segunda via de RBAC | Sem coluna de permissão em `grupos_usuarios`/`grupos_usuarios_usuarios` |
| Preferência de Canal única por Usuário/Canal | `uq_preferencias_notificacao_usuario_canal` |

## Como este arquivo cresce

Concluído para o escopo original deste lote — as 11 tabelas que ainda faltavam das 20 entidades de
`010-administracao.md`, mais `logs_auditoria` (D193/D194, gap retroativo). Estendido no Sprint
10/Lote 12 (Recursos Transversais da API) com `arquivos` (D324) e `notificacoes`/
`preferencias_notificacao` (D323) — gaps de Domain/DDL encontrados na auditoria D200 daquele lote,
mesma disciplina de todo o sprint.
