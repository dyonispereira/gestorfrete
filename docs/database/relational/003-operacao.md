# 003 — Operação (núcleo: Viagem)

Maior arquivo da Sprint 09. Traduz para SQL [`../dictionary/002-operacao.md`](../dictionary/002-operacao.md)
(14 entidades) mais duas trazidas de `001-cadastros.md` por dependência direta (ver seção de
reconciliação) e a infraestrutura física de D022/D023/D024, ainda não criada em nenhum lote
anterior. As 8 regras de [`../README.md`](../README.md) já se aplicam a toda tabela.

## Reconciliações antes de desenhar

| Ponto | Decisão |
|---|---|
| "Programação" (pedido nesta rodada) | Não é entidade — já reconciliado em `dictionary/002-operacao.md`: são os próprios atributos `data_programada`/`janela_programada` de `viagens` |
| "Tabela de Preço" (pedido nesta rodada) | Pertence a `001-cadastros.md` (dono `pricing`), mas sua tabela física nasce **aqui**, não em `002-cadastros.md` — `cotacoes` e `contratos_frete` precisam da FK e não há razão para adiar um cadastro que este lote já consome diretamente. Exceção deliberada ao mapeamento 1 lote ↔ 1 categoria (justificada por dependência real, não por conveniência) |
| Anexos/Comentários (D023/D024) | Nunca modelados fisicamente até este lote — Viagem é a primeira entidade cuja Timeline exige as duas. Criados aqui como infraestrutura compartilhada (D186), reutilizada por **todo** lote futuro, nunca recriada |
| Timeline Universal (D022) | Nunca uma tabela — sempre uma consulta (D187), ver seção própria |
| FKs para tabelas que ainda não existem (`veiculos_tracionadores`, `implementos` — chegam em `004-frota.md`) | Referenciadas desde já; a ordem real de criação nas migrations resolve a dependência (mesmo padrão já usado em `usuarios → motoristas` no Lote 2) |

---

## Infraestrutura compartilhada (D186) — `anexos` e `comentarios`

Criadas uma única vez; toda entidade com "Anexos suportados"/"Comentários suportados" no Data
Dictionary Funcional as usa por referência polimórfica, nunca ganha uma tabela própria.

```sql
CREATE TABLE anexos (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    entidade_tipo   TEXT NOT NULL,      -- 'VIAGEM', 'ENTREGA', 'CANHOTO', 'OCORRENCIA', 'ROMANEIO', ...
    entidade_id     UUID NOT NULL,
    tipo_anexo      TEXT NOT NULL,      -- vocabulário extensível (D120-style): 'FOTO', 'ASSINATURA', 'XML', 'PDF', ...
    arquivo_id      UUID NOT NULL,      -- referência lógica ao Storage (D107) — sem FK de banco
    descricao       TEXT,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    criado_por      UUID
);

CREATE INDEX idx_anexos_entidade_tipo_entidade_id ON anexos (entidade_tipo, entidade_id);

CREATE TABLE comentarios (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    entidade_tipo   TEXT NOT NULL,
    entidade_id     UUID NOT NULL,
    usuario_id      UUID NOT NULL REFERENCES usuarios(id),
    texto           TEXT NOT NULL,
    visivel_cliente BOOLEAN NOT NULL DEFAULT FALSE,   -- D023, ex: aviso de atraso visível ao Portal do Cliente
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_comentarios_entidade_tipo_entidade_id ON comentarios (entidade_tipo, entidade_id);
```

Sem `excluido_em`/`excluido_por` em nenhuma das duas — anexos e comentários seguem a mesma disciplina
de imutabilidade das entidades Históricas (D037): nunca removidos, no máximo substituídos por um
novo registro.

---

## `viagens`

Implementação física de `Viagem` — a entidade mais rica do sistema. Todo Snapshot (D038/D071/D073),
as três dimensões de status (D019/D020) e os pares Previsto/Realizado (D086/D098) existem
fisicamente, exatamente como já modelado em `dictionary/002-operacao.md`.

```sql
CREATE TYPE viagens_status_operacional_enum AS ENUM (
    'RASCUNHO', 'PLANEJADA', 'AGUARDANDO_CHECKLIST', 'LIBERADA', 'EM_DESLOCAMENTO', 'CARREGANDO',
    'EM_TRANSITO', 'EM_ENTREGA', 'FINALIZADA', 'INTERROMPIDA', 'CANCELADA'
);
CREATE TYPE viagens_status_fiscal_enum AS ENUM (
    'PENDENTE', 'CTE_EMITIDO', 'MDFE_EMITIDO', 'MDFE_ENCERRADO', 'CTE_CANCELADO'
);
CREATE TYPE viagens_status_financeiro_enum AS ENUM (
    'AGUARDANDO_FATURAMENTO', 'FATURADA', 'AGUARDANDO_RECEBIMENTO', 'RECEBIDA'
);

CREATE TABLE viagens (
    id                              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                       UUID NOT NULL REFERENCES tenants(id),
    codigo                          TEXT NOT NULL,
    versao                         INTEGER NOT NULL DEFAULT 1,

    -- Referências vivas (D033/D034) — nunca confundir com as colunas _snapshot abaixo
    cliente_id                      UUID NOT NULL REFERENCES clientes(id),
    motorista_id                    UUID REFERENCES motoristas(id),               -- nulo até PLANEJADA
    veiculo_tracionador_id          UUID REFERENCES veiculos_tracionadores(id),   -- tabela chega em 004-frota.md

    -- Programação (D076 — era "Agendamento" no pedido original, não é entidade própria)
    data_programada                 DATE,
    janela_programada               TIMESTAMPTZ,

    -- Três dimensões de status (D019/D020) — nunca colapsadas em uma só coluna
    status_operacional              viagens_status_operacional_enum NOT NULL DEFAULT 'RASCUNHO',
    status_fiscal                   viagens_status_fiscal_enum NOT NULL DEFAULT 'PENDENTE',
    status_financeiro                viagens_status_financeiro_enum NOT NULL DEFAULT 'AGUARDANDO_FATURAMENTO',

    -- Status composto ENCERRADA (D072/D185) — nunca gravável, sempre derivado
    encerrada                       BOOLEAN GENERATED ALWAYS AS (
                                         status_operacional = 'FINALIZADA'
                                         AND status_fiscal = 'MDFE_ENCERRADO'
                                         AND status_financeiro = 'RECEBIDA'
                                     ) STORED,

    -- Snapshots (D038/D071/D073) — capturados uma única vez, nunca ressincronizados
    nome_motorista_snapshot         TEXT,
    placa_veiculo_snapshot          TEXT,
    cliente_snapshot                JSONB,
    receita_prevista_snapshot        NUMERIC(14,2),
    tabela_preco_aplicada_snapshot_id UUID,   -- referência congelada, sem FK ON UPDATE (aponta para a versão usada)

    -- Financeiro Operacional (D086/D098 — pares Previsto/Realizado, nunca um substitui o outro)
    custo_previsto                   NUMERIC(14,2),
    custo_realizado                  NUMERIC(14,2),
    receita_realizada                NUMERIC(14,2),
    margem_prevista                  NUMERIC(14,2) GENERATED ALWAYS AS (receita_prevista_snapshot - custo_previsto) STORED,
    margem_realizada                 NUMERIC(14,2),   -- não gerada: só é definitiva em ENCERRADA (D019), calculada pela aplicação
    desvio_financeiro                NUMERIC(14,2),

    km_rodado                       NUMERIC(10,2),    -- Reconciliado (V1 Op. Hardening, Parte 2): derivado de leituras_hodometro (fleet), não mais de tracking (nunca implementado) — null até ter as 2 leituras de fronteira

    criado_em                       TIMESTAMPTZ NOT NULL DEFAULT now(),
    criado_por                      UUID,
    atualizado_em                   TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_por                  UUID,
    excluido_em                     TIMESTAMPTZ,
    excluido_por                    UUID,

    CONSTRAINT uq_viagens_tenant_id_codigo UNIQUE (tenant_id, codigo)
);

CREATE INDEX idx_viagens_tenant_id_status_operacional ON viagens (tenant_id, status_operacional) WHERE excluido_em IS NULL;
CREATE INDEX idx_viagens_tenant_id_motorista_id ON viagens (tenant_id, motorista_id) WHERE excluido_em IS NULL;
CREATE INDEX idx_viagens_tenant_id_veiculo_id ON viagens (tenant_id, veiculo_tracionador_id) WHERE excluido_em IS NULL;
CREATE INDEX idx_viagens_tenant_id_data_programada ON viagens (tenant_id, data_programada) WHERE excluido_em IS NULL;
CREATE INDEX idx_viagens_tenant_id_cliente_id ON viagens (tenant_id, cliente_id) WHERE excluido_em IS NULL;
CREATE INDEX idx_viagens_tenant_id_encerrada ON viagens (tenant_id, encerrada) WHERE excluido_em IS NULL;
```

`margem_realizada` **não** é `GENERATED` — ao contrário de `margem_prevista` (sempre calculável a
partir de duas colunas já fechadas), `margem_realizada` só é definitiva quando `encerrada = true`
(D019); antes disso é uma estimativa provisória que a aplicação recalcula e grava explicitamente a
cada atualização de `custo_realizado`/`receita_realizada` — uma coluna gerada recalcularia
implicitamente a cada leitura, escondendo a diferença entre "provisório" e "definitivo" que D019
exige tornar visível.

## `viagem_status_history`

Implementação física do histórico único que cobre as três dimensões + o registro automático de
`ENCERRADA` (D017/D018) — **maior volume de transições de qualquer entidade do sistema**
([`../../domain/002-operacao.md`](../../domain/002-operacao.md), nota de Auditoria de Viagem).

```sql
CREATE TYPE viagem_status_history_dimensao_enum AS ENUM ('OPERACIONAL', 'FISCAL', 'FINANCEIRO', 'COMPOSTO');

CREATE TABLE viagem_status_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    viagem_id       UUID NOT NULL REFERENCES viagens(id),
    dimensao        viagem_status_history_dimensao_enum NOT NULL,
    status          TEXT NOT NULL,     -- valor textual do enum da dimensão correspondente
    usuario_id      UUID,              -- nulo quando a transição é automática ('sistema')
    origem          TEXT NOT NULL,     -- 'app_motorista', 'portal_gestor', 'webhook_sefaz', ...
    data_hora       TIMESTAMPTZ NOT NULL DEFAULT now(),
    observacao      TEXT,              -- obrigatória (validada na aplicação) em INTERROMPIDA/CANCELADA/CTE_CANCELADO
    latitude        DOUBLE PRECISION,  -- predominante em transições de Status Operacional via app
    longitude       DOUBLE PRECISION
)
PARTITION BY RANGE (data_hora);
-- Muito Alto volume (information-model/HIGH_VOLUME_ENTITIES.md não listava esta tabela
-- explicitamente, mas a nota de domínio já a classificava como maior volume que qualquer outra
-- entidade — reclassificada aqui para "Muito Alto" e particionada por D179 desde já)

CREATE TABLE viagem_status_history_2026_01 PARTITION OF viagem_status_history
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
-- demais partições mensais criadas por job de manutenção (detalhe em MIGRATIONS.md)

CREATE INDEX idx_viagem_status_history_viagem_id_dimensao
    ON viagem_status_history (viagem_id, dimensao, data_hora);
```

> Este documento corrige a classificação de volume de `viagem_status_history`: ela não estava
> nomeada em `HIGH_VOLUME_ENTITIES.md` porque aquele documento cataloga entidades do Modelo de
> Domínio, e `ViagemStatusHistory` sempre foi tratada como parte do agregado Viagem, não uma entidade
> própria listada — na camada física ela precisa da mesma atenção de particionamento que qualquer
> outra tabela "Muito Alto" volume, então recebe aqui.

## `alocacoes_recurso_viagem`

```sql
CREATE TYPE alocacoes_recurso_viagem_status_enum AS ENUM ('VIGENTE', 'SUBSTITUIDA', 'ENCERRADA');
    -- ENCERRADA reconciliado no V1 Operational Hardening, Parte 1 — a Viagem dona terminou
    -- (Finalizada/Cancelada); distinto de SUBSTITUIDA (trocada por outra, Viagem ainda ativa).
    -- Coluna física é String livre (sem tipo Postgres físico), sem migration necessária.

CREATE TABLE alocacoes_recurso_viagem (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id),
    viagem_id               UUID NOT NULL REFERENCES viagens(id),
    motorista_id            UUID NOT NULL REFERENCES motoristas(id),
    veiculo_tracionador_id  UUID NOT NULL REFERENCES veiculos_tracionadores(id),  -- 004-frota.md
    implemento_id           UUID REFERENCES implementos(id),                     -- 004-frota.md
    status                  alocacoes_recurso_viagem_status_enum NOT NULL DEFAULT 'VIGENTE',
    motivo_troca            TEXT,
    criado_em               TIMESTAMPTZ NOT NULL DEFAULT now(),
    criado_por              UUID
);

CREATE UNIQUE INDEX uq_alocacoes_recurso_viagem_vigente
    ON alocacoes_recurso_viagem (viagem_id) WHERE status = 'VIGENTE';
    -- reforça o invariante "exatamente uma Alocação Vigente por Viagem" (D080)
```

## `pontos_parada_viagem`

```sql
CREATE TYPE pontos_parada_viagem_tipo_enum AS ENUM ('COLETA', 'ENTREGA', 'POSTO', 'PEDAGIO');
CREATE TYPE pontos_parada_viagem_status_enum AS ENUM ('PLANEJADO', 'CONCLUIDO');

CREATE TABLE pontos_parada_viagem (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    viagem_id       UUID NOT NULL REFERENCES viagens(id),
    tipo            pontos_parada_viagem_tipo_enum NOT NULL,
    ordem           INTEGER NOT NULL,
    localizacao     GEOGRAPHY(Point, 4326) NOT NULL,
    status          pontos_parada_viagem_status_enum NOT NULL DEFAULT 'PLANEJADO',

    CONSTRAINT uq_pontos_parada_viagem_viagem_id_ordem UNIQUE (viagem_id, ordem)
);
```

## `entregas`

```sql
CREATE TYPE entregas_status_enum AS ENUM ('PENDENTE', 'CONCLUIDA', 'RECUSADA', 'DEVOLVIDA', 'CANCELADA');

CREATE TABLE entregas (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id),
    viagem_id               UUID NOT NULL REFERENCES viagens(id),
    ordem                   INTEGER NOT NULL,
    destinatario            TEXT NOT NULL,
    endereco_entrega        JSONB NOT NULL,
    status                  entregas_status_enum NOT NULL DEFAULT 'PENDENTE',
    data_hora_conclusao     TIMESTAMPTZ,
    motivo_recusa           TEXT,

    CONSTRAINT uq_entregas_viagem_id_ordem UNIQUE (viagem_id, ordem)
    -- suporta N entregas por viagem (multi-drop) — nunca colunas entrega1/entrega2/entrega3
);

CREATE INDEX idx_entregas_viagem_id ON entregas (viagem_id);
```

## `janelas_entrega`

```sql
CREATE TABLE janelas_entrega (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),   -- D174/D193
    entrega_id      UUID NOT NULL REFERENCES entregas(id),
    hora_inicio     TIMESTAMPTZ NOT NULL,
    hora_fim        TIMESTAMPTZ NOT NULL,

    CONSTRAINT uq_janelas_entrega_entrega_id UNIQUE (entrega_id),
    CONSTRAINT ck_janelas_entrega_hora_fim_apos_inicio CHECK (hora_fim > hora_inicio)
);
```

## `coletas`

```sql
CREATE TABLE coletas (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),
    viagem_id           UUID NOT NULL REFERENCES viagens(id),
    data_hora           TIMESTAMPTZ NOT NULL,
    local                GEOGRAPHY(Point, 4326),
    conferencia_ok      BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_coletas_viagem_id ON coletas (viagem_id);
```

## `ocorrencias`

Genérica por design (D076) — nunca uma tabela por tipo (atraso/avaria/pane/devolução são todos
`tipo`, não tabelas).

```sql
CREATE TYPE ocorrencias_tipo_enum AS ENUM ('ATRASO', 'AVARIA', 'PANE', 'SINISTRO', 'OUTRO');
CREATE TYPE ocorrencias_gravidade_enum AS ENUM ('BAIXA', 'MEDIA', 'ALTA', 'CRITICA');
CREATE TYPE ocorrencias_status_enum AS ENUM ('ABERTA', 'RESOLVIDA');

CREATE TABLE ocorrencias (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    viagem_id       UUID NOT NULL REFERENCES viagens(id),
    tipo            ocorrencias_tipo_enum NOT NULL,
    descricao       TEXT NOT NULL,
    gravidade       ocorrencias_gravidade_enum,
    status          ocorrencias_status_enum NOT NULL DEFAULT 'ABERTA',
    data_hora       TIMESTAMPTZ NOT NULL DEFAULT now()
    -- "ocorrência sempre pertence a uma viagem": garantido por viagem_id UUID NOT NULL
);

CREATE INDEX idx_ocorrencias_viagem_id ON ocorrencias (viagem_id);
CREATE INDEX idx_ocorrencias_tenant_id_tipo ON ocorrencias (tenant_id, tipo);
```

## `romaneios` e `itens_carga`

```sql
CREATE TABLE romaneios (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),
    viagem_id           UUID NOT NULL REFERENCES viagens(id),
    numero_documento    TEXT
);

CREATE TABLE itens_carga (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),   -- D174/D193
    romaneio_id     UUID NOT NULL REFERENCES romaneios(id),
    descricao       TEXT NOT NULL,
    peso            NUMERIC(10,2) NOT NULL CHECK (peso > 0),
    quantidade      INTEGER NOT NULL CHECK (quantidade > 0)
);

CREATE INDEX idx_itens_carga_tenant_id ON itens_carga (tenant_id);
CREATE INDEX idx_itens_carga_romaneio_id ON itens_carga (romaneio_id);
```

## `canhotos`

```sql
CREATE TYPE canhotos_status_enum AS ENUM ('PENDENTE', 'REGISTRADO');

CREATE TABLE canhotos (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id),
    entrega_id              UUID NOT NULL REFERENCES entregas(id),
    status                  canhotos_status_enum NOT NULL DEFAULT 'PENDENTE',
    data_hora_registro      TIMESTAMPTZ,
    assinatura_arquivo_id   UUID,   -- referência lógica ao Storage (D107)

    CONSTRAINT uq_canhotos_entrega_id UNIQUE (entrega_id)
    -- "canhoto sempre pertence a uma entrega": garantido por entrega_id UUID NOT NULL + UNIQUE (1:1)
);
```

Fotos adicionais do canhoto físico (múltiplas por entrega, quando aplicável) usam a tabela
compartilhada `anexos` (`entidade_tipo = 'CANHOTO'`, `entidade_id = canhotos.id`) — nunca uma coluna
de foto no próprio `canhotos` nem uma tabela `canhoto_fotos` dedicada.

## `contratos_frete`

```sql
CREATE TYPE contratos_frete_status_enum AS ENUM ('ATIVO', 'ENCERRADO');

CREATE TABLE contratos_frete (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),
    codigo              TEXT NOT NULL,
    cliente_id          UUID NOT NULL REFERENCES clientes(id),
    tabela_preco_id     UUID REFERENCES tabelas_preco(id),
    vigencia_inicio     DATE NOT NULL,
    vigencia_fim        DATE,
    status              contratos_frete_status_enum NOT NULL DEFAULT 'ATIVO',
    sla_acordado        TEXT,
    criado_em           TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    excluido_em         TIMESTAMPTZ,

    CONSTRAINT uq_contratos_frete_tenant_id_codigo UNIQUE (tenant_id, codigo),
    CONSTRAINT ck_contratos_frete_vigencia CHECK (vigencia_fim IS NULL OR vigencia_fim > vigencia_inicio)
);
```

## `cotacoes` e `itens_cotacao`

```sql
CREATE TYPE cotacoes_status_enum AS ENUM ('RASCUNHO', 'APROVADA', 'RECUSADA', 'EXPIRADA');

CREATE TABLE cotacoes (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id),
    codigo                  TEXT NOT NULL,
    cliente_id              UUID NOT NULL REFERENCES clientes(id),
    contrato_frete_id       UUID REFERENCES contratos_frete(id),
    valor_total             NUMERIC(14,2) NOT NULL CHECK (valor_total > 0),
    status                  cotacoes_status_enum NOT NULL DEFAULT 'RASCUNHO',
    data_validade           DATE NOT NULL,
    criado_em               TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em           TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_cotacoes_tenant_id_codigo UNIQUE (tenant_id, codigo)
    -- "Cotação Aprovada nunca é editada": reforçado na aplicação (trigger opcional a avaliar em
    -- MIGRATIONS.md — bloquear UPDATE quando status = 'APROVADA', exceto a própria transição de status)
);

CREATE TABLE itens_cotacao (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),   -- D174/D193
    cotacao_id      UUID NOT NULL REFERENCES cotacoes(id),
    descricao       TEXT NOT NULL,
    valor           NUMERIC(14,2) NOT NULL CHECK (valor >= 0)
);

CREATE INDEX idx_itens_cotacao_tenant_id ON itens_cotacao (tenant_id);
CREATE INDEX idx_itens_cotacao_cotacao_id ON itens_cotacao (cotacao_id);
```

## `solicitacoes_frete`

```sql
CREATE TYPE solicitacoes_frete_status_enum AS ENUM ('REGISTRADA', 'COTADA', 'DESCARTADA');

CREATE TABLE solicitacoes_frete (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    cliente_id      UUID NOT NULL REFERENCES clientes(id),
    origem          JSONB NOT NULL,
    destinos        JSONB NOT NULL,
    tipo_carga      TEXT,
    prazo_desejado  DATE,
    status          solicitacoes_frete_status_enum NOT NULL DEFAULT 'REGISTRADA',
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## `tabelas_preco` e `itens_tabela_preco`

Implementadas no Lote 2 (`GESTORFRETE — PROMPT MESTRE`,
`alembic/versions/d10bc3b53be7_pricing_tabelas_preco.py`). O desenho abaixo substitui a versão
anterior deste documento (que usava `condicao TEXT` livre): o cálculo determinístico exigido pelo
Lote 2 precisava de critérios estruturados, não texto livre interpretado por humano. `direcao`
(VENDA/COMPRA) também é novo — o desenho original não previa frete de compra (pago a
transportador), que só passou a fazer sentido com o Acerto de Transportadores (backlog).

```sql
CREATE TYPE tabelas_preco_direcao_enum AS ENUM ('VENDA', 'COMPRA');
CREATE TYPE tabelas_preco_status_enum AS ENUM ('RASCUNHO', 'VIGENTE', 'EXPIRADA');
CREATE TYPE itens_tabela_preco_unidade_enum AS ENUM
    ('VIAGEM', 'KM', 'TONELADA', 'KG', 'FAIXA_DISTANCIA', 'PERCENTUAL');

CREATE TABLE tabelas_preco (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),
    nome                TEXT NOT NULL,
    direcao             tabelas_preco_direcao_enum NOT NULL,
    versao              INTEGER NOT NULL DEFAULT 1,   -- incrementa a cada mutação pós-criação
    vigencia_inicio     DATE NOT NULL,
    vigencia_fim        DATE,
    cliente_id          UUID REFERENCES clientes(id),   -- opcional, só VENDA — ausente = tabela geral
    status              tabelas_preco_status_enum NOT NULL DEFAULT 'RASCUNHO',
    criado_em           TIMESTAMPTZ NOT NULL DEFAULT now(),
    criado_por          UUID REFERENCES usuarios(id),
    atualizado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_por      UUID REFERENCES usuarios(id),

    CONSTRAINT ck_tabelas_preco_vigencia
        CHECK (vigencia_fim IS NULL OR vigencia_fim > vigencia_inicio),   -- D199
    CONSTRAINT ck_tabelas_preco_cliente_so_venda
        CHECK (direcao = 'VENDA' OR cliente_id IS NULL)
);
CREATE INDEX idx_tabelas_preco_tenant_id ON tabelas_preco (tenant_id);
CREATE INDEX idx_tabelas_preco_tenant_id_direcao_status ON tabelas_preco (tenant_id, direcao, status);

CREATE TABLE itens_tabela_preco (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id),   -- D174/D193
    tabela_preco_id         UUID NOT NULL REFERENCES tabelas_preco(id),
    unidade_calculo         itens_tabela_preco_unidade_enum NOT NULL,
    categoria_veiculo_id    UUID REFERENCES categorias_veiculo(id),   -- opcional — vazio = qualquer categoria
    origem_uf               CHAR(2),
    destino_uf              CHAR(2),
    faixa_distancia_min_km  NUMERIC(10,2),
    faixa_distancia_max_km  NUMERIC(10,2),
    faixa_modo              TEXT,   -- 'TARIFA_POR_KM' | 'VALOR_FIXO', obrigatório só p/ FAIXA_DISTANCIA
    valor                   NUMERIC(14,2) NOT NULL CHECK (valor > 0),
    valor_minimo            NUMERIC(14,2) CHECK (valor_minimo IS NULL OR valor_minimo > 0),
    adicional_fixo          NUMERIC(14,2),
    desconto_fixo           NUMERIC(14,2),
    adicional_percentual    NUMERIC(5,2),
    desconto_percentual     NUMERIC(5,2),
    base_percentual_descricao TEXT,   -- obrigatório quando unidade_calculo = 'PERCENTUAL'
    criado_em               TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ck_itens_tabela_preco_faixa_distancia_completa CHECK (
        unidade_calculo != 'FAIXA_DISTANCIA'
        OR (faixa_distancia_min_km IS NOT NULL AND faixa_distancia_max_km IS NOT NULL
            AND faixa_distancia_max_km > faixa_distancia_min_km
            AND faixa_modo IN ('TARIFA_POR_KM', 'VALOR_FIXO'))
    ),
    CONSTRAINT ck_itens_tabela_preco_percentual_exige_base
        CHECK (unidade_calculo != 'PERCENTUAL' OR base_percentual_descricao IS NOT NULL)
);

CREATE INDEX idx_itens_tabela_preco_tenant_id ON itens_tabela_preco (tenant_id);
CREATE INDEX idx_itens_tabela_preco_tabela_preco_id ON itens_tabela_preco (tabela_preco_id);
```

Cálculo (`modules/pricing/application/price_calculation_service.py`), ordem fixa, `Decimal`,
arredondamento só no passo final: valor base (conforme `unidade_calculo`) → `+ adicional_fixo` →
`- desconto_fixo` → `× (1 + adicional_percentual/100)` → `× (1 - desconto_percentual/100)` →
`max(resultado, valor_minimo)`.

`PERCENTUAL` nunca infere a base sozinho (nem do frete de venda, nem de nenhum outro campo) — o
item só guarda `base_percentual_descricao` (texto explicativo); o valor numérico da base é sempre
informado explicitamente pelo operador no momento da aplicação na Viagem.

Campos de rota (`origem_uf`/`destino_uf`) e faixa de distância existem no schema mas **a aplicação
automática por rota geográfica ainda não é possível** — depende de `modules/routing` (ainda vazio).
Nesta fase o operador escolhe manualmente o item compatível.

### `aplicacoes_tabela_preco_viagem`

Snapshot completo e append-only (nunca `UPDATE`/`DELETE` físico, D109-consistent) de cada aplicação
de Tabela de Frete numa Viagem — `alembic/versions/18bc06f9bb5a_freight_carga_rota_aplicacao_preco.py`.

```sql
CREATE TABLE aplicacoes_tabela_preco_viagem (
    id                              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                       UUID NOT NULL REFERENCES tenants(id),
    viagem_id                       UUID NOT NULL REFERENCES viagens(id),
    tabela_preco_id                 UUID NOT NULL REFERENCES tabelas_preco(id),
    item_tabela_preco_id            UUID NOT NULL REFERENCES itens_tabela_preco(id),
    tabela_preco_versao             INTEGER NOT NULL,
    direcao                         TEXT NOT NULL,
    unidade_calculo                 TEXT NOT NULL,
    quantidade_utilizada            NUMERIC(14,3),
    base_percentual_valor           NUMERIC(14,2),
    tarifa_aplicada                 NUMERIC(14,2) NOT NULL,
    valor_minimo_aplicado           NUMERIC(14,2),
    adicional_fixo_aplicado         NUMERIC(14,2),
    desconto_fixo_aplicado          NUMERIC(14,2),
    adicional_percentual_aplicado   NUMERIC(5,2),
    desconto_percentual_aplicado    NUMERIC(5,2),
    valor_calculado_bruto           NUMERIC(14,2) NOT NULL,
    valor_final                     NUMERIC(14,2) NOT NULL CHECK (valor_final >= 0),
    aplicado_em                     TIMESTAMPTZ NOT NULL,
    aplicado_por                    UUID NOT NULL REFERENCES usuarios(id),
    removido_em                     TIMESTAMPTZ,   -- "desfazer" marca, nunca apaga
    removido_por                    UUID REFERENCES usuarios(id)
);
CREATE INDEX idx_aplicacoes_tabela_preco_viagem_viagem_id ON aplicacoes_tabela_preco_viagem (viagem_id);
CREATE INDEX idx_aplicacoes_tabela_preco_viagem_tenant_id ON aplicacoes_tabela_preco_viagem (tenant_id);
```

`viagens.tabela_preco_aplicada_snapshot_id` (acima) continua apontando direto para
`tabelas_preco(id)` **sem** FK `ON UPDATE`/reatualização — snapshot (D073), inalterado por este
lote. `viagens.aplicacao_tabela_preco_atual_id` é novo: aponta para a linha ativa (não-removida)
em `aplicacoes_tabela_preco_viagem`, ou `NULL` se nenhuma aplicação está ativa.

### Dados de carga/percurso em `viagens` (par PREVISTO de `itens_carga`)

Também do Lote 2 — `itens_carga`/Romaneio (acima) só existem a partir da Coleta real (D005/D006),
tarde demais para o cálculo de frete PREVISTO na programação. Estes campos são a estimativa
informada na programação, nunca um duplicado do dado real de carga:

```sql
ALTER TABLE viagens ADD COLUMN origem_cidade TEXT;
ALTER TABLE viagens ADD COLUMN origem_uf CHAR(2);
ALTER TABLE viagens ADD COLUMN destino_cidade TEXT;
ALTER TABLE viagens ADD COLUMN destino_uf CHAR(2);
ALTER TABLE viagens ADD COLUMN distancia_prevista_km NUMERIC(10,2) CHECK (distancia_prevista_km IS NULL OR distancia_prevista_km > 0);
ALTER TABLE viagens ADD COLUMN peso_carga_kg NUMERIC(12,2) CHECK (peso_carga_kg IS NULL OR peso_carga_kg > 0);
ALTER TABLE viagens ADD COLUMN toneladas_carga NUMERIC(12,3)
    GENERATED ALWAYS AS (peso_carga_kg / 1000) STORED;   -- mesmo padrão de margem_prevista/encerrada
ALTER TABLE viagens ADD COLUMN tipo_carga TEXT;
ALTER TABLE viagens ADD COLUMN quantidade_carga INTEGER CHECK (quantidade_carga IS NULL OR quantidade_carga > 0);
ALTER TABLE viagens ADD COLUMN unidade_quantidade_carga TEXT;
ALTER TABLE viagens ADD COLUMN aplicacao_tabela_preco_atual_id UUID;
```

---

## Timeline Universal (D022/D187) — consulta, não tabela

```sql
-- Ilustrativo — a versão real vira uma VIEW ou é montada na camada de aplicação, não uma tabela.
SELECT 'STATUS' AS tipo_evento, dimensao::TEXT AS subtipo, status AS conteudo, data_hora
    FROM viagem_status_history WHERE viagem_id = :viagem_id
UNION ALL
SELECT 'COMENTARIO', NULL, texto, criado_em
    FROM comentarios WHERE entidade_tipo = 'VIAGEM' AND entidade_id = :viagem_id
UNION ALL
SELECT 'ANEXO', tipo_anexo, descricao, criado_em
    FROM anexos WHERE entidade_tipo = 'VIAGEM' AND entidade_id = :viagem_id
ORDER BY data_hora;
```

Nenhuma tabela nova para isso (D187) — a Timeline de uma Viagem é sempre a fusão de
`viagem_status_history` + `comentarios`/`anexos` (filtrados pela Viagem e por suas entidades filhas,
quando a UI quiser granularidade máxima) + eventos de outros bounded contexts relacionados (Ordem de
Serviço quando pane, Documento Fiscal quando emitido) — estes últimos buscados por consulta federada
na camada de aplicação, nunca replicados fisicamente aqui.

## Constraints de integridade — resumo

| Regra de negócio | Constraint física |
|---|---|
| Entrega sempre pertence a uma Viagem | `entregas.viagem_id UUID NOT NULL REFERENCES viagens(id)` |
| Canhoto sempre pertence a uma Entrega (1:1) | `canhotos.entrega_id UUID NOT NULL` + `uq_canhotos_entrega_id` |
| Ocorrência sempre pertence a uma Viagem | `ocorrencias.viagem_id UUID NOT NULL` |
| Histórico nunca existe sem Viagem | `viagem_status_history.viagem_id UUID NOT NULL` |
| `ENCERRADA` nunca editável diretamente | `GENERATED ALWAYS AS (...) STORED` (D185) |
| Exatamente uma Alocação `VIGENTE` por Viagem | `uq_alocacoes_recurso_viagem_vigente` (índice único parcial) |
| Multi-drop sem colunas fixas | `entregas` 1:N com `UNIQUE (viagem_id, ordem)`, nunca `entrega1`/`entrega2` |

Sobre **"snapshots nunca nulos quando viagem for iniciada"**: não modelado como `NOT NULL` direto na
coluna, porque os snapshots só existem a partir de `PLANEJADA`/aprovação da Cotação — `RASCUNHO`
legitimamente não os tem ainda. A obrigatoriedade condicional (nulo em `RASCUNHO`, obrigatório a
partir de `PLANEJADA`) é uma regra de transição de estado, melhor garantida na camada de aplicação
(mesmo padrão de `Cotação Aprovada imutável`, acima) do que por `CHECK` — um `CHECK` teria que
conhecer a máquina de estados inteira, violando a separação entre "estrutura" (banco) e "regra de
transição" (aplicação/domínio).

## Preparação para alta escala

- **Particionamento**: `viagem_status_history` particionada por mês desde a criação (D179, ver
  acima). `viagens`/`entregas`/`ocorrencias` não particionadas neste lote — volume "Médio"/"Alto"
  ([`../../information-model/HIGH_VOLUME_ENTITIES.md`](../../information-model/HIGH_VOLUME_ENTITIES.md)),
  reavaliar por tenant se algum cliente específico crescer muito além do esperado.
- **Índices compostos**: todos já listados começam por `tenant_id` (D174) — nunca um índice sem o
  tenant como primeiro componente.
- **Arquivamento**: `viagens.encerrada = true` há mais de N anos é candidata natural a mover para
  tabela fria/partição histórica — critério exato (N) e mecanismo (partição adicional vs. tabela
  separada) ficam para [`../../information-model/007-DATA_RETENTION.md`](../../information-model/007-DATA_RETENTION.md)
  quando esse documento for revisado à luz do schema físico, não decidido aqui.
- **Réplica de leitura**: nenhuma tabela deste lote tem obstáculo a replicação padrão do PostgreSQL
  (sem `UNLOGGED`, sem extensões que quebrem replicação lógica) — compatibilidade garantida por
  ausência de decisão em contrário, não por configuração especial.

## DER textual deste lote

```
                                    clientes
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                   │
            solicitacoes_frete    contratos_frete      tabelas_preco
                    │                  │                   │
                    │ 0..1              │ 0..1                │ N
                    ▼                  ▼                   ▼
                 cotacoes ──────────────┴───────────► itens_tabela_preco
                    │
                    │ itens_cotacao (1:N)
                    │
                    ▼ (aprovação)
                 viagens ◄──── motoristas, veiculos_tracionadores (referência viva)
                    │
      ┌─────────────┼──────────────┬───────────────┬──────────────┬───────────────┐
      │             │              │               │              │               │
viagem_status_  alocacoes_    pontos_parada_    entregas      ocorrencias      coletas
history         recurso_      viagem                │
                viagem                              ├── janelas_entrega (1:1)
                                                     └── canhotos (1:1)
                                                              │
                                                          romaneios ── itens_carga

  anexos / comentarios: polimórficos, apontam para qualquer tabela acima via
  (entidade_tipo, entidade_id) — arcos omitidos por espaço.
```

## Como este arquivo cresce

Concluído para o escopo deste lote — as 14 entidades de `002-operacao.md` mais `tabelas_preco`/
`itens_tabela_preco` (trazidas por dependência) e a infraestrutura compartilhada de Anexos/
Comentários. Próximo: `004-frota.md`, que finalmente cria `veiculos_tracionadores`/`implementos`
referenciados desde este lote.
