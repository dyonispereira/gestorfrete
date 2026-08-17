# 007 — Fiscal

Traduz para SQL as 7 entidades de
[`../dictionary/007-fiscal.md`](../dictionary/007-fiscal.md). As 8 regras de
[`../README.md`](../README.md) já se aplicam a toda tabela. Filosofia confirmada e mantida:
documentos separados por responsabilidade (nunca uma tabela genérica "documentos"), `status_history`
próprio por agregado, XML sempre em `storage`, idempotência por constraint (não só por código),
numeração exclusiva de `configuracoes_fiscais_tenant`.

**D284 (Sprint 10 Lote 8, auditoria da API)**: `flows/009-FISCAL.md` especifica explicitamente que
as três tabelas de histórico usam "mesmos campos padrão (`id`, `documento_id`, `status`, `usuario`,
`origem`, `data_hora`, `observacao`)" — mas `ctes_status_history` não tinha `origem`,
`mdfes_status_history` não tinha `usuario_id`/`origem`, e `ciots_status_history` não tinha nenhum
dos três. Corrigido: as três tabelas abaixo já refletem os campos completos.

## `configuracoes_fiscais_tenant`

Única fonte de numeração de CT-e/MDF-e (D110/D175) — `ctes.numero`/`mdfes.numero` são uma **cópia**
capturada no momento da emissão (mesmo princípio de snapshot, D038), nunca uma sequência própria.

```sql
CREATE TYPE configuracoes_fiscais_tenant_ambiente_enum AS ENUM ('PRODUCAO', 'HOMOLOGACAO');

CREATE TABLE configuracoes_fiscais_tenant (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id),
    certificado_arquivo_id  UUID NOT NULL,
    certificado_validade    DATE NOT NULL,
    ambiente                configuracoes_fiscais_tenant_ambiente_enum NOT NULL DEFAULT 'HOMOLOGACAO',
    regime_tributario       TEXT NOT NULL,
    serie_cte               TEXT NOT NULL,
    proximo_numero_cte      BIGINT NOT NULL DEFAULT 1,
    serie_mdfe              TEXT NOT NULL,
    proximo_numero_mdfe     BIGINT NOT NULL DEFAULT 1,
    status                  TEXT NOT NULL DEFAULT 'ATIVA',

    CONSTRAINT uq_configuracoes_fiscais_tenant_id UNIQUE (tenant_id)
);
```

`proximo_numero_cte`/`proximo_numero_mdfe` nunca decrescem nem são reutilizados (D084) — obtidos de
forma atômica (`SELECT ... FOR UPDATE` na linha desta tabela, ou sequência dedicada por tenant, a
confirmar em `MIGRATIONS.md`), mesma nota já registrada em `UUID_STRATEGY.md`.

## `ctes` e `ctes_status_history`

```sql
CREATE TYPE ctes_status_enum AS ENUM (
    'RASCUNHO', 'VALIDADO', 'ASSINADO', 'TRANSMITIDO', 'AUTORIZADO', 'CANCELADO', 'DENEGADO',
    'INUTILIZADO'
);

CREATE TABLE ctes (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id),
    viagem_id               UUID NOT NULL REFERENCES viagens(id),
    numero                  TEXT NOT NULL,      -- capturado de configuracoes_fiscais_tenant no momento da emissão
    serie                   TEXT NOT NULL,
    chave_acesso            TEXT,                -- 44 dígitos, preenchida a partir de TRANSMITIDO
    valor_servico           NUMERIC(14,2) NOT NULL,
    status                  ctes_status_enum NOT NULL DEFAULT 'RASCUNHO',
    xml_arquivo_id           UUID,                -- D107 — obrigatório (aplicação) a partir de AUTORIZADO
    protocolo_sefaz          TEXT,                -- D111 — chave de idempotência
    data_hora_autorizacao    TIMESTAMPTZ,
    criado_em                TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em             TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_ctes_tenant_id_serie_numero UNIQUE (tenant_id, serie, numero),
    CONSTRAINT uq_ctes_chave_acesso UNIQUE (chave_acesso)
);

-- Idempotência por constraint (não só por código, pedido explícito): reprocessar a mesma resposta
-- da SEFAZ nunca deve conseguir gravar um segundo protocolo igual.
CREATE UNIQUE INDEX uq_ctes_protocolo_sefaz ON ctes (protocolo_sefaz) WHERE protocolo_sefaz IS NOT NULL;

CREATE TABLE ctes_status_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),   -- D174/D193
    cte_id          UUID NOT NULL REFERENCES ctes(id),
    status          TEXT NOT NULL,
    usuario_id      UUID,
    origem          TEXT NOT NULL,   -- D284 — 'documents' (automático, resposta SEFAZ) / usuário (ação manual)
    observacao      TEXT,   -- obrigatória (aplicação) em CANCELADO/DENEGADO
    data_hora       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_ctes_status_history_tenant_id ON ctes_status_history (tenant_id);
CREATE INDEX idx_ctes_tenant_id_status ON ctes (tenant_id, status);
CREATE INDEX idx_ctes_viagem_id ON ctes (viagem_id);
```

## `mdfes`, `mdfes_ctes` e `mdfes_status_history`

```sql
CREATE TYPE mdfes_status_enum AS ENUM ('PENDENTE', 'AUTORIZADO', 'ENCERRADO', 'CANCELADO');

CREATE TABLE mdfes (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id),
    viagem_id               UUID NOT NULL REFERENCES viagens(id),
    numero                  TEXT NOT NULL,
    serie                   TEXT NOT NULL,
    chave_acesso            TEXT,
    status                  mdfes_status_enum NOT NULL DEFAULT 'PENDENTE',
    xml_arquivo_id           UUID,
    protocolo_sefaz          TEXT,
    data_hora_encerramento   TIMESTAMPTZ,

    CONSTRAINT uq_mdfes_tenant_id_serie_numero UNIQUE (tenant_id, serie, numero),
    CONSTRAINT uq_mdfes_chave_acesso UNIQUE (chave_acesso)
);

CREATE UNIQUE INDEX uq_mdfes_protocolo_sefaz ON mdfes (protocolo_sefaz) WHERE protocolo_sefaz IS NOT NULL;

-- N:N — um MDF-e consolida um ou mais CT-e (multi-cliente/multi-carga)
CREATE TABLE mdfes_ctes (
    mdfe_id     UUID NOT NULL REFERENCES mdfes(id),
    cte_id      UUID NOT NULL REFERENCES ctes(id),

    PRIMARY KEY (mdfe_id, cte_id)
);

CREATE TABLE mdfes_status_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),   -- D174/D193
    mdfe_id         UUID NOT NULL REFERENCES mdfes(id),
    status          TEXT NOT NULL,
    usuario_id      UUID,   -- D284
    origem          TEXT NOT NULL,   -- D284
    observacao      TEXT,
    data_hora       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_mdfes_status_history_tenant_id ON mdfes_status_history (tenant_id);
CREATE INDEX idx_mdfes_viagem_id ON mdfes (viagem_id);
```

## `ciots` e `ciots_status_history`

```sql
CREATE TYPE ciots_status_enum AS ENUM ('PENDENTE', 'REGISTRADO', 'CANCELADO');

CREATE TABLE ciots (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),
    viagem_id           UUID NOT NULL REFERENCES viagens(id),
    motorista_id        UUID NOT NULL REFERENCES motoristas(id),   -- exige TIPO_VINCULO = AUTONOMO (validação de aplicação)
    codigo_ciot         TEXT,
    status              ciots_status_enum NOT NULL DEFAULT 'PENDENTE',
    protocolo_antt      TEXT,
    data_hora_registro  TIMESTAMPTZ,

    CONSTRAINT uq_ciots_codigo_ciot UNIQUE (codigo_ciot)
);

CREATE UNIQUE INDEX uq_ciots_protocolo_antt ON ciots (protocolo_antt) WHERE protocolo_antt IS NOT NULL;

CREATE TABLE ciots_status_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),   -- D174/D193
    ciot_id         UUID NOT NULL REFERENCES ciots(id),
    status          TEXT NOT NULL,
    usuario_id      UUID,   -- D284
    origem          TEXT NOT NULL,   -- D284
    observacao      TEXT,   -- D284
    data_hora       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_ciots_status_history_tenant_id ON ciots_status_history (tenant_id);
```

## `cartas_correcao`

```sql
CREATE TABLE cartas_correcao (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),
    cte_id              UUID NOT NULL REFERENCES ctes(id),
    numero_sequencial   INTEGER NOT NULL,
    texto_correcao      TEXT NOT NULL,
    xml_arquivo_id       UUID,
    data_hora_envio      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_cartas_correcao_cte_id_sequencial UNIQUE (cte_id, numero_sequencial)
    -- só aceita CT-e AUTORIZADO: validação de aplicação (não expressável como CHECK entre tabelas)
);
```

## `nfe_referenciadas`

```sql
CREATE TABLE nfe_referenciadas (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),   -- D174/D193
    cte_id          UUID NOT NULL REFERENCES ctes(id),
    chave_acesso    TEXT NOT NULL,
    xml_arquivo_id  UUID,

    CONSTRAINT ck_nfe_referenciadas_chave_44_digitos CHECK (chave_acesso ~ '^[0-9]{44}$')
);

CREATE INDEX idx_nfe_referenciadas_tenant_id ON nfe_referenciadas (tenant_id);
CREATE INDEX idx_nfe_referenciadas_cte_id ON nfe_referenciadas (cte_id);
```

## `eventos_fiscais`

Log técnico bruto (D105) — distinto dos `*_status_history` de negócio acima. Classificada "Alto"
volume ([`../../information-model/HIGH_VOLUME_ENTITIES.md`](../../information-model/HIGH_VOLUME_ENTITIES.md),
corrigida nesta rodada) — particionada por mês (D179), mesmo padrão de `viagem_status_history`.

```sql
CREATE TYPE eventos_fiscais_documento_tipo_enum AS ENUM ('CTE', 'MDFE', 'CIOT');
CREATE TYPE eventos_fiscais_tipo_evento_enum AS ENUM ('REQUISICAO', 'RESPOSTA');
CREATE TYPE eventos_fiscais_resultado_enum AS ENUM ('SUCESSO', 'FALHA', 'TIMEOUT');

CREATE TABLE eventos_fiscais (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),
    documento_tipo      eventos_fiscais_documento_tipo_enum NOT NULL,
    documento_id        UUID NOT NULL,   -- polimórfico, sem FK de banco (mesmo padrão de anexos/comentarios)
    tipo_evento         eventos_fiscais_tipo_evento_enum NOT NULL,
    payload_arquivo_id  UUID NOT NULL,   -- D107 — payload em storage, nunca inline
    protocolo_externo   TEXT,            -- D111 — chave de idempotência declarada
    data_hora_inicio    TIMESTAMPTZ NOT NULL,
    data_hora_fim        TIMESTAMPTZ,
    duracao_ms           INTEGER GENERATED ALWAYS AS (
                             EXTRACT(EPOCH FROM (data_hora_fim - data_hora_inicio)) * 1000
                         ) STORED,
    numero_tentativa     INTEGER NOT NULL DEFAULT 1,
    resultado            eventos_fiscais_resultado_enum,
    origem                TEXT NOT NULL   -- 'documents' (automático) / usuário (reenvio manual)
)
PARTITION BY RANGE (data_hora_inicio);

CREATE TABLE eventos_fiscais_2026_01 PARTITION OF eventos_fiscais
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

-- Idempotência por constraint: mesma combinação documento + protocolo nunca duplica
CREATE UNIQUE INDEX uq_eventos_fiscais_documento_protocolo
    ON eventos_fiscais (documento_tipo, documento_id, protocolo_externo)
    WHERE protocolo_externo IS NOT NULL;

CREATE INDEX idx_eventos_fiscais_documento_tipo_documento_id ON eventos_fiscais (documento_tipo, documento_id);
```

`duracao_ms` **é** `GENERATED` aqui (ao contrário de `ordens_servico.custo_realizado`) porque
depende só de duas colunas da própria linha (`data_hora_fim − data_hora_inicio`), não de agregação
entre tabelas — mesma regra já usada em `viagens.margem_prevista` (Lote 4).

## Constraints de integridade — resumo

| Regra de negócio | Constraint física |
|---|---|
| Protocolo SEFAZ único (idempotência, D111) | `uq_ctes_protocolo_sefaz`, `uq_mdfes_protocolo_sefaz` (índices únicos parciais) |
| Protocolo ANTT único (idempotência) | `uq_ciots_protocolo_antt` |
| Reprocessamento de Evento Fiscal nunca duplica | `uq_eventos_fiscais_documento_protocolo` |
| Numeração CT-e/MDF-e exclusiva de `configuracoes_fiscais_tenant` | Nenhuma coluna de sequência em `ctes`/`mdfes` — `numero` é sempre uma cópia capturada, nunca calculada localmente |
| Chave de acesso de 44 dígitos | `ck_nfe_referenciadas_chave_44_digitos` (mesma regra aplicável a `ctes.chave_acesso`/`mdfes.chave_acesso`, formato validado na aplicação por já serem geradas pela SEFAZ, não digitadas) |
| Documento fiscal nunca excluído (D109) | Nenhuma coluna `excluido_em`/`excluido_por` em `ctes`/`mdfes`/`ciots` — mesma exceção já aplicada a `logs_auditoria` |

## Como este arquivo cresce

Concluído para o escopo deste lote. Próximo: `008-rastreamento.md`.
