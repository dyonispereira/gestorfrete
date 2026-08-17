# 008 — Rastreamento

Traduz para SQL as 9 entidades de
[`../dictionary/008-rastreamento.md`](../dictionary/008-rastreamento.md) — o lote de maior volume de
dados de toda a modelagem relacional. As 8 regras de [`../README.md`](../README.md) já se aplicam a
toda tabela.

## Padrão único de Time Series (D191, formalizado nesta rodada)

`posicoes_veiculo`, `leituras_telemetria` e `heartbeats` seguem exatamente o mesmo esqueleto — nunca
divergem em nome de coluna ou estrutura:

```sql
-- Esqueleto de referência (não uma tabela real) — toda tabela Time Series abaixo o segue à risca:
--
-- id                UUID PRIMARY KEY DEFAULT gen_random_uuid()
-- tenant_id         UUID NOT NULL REFERENCES tenants(id)
-- <entidade>_id      UUID NOT NULL              -- veiculo_tracionador_id / equipamento_rastreamento_id
-- capturado_em       TIMESTAMPTZ NOT NULL         -- D124/D125 — no dispositivo/fonte externa
-- recebido_em        TIMESTAMPTZ NOT NULL         -- D124/D125 — quando o GestorFrete recebeu
-- processado_em      TIMESTAMPTZ NOT NULL         -- D125 — quando foi persistido/interpretado
-- ... colunas específicas da entidade ...
--
-- PARTITION BY RANGE (capturado_em)  — mensal, D179
-- índice: (<entidade>_id, capturado_em)
```

---

## `provedores_rastreamento`

```sql
CREATE TABLE provedores_rastreamento (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    nome            TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'ATIVO',

    CONSTRAINT uq_provedores_rastreamento_tenant_id_nome UNIQUE (tenant_id, nome)
);
```

## `equipamentos_rastreamento`

Suporta múltiplos equipamentos simultâneos por veículo (D128) — Principal/Backup/Câmera/Sensor de
Temperatura/TPMS.

```sql
CREATE TYPE equipamentos_rastreamento_tipo_enum AS ENUM
    ('PRINCIPAL', 'BACKUP', 'CAMERA', 'SENSOR_TEMPERATURA', 'TPMS', 'OUTRO');
CREATE TYPE equipamentos_rastreamento_status_enum AS ENUM ('ATIVO', 'INATIVO', 'REMOVIDO');

CREATE TABLE equipamentos_rastreamento (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                UUID NOT NULL REFERENCES tenants(id),
    provedor_rastreamento_id UUID NOT NULL REFERENCES provedores_rastreamento(id),
    identificador_serial     TEXT NOT NULL,
    tipo_equipamento         equipamentos_rastreamento_tipo_enum NOT NULL,
    veiculo_tracionador_id   UUID REFERENCES veiculos_tracionadores(id),
    data_inicio_vigencia     TIMESTAMPTZ,
    data_fim_vigencia        TIMESTAMPTZ,
    alterado_por             UUID,
    status                   equipamentos_rastreamento_status_enum NOT NULL DEFAULT 'ATIVO',

    CONSTRAINT uq_equipamentos_rastreamento_identificador_serial UNIQUE (identificador_serial),
    CONSTRAINT ck_equipamentos_rastreamento_vigencia
        CHECK (data_fim_vigencia IS NULL OR data_inicio_vigencia IS NULL OR data_fim_vigencia > data_inicio_vigencia)   -- D199
);

CREATE UNIQUE INDEX uq_equipamentos_rastreamento_principal_vigente
    ON equipamentos_rastreamento (veiculo_tracionador_id)
    WHERE tipo_equipamento = 'PRINCIPAL' AND data_fim_vigencia IS NULL;
    -- no máximo um Principal vigente por veículo — demais papéis podem coexistir livremente (D128)
```

## `origens_localizacao`

Platform Reference Data (D046) — catálogo técnico, sem `tenant_id`.

```sql
CREATE TABLE origens_localizacao (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome                    TEXT NOT NULL UNIQUE,   -- GPS/GSM/Satélite/Wi-Fi/BLE/Manual/API Externa
    precisao_tipica_metros  NUMERIC(6,2)
);
```

## `posicoes_veiculo`

Segue o padrão D191 à risca — a entidade mais consultada do sistema.

```sql
CREATE TABLE posicoes_veiculo (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                   UUID NOT NULL REFERENCES tenants(id),
    veiculo_tracionador_id      UUID NOT NULL,
    equipamento_rastreamento_id UUID NOT NULL,
    localizacao                 GEOGRAPHY(Point, 4326) NOT NULL,
    origem_localizacao_id       UUID NOT NULL REFERENCES origens_localizacao(id),
    precisao_metros             NUMERIC(6,2),
    numero_satelites            SMALLINT,
    hdop                         NUMERIC(4,2),
    nivel_confianca              NUMERIC(5,2),
    capturado_em                 TIMESTAMPTZ NOT NULL,
    recebido_em                  TIMESTAMPTZ NOT NULL,
    processado_em                 TIMESTAMPTZ NOT NULL DEFAULT now()
)
PARTITION BY RANGE (capturado_em);

CREATE TABLE posicoes_veiculo_2026_01 PARTITION OF posicoes_veiculo
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE INDEX idx_posicoes_veiculo_veiculo_id_capturado_em
    ON posicoes_veiculo (veiculo_tracionador_id, capturado_em DESC);
CREATE INDEX idx_posicoes_veiculo_localizacao
    ON posicoes_veiculo USING GIST (localizacao);   -- D197 — gap encontrado ao preparar INDEXES.md
```

Sem FK física em `veiculo_tracionador_id`/`equipamento_rastreamento_id` **dentro de cada partição**
por padrão do PostgreSQL para tabelas particionadas com muitas partições — a integridade é mantida
pela aplicação/ingestão (mesma exceção documentada em `AUDIT_MODEL.md` para `logs_auditoria`); uma
FK "solta" (sem `ON DELETE`) pode ser adicionada em `MIGRATIONS.md` se o volume permitir sem
impacto de performance.

## `leituras_telemetria`

Mesmo padrão D191. EAV (D120) — uma linha por sensor por instante, nunca uma coluna por sensor.
`tipo_sensor` é catálogo fechado (Enum), nunca texto livre — evita `RPM`/`Rpm`/`Rotação` coexistindo
como valores distintos por erro de digitação/integração.

```sql
CREATE TYPE leituras_telemetria_tipo_sensor_enum AS ENUM (
    'IGNICAO', 'VELOCIDADE', 'BATERIA', 'TENSAO', 'ODOMETRO', 'HORIMETRO', 'RPM', 'TEMPERATURA',
    'COMBUSTIVEL', 'ACELERACAO', 'FRENAGEM'
    -- vocabulário extensível (D120) via ALTER TYPE ... ADD VALUE — nunca um novo valor livre
    -- digitado pela aplicação; adicionar um sensor novo é uma migration pequena e explícita,
    -- não uma string arbitrária
);

CREATE TABLE leituras_telemetria (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                   UUID NOT NULL REFERENCES tenants(id),
    veiculo_tracionador_id      UUID NOT NULL,
    equipamento_rastreamento_id UUID NOT NULL,
    posicao_veiculo_id          UUID,     -- opcional, quando o mesmo pacote trouxe posição junto
    tipo_sensor                 leituras_telemetria_tipo_sensor_enum NOT NULL,
    valor                       NUMERIC(12,4) NOT NULL,
    unidade                     TEXT NOT NULL,
    capturado_em                 TIMESTAMPTZ NOT NULL,
    recebido_em                  TIMESTAMPTZ NOT NULL,
    processado_em                 TIMESTAMPTZ NOT NULL DEFAULT now()
)
PARTITION BY RANGE (capturado_em);

CREATE TABLE leituras_telemetria_2026_01 PARTITION OF leituras_telemetria
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE INDEX idx_leituras_telemetria_veiculo_id_tipo_sensor_capturado_em
    ON leituras_telemetria (veiculo_tracionador_id, tipo_sensor, capturado_em DESC);
```

## `heartbeats`

Mesmo padrão D191 — sinal técnico (D105), não de negócio.

```sql
CREATE TABLE heartbeats (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                   UUID NOT NULL REFERENCES tenants(id),
    equipamento_rastreamento_id UUID NOT NULL REFERENCES equipamentos_rastreamento(id),
    protocolo_externo           TEXT,   -- D111 — chave de idempotência, quando o Provedor oferece
    capturado_em                 TIMESTAMPTZ,
    recebido_em                  TIMESTAMPTZ NOT NULL,
    processado_em                 TIMESTAMPTZ NOT NULL DEFAULT now()
)
PARTITION BY RANGE (recebido_em);
-- particionada por recebido_em, não capturado_em: heartbeat pode não informar captura (D124/D125,
-- ver dictionary) — única exceção ao padrão D191, documentada explicitamente aqui.

CREATE TABLE heartbeats_2026_01 PARTITION OF heartbeats
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE UNIQUE INDEX uq_heartbeats_equipamento_protocolo
    ON heartbeats (equipamento_rastreamento_id, protocolo_externo) WHERE protocolo_externo IS NOT NULL;
```

## `cercas_eletronicas`

Configuração (D122), não histórico.

```sql
CREATE TYPE cercas_eletronicas_tipo_geometria_enum AS ENUM ('CIRCULO', 'POLIGONO');

CREATE TABLE cercas_eletronicas (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),
    nome                TEXT NOT NULL,
    tipo_geometria      cercas_eletronicas_tipo_geometria_enum NOT NULL,
    centro              GEOGRAPHY(Point, 4326),        -- quando CIRCULO
    raio_metros         NUMERIC(10,2),                  -- quando CIRCULO
    poligono            GEOGRAPHY(Polygon, 4326),       -- quando POLIGONO
    cliente_id          UUID REFERENCES clientes(id),
    filial_id           UUID REFERENCES filiais(id),
    status              TEXT NOT NULL DEFAULT 'ATIVA',

    CONSTRAINT uq_cercas_eletronicas_tenant_id_nome UNIQUE (tenant_id, nome),
    CONSTRAINT ck_cercas_eletronicas_geometria CHECK (
        (tipo_geometria = 'CIRCULO' AND centro IS NOT NULL AND raio_metros IS NOT NULL)
        OR (tipo_geometria = 'POLIGONO' AND poligono IS NOT NULL)
    )
);

CREATE INDEX idx_cercas_eletronicas_centro
    ON cercas_eletronicas USING GIST (centro) WHERE centro IS NOT NULL;   -- D197
CREATE INDEX idx_cercas_eletronicas_poligono
    ON cercas_eletronicas USING GIST (poligono) WHERE poligono IS NOT NULL;   -- D197
```

## `eventos_rastreamento`

Derivado (D119) — nunca substitui a leitura bruta; volume "Alto"
([`../../information-model/HIGH_VOLUME_ENTITIES.md`](../../information-model/HIGH_VOLUME_ENTITIES.md)),
particionada por mês, mas **não** segue o padrão D191 de três timestamps — é detectada pelo sistema,
não capturada de fonte externa, então um único `data_hora` basta.

```sql
CREATE TYPE eventos_rastreamento_tipo_enum AS ENUM (
    'PARADA_DETECTADA', 'DESVIO_DE_ROTA_DETECTADO', 'EXCESSO_DE_VELOCIDADE', 'ENTROU_GEOFENCE',
    'SAIU_GEOFENCE', 'IGNICAO_LIGADA', 'IGNICAO_DESLIGADA'
);
CREATE TYPE eventos_rastreamento_severidade_enum AS ENUM ('INFORMACAO', 'ATENCAO', 'ALERTA', 'CRITICO');

CREATE TABLE eventos_rastreamento (
    id                                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                           UUID NOT NULL REFERENCES tenants(id),
    veiculo_tracionador_id              UUID NOT NULL,
    tipo                                eventos_rastreamento_tipo_enum NOT NULL,
    posicao_veiculo_id                  UUID,
    cerca_eletronica_id                 UUID REFERENCES cercas_eletronicas(id),
    configuracao_limite_velocidade_id   UUID,
    valor_detectado                     NUMERIC(12,4),
    severidade                          eventos_rastreamento_severidade_enum NOT NULL,
    data_hora                            TIMESTAMPTZ NOT NULL DEFAULT now()
)
PARTITION BY RANGE (data_hora);

CREATE TABLE eventos_rastreamento_2026_01 PARTITION OF eventos_rastreamento
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE INDEX idx_eventos_rastreamento_veiculo_id_tipo ON eventos_rastreamento (veiculo_tracionador_id, tipo, data_hora DESC);
```

## `configuracoes_limite_velocidade`

```sql
CREATE TABLE configuracoes_limite_velocidade (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id),
    categoria_veiculo_id    UUID REFERENCES categorias_veiculo(id),   -- opcional — ausente = padrão do tenant
    limite_kmh              NUMERIC(5,2) NOT NULL CHECK (limite_kmh > 0),
    status                  TEXT NOT NULL DEFAULT 'ATIVA'
);
```

## Índices — resumo

| Tabela | Índice principal |
|---|---|
| `posicoes_veiculo` | `(veiculo_tracionador_id, capturado_em DESC)` |
| `leituras_telemetria` | `(veiculo_tracionador_id, tipo_sensor, capturado_em DESC)` |
| `eventos_rastreamento` | `(veiculo_tracionador_id, tipo, data_hora DESC)` |
| `equipamentos_rastreamento` | único parcial: um `PRINCIPAL` vigente por veículo |
| `heartbeats` | único parcial: `(equipamento_rastreamento_id, protocolo_externo)` |

## Como este arquivo cresce

Concluído para o escopo deste lote. Próximo: `009-app_motorista.md`.
