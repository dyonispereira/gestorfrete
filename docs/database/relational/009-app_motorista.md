# 009 — App (Motorista)

Traduz para SQL as 5 entidades de
[`../dictionary/009-app_motorista.md`](../dictionary/009-app_motorista.md). As 8 regras de
[`../README.md`](../README.md) já se aplicam a toda tabela. Lote mais simples que os anteriores, como
esperado — a maior parte da complexidade já foi resolvida no Domain/Dictionary (Sprint 08).

## `sessoes_mobile`

Separada nas quatro preocupações já estabelecidas no dicionário — **nunca guarda RBAC** (autorização
é sempre resolvida ao vivo, D060) e **nunca representa identidade** (D140, só `motorista_id`
referencia quem é a pessoa).

```sql
CREATE TYPE sessoes_mobile_metodo_autenticacao_enum AS ENUM ('CPF_VEICULO', 'BIOMETRIA', 'PIN');
CREATE TYPE sessoes_mobile_motivo_encerramento_enum AS ENUM ('LOGOUT', 'REVOGACAO_ADMINISTRATIVA', 'TROCA_DE_DISPOSITIVO');
CREATE TYPE sessoes_mobile_status_enum AS ENUM ('ATIVA', 'EXPIRADA', 'ENCERRADA');

CREATE TABLE sessoes_mobile (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                   UUID NOT NULL REFERENCES tenants(id),

    -- Autenticação
    motorista_id                UUID NOT NULL REFERENCES motoristas(id),
    veiculo_tracionador_id      UUID NOT NULL REFERENCES veiculos_tracionadores(id),
    dispositivo_mobile_id        UUID NOT NULL REFERENCES dispositivos_mobile(id),
    metodo_autenticacao          sessoes_mobile_metodo_autenticacao_enum NOT NULL,
    token_acesso_hash            TEXT NOT NULL,

    -- Autorização: deliberadamente ausente — nunca cacheada aqui (D060)

    -- Expiração
    data_hora_inicio              TIMESTAMPTZ NOT NULL DEFAULT now(),
    data_hora_expiracao_prevista  TIMESTAMPTZ NOT NULL,

    -- Revogação
    data_hora_encerramento        TIMESTAMPTZ,
    motivo_encerramento           sessoes_mobile_motivo_encerramento_enum,
    revogado_por                  UUID REFERENCES usuarios(id),

    status                        sessoes_mobile_status_enum NOT NULL DEFAULT 'ATIVA'
);

CREATE INDEX idx_sessoes_mobile_motorista_id_status ON sessoes_mobile (motorista_id, status);
```

Revogar uma Sessão **nunca** bloqueia o Dispositivo (D132) — `motivo_encerramento =
'REVOGACAO_ADMINISTRATIVA'` afeta só esta linha; `dispositivos_mobile.status` é independente.

## `dispositivos_mobile`

Identificação, configuração e estado separados em grupos de colunas explícitos — nunca misturados
com dado de sessão (que é transiente; o dispositivo é persistente).

```sql
CREATE TYPE dispositivos_mobile_sistema_operacional_enum AS ENUM ('ANDROID', 'IOS');
CREATE TYPE dispositivos_mobile_status_enum AS ENUM ('ATIVO', 'INATIVO', 'REVOGADO');

CREATE TABLE dispositivos_mobile (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                   UUID NOT NULL REFERENCES tenants(id),
    motorista_id                UUID NOT NULL REFERENCES motoristas(id),

    -- Identificação
    identificador_dispositivo    TEXT NOT NULL,

    -- Configuração
    sistema_operacional          dispositivos_mobile_sistema_operacional_enum NOT NULL,
    versao_so                    TEXT,
    versao_app                   TEXT NOT NULL,
    token_push                   TEXT,

    -- Estado
    status                       dispositivos_mobile_status_enum NOT NULL DEFAULT 'ATIVO',
    ultimo_acesso_em              TIMESTAMPTZ,   -- D081 projeção, atualizada a cada nova sessão

    CONSTRAINT uq_dispositivos_mobile_identificador UNIQUE (identificador_dispositivo)
);
```

`token_push` nunca dispara alteração de estado sozinho (D134) — é só o destino de envio; nenhuma
lógica de aplicação pode tratar "recebi um push" como gatilho de mudança de dado.

## `filas_sincronizacao`

A tabela mais crítica deste lote — idempotência, reprocessamento, conflito, payload original e
rastreabilidade, todos como colunas próprias, nunca inferidos.

```sql
CREATE TYPE filas_sincronizacao_status_enum AS ENUM ('PENDENTE', 'ENVIANDO', 'PROCESSADA', 'FALHOU', 'CONFLITO');

CREATE TABLE filas_sincronizacao (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                   UUID NOT NULL REFERENCES tenants(id),
    sessao_mobile_id             UUID NOT NULL REFERENCES sessoes_mobile(id),

    -- Rastreabilidade / ordem (D136)
    sequencia_local               INTEGER NOT NULL,

    -- O comando em si (D137 — sempre atômico) e seu alvo
    tipo_comando                  TEXT NOT NULL,   -- vocabulário extensível (D120)
    entidade_destino_tipo         TEXT NOT NULL,
    entidade_destino_id           UUID NOT NULL,
    payload                       JSONB NOT NULL,   -- preservado integralmente, nunca sobrescrito (D139)

    -- Idempotência (D111/D138) por constraint, não só por código
    identificador_local_unico     TEXT NOT NULL,

    -- Reprocessamento
    numero_tentativa              INTEGER NOT NULL DEFAULT 1,
    status                        filas_sincronizacao_status_enum NOT NULL DEFAULT 'PENDENTE',

    -- Resolução de conflito (D131/D139) — sempre um campo adicional, nunca sobrescreve payload
    resolucao_conflito            TEXT,

    criado_em                     TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_filas_sincronizacao_identificador_local UNIQUE (sessao_mobile_id, identificador_local_unico),
    CONSTRAINT uq_filas_sincronizacao_sessao_sequencia UNIQUE (sessao_mobile_id, sequencia_local)
);

CREATE INDEX idx_filas_sincronizacao_status ON filas_sincronizacao (tenant_id, status) WHERE status IN ('PENDENTE', 'FALHOU', 'CONFLITO');
CREATE INDEX idx_filas_sincronizacao_entidade_destino ON filas_sincronizacao (entidade_destino_tipo, entidade_destino_id);
```

Notas de design, uma por preocupação pedida:

- **Idempotência**: `uq_filas_sincronizacao_identificador_local` é a garantia física — reenviar o
  mesmo comando (rede instável, retry automático) nunca cria uma segunda linha; o backend faz
  `INSERT ... ON CONFLICT (sessao_mobile_id, identificador_local_unico) DO NOTHING` (ou equivalente).
- **Reprocessamento**: `numero_tentativa` incrementado a cada nova tentativa da mesma linha
  (`UPDATE`, não `INSERT` — o comando já existe, só sua execução é retentada).
- **Resolução de conflito**: `resolucao_conflito` é preenchido **sem apagar `payload`** — ambos os
  lados (o que foi pedido, o que foi decidido) coexistem na mesma linha (D139), nunca um substitui o
  outro.
- **Preservação do payload original**: `payload JSONB NOT NULL`, nunca `UPDATE`d após criado — só
  `status`/`numero_tentativa`/`resolucao_conflito` mudam.
- **Rastreabilidade**: `sequencia_local` + `uq_filas_sincronizacao_sessao_sequencia` garante a ordem
  de execução exata em que o dispositivo gerou os comandos (D136) — o backend processa em ordem de
  `sequencia_local`, nunca por ordem de chegada na rede.

## `registros_sincronizacao`

Nível de lote (D135) — início, fim, quantidade de comandos, sucesso, falhas, tempo.

```sql
CREATE TABLE registros_sincronizacao (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id),
    sessao_mobile_id         UUID NOT NULL REFERENCES sessoes_mobile(id),
    data_hora_inicio          TIMESTAMPTZ NOT NULL,
    data_hora_fim             TIMESTAMPTZ NOT NULL,
    duracao_ms                INTEGER GENERATED ALWAYS AS (
                                   EXTRACT(EPOCH FROM (data_hora_fim - data_hora_inicio)) * 1000
                               ) STORED,
    quantidade_comandos       INTEGER NOT NULL,
    quantidade_sucesso        INTEGER NOT NULL,
    quantidade_falha          INTEGER NOT NULL
);

CREATE INDEX idx_registros_sincronizacao_sessao_mobile_id ON registros_sincronizacao (sessao_mobile_id);
```

`duracao_ms` é `GENERATED` (mesmo critério consolidado no Lote 8: depende só de duas colunas da
própria linha, não de agregação entre tabelas).

## `assinaturas_digitais`

```sql
CREATE TYPE assinaturas_digitais_documento_tipo_enum AS ENUM ('CANHOTO');   -- extensível: CHECKLIST, etc.
CREATE TYPE assinaturas_digitais_papel_signatario_enum AS ENUM ('MOTORISTA', 'CLIENTE', 'RECEBEDOR');

CREATE TABLE assinaturas_digitais (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                   UUID NOT NULL REFERENCES tenants(id),
    documento_tipo               assinaturas_digitais_documento_tipo_enum NOT NULL,
    documento_id                 UUID NOT NULL,   -- polimórfico, sem FK (mesmo padrão de anexos)
    papel_signatario              assinaturas_digitais_papel_signatario_enum NOT NULL,
    nome_signatario_informado     TEXT,   -- obrigatório (aplicação) quando papel = RECEBEDOR sem cadastro
    arquivo_id                    UUID NOT NULL,   -- D107
    capturado_em                  TIMESTAMPTZ NOT NULL,
    recebido_em                   TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_assinaturas_digitais_documento ON assinaturas_digitais (documento_tipo, documento_id);
```

## Constraints de integridade — resumo

| Regra de negócio | Constraint física |
|---|---|
| Comando de sincronização nunca duplicado (D111) | `uq_filas_sincronizacao_identificador_local` |
| Ordem de execução preservada (D136) | `sequencia_local` + `uq_filas_sincronizacao_sessao_sequencia` |
| Payload original nunca sobrescrito (D139) | `resolucao_conflito` é coluna adicional, não substitui `payload` |
| Sessão nunca cacheia RBAC (D060) | Ausência deliberada de coluna de permissões |
| Revogar sessão nunca bloqueia dispositivo (D132) | Tabelas independentes, sem `ON DELETE`/trigger cruzado |

## Como este arquivo cresce

Concluído para o escopo deste lote. Próximo: `010-administracao.md`.
