# 004 — Frota

Traduz para SQL as 10 entidades de
[`../dictionary/003-frota.md`](../dictionary/003-frota.md). Cria `veiculos_tracionadores`/
`implementos`, já referenciados por FK antecipada desde `003-operacao.md` (Lote 4). As 8 regras de
[`../README.md`](../README.md) já se aplicam a toda tabela.

## Sobre a recomendação de unificar alocações de recurso (D188)

Avaliado e **mantido o desenho atual** (`alocacoes_recurso_viagem`, um pacote único
Motorista+Veículo+Implemento por linha) em vez de generalizar para uma tabela polimórfica de
recursos. Razão: o invariante de domínio já registrado em `002-operacao.md` é "exatamente uma
Alocação **Vigente por Viagem**" — singular, um pacote coerente, não uma janela de vigência
independente por tipo de recurso. Se motorista e veículo pudessem ter vigências desacopladas na
mesma tabela genérica, uma troca de motorista sem troca de veículo (comum) exigiria decidir se o
veículo "continua" ou gera uma segunda linha — ambiguidade que o pacote único elimina por
construção, e que já reflete a realidade de negócio (uma reatribuição tem um motivo só,
`motivo_troca`, para o conjunto inteiro). A necessidade real por trás da sugestão — múltiplos
implementos simultâneos (bitrem/rodotrem) — já tem solução própria abaixo, em `Composição Veicular`
(N:N com Implemento), que é exatamente o nível certo para isso (frota, não por-viagem).

## Escopo e separação pedida

Identidade, características técnicas, documentação, estado operacional e configuração já eram
tratados como conceitos distintos em `docs/domain/003-frota.md` — aqui cada um vira sua própria
tabela, nunca misturados:

| Conceito | Tabela(s) |
|---|---|
| Identidade | `veiculos_tracionadores`, `implementos` |
| Características técnicas (permanentes, D082) | `fichas_tecnicas_veiculo` |
| Documentação | `documentos_veiculo`, `apolices_seguro_veicular`, `licenciamentos_veiculo` |
| Configuração (combinação) | `composicoes_veiculares` + `composicoes_veiculares_implementos` |
| Estado operacional (histórico, D083) | `leituras_hodometro` |
| Estado operacional (projeção atual, D081) | `disponibilidade_veiculo` |
| Referência | `categorias_veiculo` |

---

## `categorias_veiculo`

```sql
CREATE TABLE categorias_veiculo (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    codigo          TEXT NOT NULL,
    nome            TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'ATIVA',
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_categorias_veiculo_tenant_id_nome UNIQUE (tenant_id, nome)
);
```

## `veiculos_tracionadores`

```sql
CREATE TABLE veiculos_tracionadores (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id),
    codigo                  TEXT NOT NULL,
    versao                  INTEGER NOT NULL DEFAULT 1,
    placa                   TEXT NOT NULL,
    renavam                 TEXT NOT NULL,
    fabricante              TEXT NOT NULL,
    modelo                  TEXT NOT NULL,
    ano_fabricacao          INTEGER NOT NULL,
    categoria_veiculo_id    UUID NOT NULL REFERENCES categorias_veiculo(id),
    filial_id               UUID REFERENCES filiais(id),
    status                  TEXT NOT NULL DEFAULT 'ATIVO',
    criado_em               TIMESTAMPTZ NOT NULL DEFAULT now(),
    criado_por              UUID,
    atualizado_em           TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_por          UUID,
    excluido_em             TIMESTAMPTZ,
    excluido_por            UUID,

    CONSTRAINT uq_veiculos_tracionadores_tenant_id_codigo UNIQUE (tenant_id, codigo),
    CONSTRAINT uq_veiculos_tracionadores_tenant_id_placa UNIQUE (tenant_id, placa),
    CONSTRAINT uq_veiculos_tracionadores_tenant_id_renavam UNIQUE (tenant_id, renavam)
);

CREATE INDEX idx_veiculos_tracionadores_tenant_id_status
    ON veiculos_tracionadores (tenant_id, status) WHERE excluido_em IS NULL;
```

`placa` é **Atributo Crítico** (D077) no Data Dictionary — a governança (quem altera/quando/quem
nunca altera) é uma regra de aplicação (troca de placa é evento raro e auditado, `logs_auditoria`),
não uma constraint de schema adicional além do `UNIQUE` acima.

## `implementos`

```sql
CREATE TYPE implementos_tipo_carroceria_enum AS ENUM
    ('CARRETA', 'TANQUE', 'BAU', 'GRANELEIRO', 'PRANCHA', 'FRIGORIFICO', 'GAIOLA');
CREATE TYPE implementos_status_disponibilidade_enum AS ENUM ('DISPONIVEL', 'EM_USO', 'INATIVO');

CREATE TABLE implementos (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id),
    codigo                  TEXT NOT NULL,
    placa                   TEXT NOT NULL,
    renavam                 TEXT NOT NULL,
    tipo_carroceria         implementos_tipo_carroceria_enum NOT NULL,
    categoria_veiculo_id    UUID NOT NULL REFERENCES categorias_veiculo(id),
    capacidade_carga        NUMERIC(10,2) NOT NULL,
    status_disponibilidade  implementos_status_disponibilidade_enum NOT NULL DEFAULT 'DISPONIVEL',
    criado_em               TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em           TIMESTAMPTZ NOT NULL DEFAULT now(),
    excluido_em             TIMESTAMPTZ,

    CONSTRAINT uq_implementos_tenant_id_codigo UNIQUE (tenant_id, codigo),
    CONSTRAINT uq_implementos_tenant_id_placa UNIQUE (tenant_id, placa)
);
```

`TIPO_CARROCERIA` (Carreta/Tanque/Baú/Graneleiro/Prancha/Frigorífico/Gaiola) — nunca confundir com
`composicoes_veiculares.tipo_combinacao` (Simples/Bitrem/Rodotrem, abaixo): dimensões diferentes,
reconciliação já feita em `003-frota.md` (D076), preservada aqui.

## `composicoes_veiculares` e `composicoes_veiculares_implementos`

Suporta múltiplos implementos simultâneos (bitrem/rodotrem) — a resposta física à "preparação para
múltiplos implementos" pedida, via tabela de junção N:N, nunca colunas `implemento1`/`implemento2`.

```sql
CREATE TYPE composicoes_veiculares_tipo_combinacao_enum AS ENUM ('SIMPLES', 'BITREM', 'RODOTREM');
CREATE TYPE composicoes_veiculares_status_enum AS ENUM ('VALIDA', 'INVALIDA');

CREATE TABLE composicoes_veiculares (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                UUID NOT NULL REFERENCES tenants(id),
    veiculo_tracionador_id   UUID NOT NULL REFERENCES veiculos_tracionadores(id),
    tipo_combinacao          composicoes_veiculares_tipo_combinacao_enum NOT NULL,
    eixos_total              INTEGER NOT NULL,
    status                   composicoes_veiculares_status_enum NOT NULL DEFAULT 'VALIDA',
    data_inicio_vigencia     TIMESTAMPTZ NOT NULL DEFAULT now(),
    data_fim_vigencia        TIMESTAMPTZ,
    alterado_por             UUID,

    CONSTRAINT ck_composicoes_veiculares_vigencia
        CHECK (data_fim_vigencia IS NULL OR data_fim_vigencia > data_inicio_vigencia)   -- D199
);

CREATE TABLE composicoes_veiculares_implementos (
    composicao_veicular_id  UUID NOT NULL REFERENCES composicoes_veiculares(id),
    implemento_id           UUID NOT NULL REFERENCES implementos(id),
    ordem                   INTEGER NOT NULL,

    PRIMARY KEY (composicao_veicular_id, implemento_id)
);

CREATE UNIQUE INDEX uq_composicoes_veiculares_vigente
    ON composicoes_veiculares (veiculo_tracionador_id) WHERE data_fim_vigencia IS NULL;
```

Sobre **"Histórico de Alocação"** (pedido, "se ainda não consolidado"): já está — `data_fim_vigencia
IS NULL` marca a composição vigente; cada troca fecha a linha atual (`UPDATE ... SET
data_fim_vigencia = now()`) e insere uma nova. Nenhuma tabela `historico_composicao_veicular`
separada — o histórico **é** a própria tabela (D037: entidade Histórica é a tabela toda, não uma
tabela + um log paralelo). Mesmo princípio já usado em `alocacoes_recurso_viagem` (Lote 4).

## `fichas_tecnicas_veiculo`

```sql
CREATE TYPE fichas_tecnicas_veiculo_combustivel_enum AS ENUM ('DIESEL_S10', 'DIESEL_S500', 'GNV', 'ELETRICO');

CREATE TABLE fichas_tecnicas_veiculo (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id),   -- D174/D193
    veiculo_tracionador_id  UUID NOT NULL REFERENCES veiculos_tracionadores(id),
    chassi                  TEXT NOT NULL,
    motor                   TEXT,
    eixos                   INTEGER NOT NULL,
    tara                    NUMERIC(10,2) NOT NULL,
    capacidade_carga        NUMERIC(10,2) NOT NULL,
    pbt                     NUMERIC(10,2) NOT NULL,
    rntrc_proprietario      TEXT,
    combustivel             fichas_tecnicas_veiculo_combustivel_enum NOT NULL,

    CONSTRAINT uq_fichas_tecnicas_veiculo_veiculo_id UNIQUE (veiculo_tracionador_id),
    CONSTRAINT uq_fichas_tecnicas_veiculo_chassi UNIQUE (chassi)
);

CREATE INDEX idx_fichas_tecnicas_veiculo_tenant_id ON fichas_tecnicas_veiculo (tenant_id);
```

`chassi`/`renavam`/`ano_fabricacao` são **dados permanentes** (D082, imutáveis por padrão) — sem
coluna própria de bloqueio de edição (o schema não impede `UPDATE`); a auditoria reforçada exigida
por D082 vive em `logs_auditoria`, que registra qualquer alteração com o mesmo rigor de uma ação
sensível, não numa trava de banco.

## `documentos_veiculo`

```sql
CREATE TYPE documentos_veiculo_status_enum AS ENUM ('VALIDO', 'VENCIDO');

CREATE TABLE documentos_veiculo (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id),
    veiculo_tracionador_id  UUID NOT NULL REFERENCES veiculos_tracionadores(id),
    tipo                    TEXT NOT NULL,   -- ex: 'CRLV' — vocabulário extensível (D120-style)
    numero                  TEXT NOT NULL,
    data_validade           DATE NOT NULL,
    status                  documentos_veiculo_status_enum NOT NULL DEFAULT 'VALIDO',
    arquivo_id              UUID
);

CREATE INDEX idx_documentos_veiculo_veiculo_id ON documentos_veiculo (veiculo_tracionador_id);
```

## `apolices_seguro_veicular`

```sql
CREATE TYPE apolices_seguro_veicular_status_enum AS ENUM ('VIGENTE', 'VENCIDA');

CREATE TABLE apolices_seguro_veicular (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id),
    veiculo_tracionador_id  UUID NOT NULL REFERENCES veiculos_tracionadores(id),
    seguradora_id           UUID NOT NULL REFERENCES seguradoras(id),  -- 002-cadastros.md complemento
    numero_apolice          TEXT NOT NULL,
    vigencia_inicio         DATE NOT NULL,
    vigencia_fim            DATE NOT NULL,
    status                  apolices_seguro_veicular_status_enum NOT NULL DEFAULT 'VIGENTE',

    CONSTRAINT ck_apolices_seguro_veicular_vigencia CHECK (vigencia_fim > vigencia_inicio)
);
```

`seguradoras` não foi criada no Lote 3 (`002-cadastros.md`) — estava entre as 6 entidades
explicitamente adiadas para "lote de complemento". Criada agora, minimamente, por dependência real
(mesmo critério já usado para `tabelas_preco` no Lote 4):

```sql
CREATE TABLE seguradoras (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    codigo          TEXT NOT NULL,
    razao_social    TEXT NOT NULL,
    cnpj            TEXT NOT NULL,
    telefone        TEXT,
    status          TEXT NOT NULL DEFAULT 'ATIVA',

    CONSTRAINT uq_seguradoras_tenant_id_cnpj UNIQUE (tenant_id, cnpj)
);
```

## `licenciamentos_veiculo`

```sql
CREATE TYPE licenciamentos_veiculo_status_enum AS ENUM ('PENDENTE', 'QUITADO', 'VENCIDO');

CREATE TABLE licenciamentos_veiculo (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id),
    veiculo_tracionador_id  UUID NOT NULL REFERENCES veiculos_tracionadores(id),
    exercicio               INTEGER NOT NULL,
    valor_pago              NUMERIC(10,2),
    data_quitacao           DATE,
    status                  licenciamentos_veiculo_status_enum NOT NULL DEFAULT 'PENDENTE',

    CONSTRAINT uq_licenciamentos_veiculo_veiculo_id_exercicio UNIQUE (veiculo_tracionador_id, exercicio)
);
```

## `leituras_hodometro`

Entidade **Histórica/Time Series** (D037/D050) — nunca uma coluna `hodometro_atual` em
`veiculos_tracionadores`. Volume "Alto" ([`../../information-model/HIGH_VOLUME_ENTITIES.md`](../../information-model/HIGH_VOLUME_ENTITIES.md)) — particionada por mês (D179), mesmo padrão de
`viagem_status_history`.

```sql
CREATE TYPE leituras_hodometro_origem_enum AS ENUM ('ABASTECIMENTO', 'CHECKLIST', 'MANUAL', 'TELEMETRIA');

CREATE TABLE leituras_hodometro (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id),
    veiculo_tracionador_id  UUID NOT NULL REFERENCES veiculos_tracionadores(id),
    valor_km                NUMERIC(10,2) NOT NULL,
    origem                  leituras_hodometro_origem_enum NOT NULL,
    viagem_id               UUID REFERENCES viagens(id),
    data_hora               TIMESTAMPTZ NOT NULL DEFAULT now()
)
PARTITION BY RANGE (data_hora);

CREATE TABLE leituras_hodometro_2026_01 PARTITION OF leituras_hodometro
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE INDEX idx_leituras_hodometro_veiculo_id_data_hora
    ON leituras_hodometro (veiculo_tracionador_id, data_hora DESC);
```

Invariante "uma nova leitura nunca é menor que a última" (`shared/INVARIANTS.md`) — não expressa
como `CHECK` (um `CHECK` de linha não enxerga a leitura anterior); reforçada por trigger
`BEFORE INSERT` (comparando contra `MAX(valor_km)` do mesmo veículo) ou validação de aplicação —
decisão de implementação exata para `MIGRATIONS.md`, não fixada aqui.

## `disponibilidade_veiculo`

Read model (D081) — nunca a fonte de verdade de nada que resume.

```sql
CREATE TYPE disponibilidade_veiculo_status_enum AS ENUM ('DISPONIVEL', 'EM_VIAGEM', 'EM_MANUTENCAO', 'INATIVO');

CREATE TABLE disponibilidade_veiculo (
    veiculo_tracionador_id  UUID PRIMARY KEY REFERENCES veiculos_tracionadores(id),
    tenant_id               UUID NOT NULL REFERENCES tenants(id),   -- D174/D193
    status                  disponibilidade_veiculo_status_enum NOT NULL,
    motorista_atual_id      UUID REFERENCES motoristas(id),
    implemento_atual_id     UUID REFERENCES implementos(id),
    atualizado_em           TIMESTAMPTZ NOT NULL DEFAULT now()
    -- sem criado_por/atualizado_por: ninguém edita diretamente (D032) — só o processo consumidor de eventos
);

CREATE INDEX idx_disponibilidade_veiculo_tenant_id ON disponibilidade_veiculo (tenant_id);
```

Populada/atualizada exclusivamente por consumidores de evento (`ViagemDespachada`,
`ViagemConcluida`, `OrdemServicoAberta`, etc.) — nenhuma rota de API de escrita direta nesta tabela.

## FK de `003-operacao.md` agora resolvida

`viagens.veiculo_tracionador_id`, `alocacoes_recurso_viagem.veiculo_tracionador_id`/`implemento_id`
(Lote 4) apontavam para tabelas que só existem a partir deste lote — nenhuma alteração necessária
naqueles arquivos, a FK já estava correta, só a ordem de criação nas migrations depende deste lote
vir antes (ou as duas migrations na mesma transação de schema inicial).

## Constraints de integridade — resumo

| Regra de negócio | Constraint física |
|---|---|
| Placa única por tenant (Veículo e Implemento) | `uq_veiculos_tracionadores_tenant_id_placa`, `uq_implementos_tenant_id_placa` |
| Chassi único na plataforma | `uq_fichas_tecnicas_veiculo_chassi` |
| Uma Composição Veicular vigente por Veículo | `uq_composicoes_veiculares_vigente` (índice único parcial) |
| Hodômetro nunca decresce | Trigger/validação de aplicação (não expressável em `CHECK` de linha) |
| Disponibilidade nunca escrita por rota de API | Ausência deliberada de `criado_por`; reforçado em nível de aplicação/RBAC |

## Como este arquivo cresce

Concluído para o escopo deste lote. `seguradoras` trazida de `002-cadastros.md` por dependência
direta (mesmo critério já usado para `tabelas_preco`). Próximo: `005-manutencao.md`.
