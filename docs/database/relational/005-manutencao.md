# 005 — Manutenção

Traduz para SQL as 9 entidades de
[`../dictionary/004-manutencao.md`](../dictionary/004-manutencao.md) (`Checklist` adicionada depois
deste arquivo já escrito — ver Reconciliações abaixo). As 8 regras de
[`../README.md`](../README.md) já se aplicam a toda tabela.

## Reconciliações antes de desenhar (D076)

| Pedido nesta rodada | Decisão |
|---|---|
| Fornecedores Executores | Não é entidade nova — `fornecedores` (Lote 3, `002-cadastros.md`) já é genérica por design (`tipo_principal` inclui Oficina/Recapagem/Seguro/Outro); `ordens_servico.fornecedor_executor_id` referencia essa mesma tabela |
| Agenda Preventiva | Não é entidade nova — é uma consulta (mesmo princípio de D187, Timeline Universal) que cruza `planos_manutencao_preventiva` com a última `leituras_hodometro`/`leituras_telemetria` de cada veículo para calcular a próxima data/km prevista; nenhuma tabela armazena "a agenda" pronta |
| Histórico de Execução | Implementação física de `OrdemServicoStatusHistory` (D017/D018, já citado em `003-MANUTENCAO.md`) — tabela `ordens_servico_status_history` |
| Checklist de Execução | **Modelado agora** (reconciliação, ver `../../domain/004-manutencao.md`) — estava bloqueado por D101/D102 (Domain é a única fonte de entidades) até a entidade `Checklist` ser formalizada no Modelo de Domínio, o que foi feito para desbloquear `AGUARDANDO_CHECKLIST → LIBERADA` em `freight` (gap identificado nos Lotes Operação/Documentos Fiscais). `ordens_servico.origem_abertura` já reservava o valor `CHECKLIST_REPROVADO` desde a rodada anterior — nenhuma migração adicional em `ordens_servico` é necessária, só a FK lógica (sem constraint física, referência polimórfica) |
| Hodômetro na abertura/conclusão da OS | **Reconciliado** — `ordens_servico` ganha `hodometro_abertura_km`/`hodometro_conclusao_km` (ambos opcionais — nem toda abertura/conclusão tem leitura disponível no momento). Não é um dado novo de posse da OS: cada valor informado também gera uma `leituras_hodometro` real em `fleet` com `origem = 'ORDEM_SERVICO'` (`OdometerOrigin`, D033/D034 — a OS não duplica a posse da Time Series, só denormaliza o valor pontual capturado para exibição rápida). Alimenta o futuro plano de manutenção preventiva por KM (`planos_manutencao_preventiva`, ainda não construída) |
| Disponibilidade do veículo bloqueada por OS aberta | **Conectado agora** — `VehicleAvailabilityProjector.apply_service_order_opened`/`apply_service_order_closed` (`004-frota.md`, D247) já existiam como scaffolding desde a fundação de `fleet`, sem consumidor real porque `maintenance` não existia. `create_ordem_servico`/`concluir_ordem_servico`/`cancelar_ordem_servico` agora chamam esses métodos (mesmo padrão cross-module de D390/D398): OS `ABERTA` → veículo `EM_MANUTENCAO`; OS `CONCLUIDA` ou `CANCELADA` → veículo `DISPONIVEL` de volta. Nenhuma tabela nova, nenhuma migração em `fleet` |
| Centro de Custo na OS (Lote Financeiro, Parte 1) | **Reconciliado** — `ordens_servico` ganha `centro_custo_id` opcional. Habilita `OrdemServicoFechada` → Conta a Pagar automática (`006-financeiro.md`) quando presente junto com `fornecedor_executor_id`; OS sem os dois seguem fechando normalmente, só sem gerar a Conta a Pagar sozinha |

---

## `tipos_servico`

```sql
CREATE TABLE tipos_servico (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    nome            TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'ATIVO',

    CONSTRAINT uq_tipos_servico_tenant_id_nome UNIQUE (tenant_id, nome)
);
```

## `planos_manutencao_preventiva`

Os sete gatilhos (D120-style, extensível) já cabem no Enum — nenhuma alteração de schema será
necessária se um oitavo gatilho surgir, só um novo valor.

```sql
CREATE TYPE planos_manutencao_preventiva_tipo_gatilho_enum AS ENUM (
    'QUILOMETRAGEM', 'HORAS_MOTOR', 'DIAS', 'CALENDARIO', 'MOTOR', 'TELEMETRIA',
    'RECOMENDACAO_FABRICANTE'
);
CREATE TYPE planos_manutencao_preventiva_status_enum AS ENUM ('ATIVO', 'INATIVO');

CREATE TABLE planos_manutencao_preventiva (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id),
    veiculo_tracionador_id  UUID REFERENCES veiculos_tracionadores(id),   -- 1 dos 2 obrigatório
    categoria_veiculo_id    UUID REFERENCES categorias_veiculo(id),
    tipo_gatilho            planos_manutencao_preventiva_tipo_gatilho_enum NOT NULL,
    valor_intervalo         NUMERIC(10,2) NOT NULL CHECK (valor_intervalo > 0),
    tipo_servico_id         UUID NOT NULL REFERENCES tipos_servico(id),
    status                  planos_manutencao_preventiva_status_enum NOT NULL DEFAULT 'ATIVO',

    CONSTRAINT ck_planos_manutencao_preventiva_alvo
        CHECK (veiculo_tracionador_id IS NOT NULL OR categoria_veiculo_id IS NOT NULL)
);

CREATE INDEX idx_planos_manutencao_preventiva_veiculo_id
    ON planos_manutencao_preventiva (veiculo_tracionador_id) WHERE status = 'ATIVO';
```

**Agenda Preventiva** (consulta, não tabela): próxima manutenção prevista por veículo é
`valor_intervalo − (leitura_atual − leitura_no_ultimo_plano_executado)`, calculada a partir de
`leituras_hodometro`/`leituras_telemetria` (`004-frota.md`/`008-rastreamento.md`) no momento da
consulta — mesmo padrão de D187 (Timeline como view, não tabela).

## `ordens_servico`

Aggregate Root — Item de OS nunca existe sem ela (FK `NOT NULL` abaixo garante).

```sql
CREATE TYPE ordens_servico_tipo_enum AS ENUM ('PREVENTIVA', 'CORRETIVA', 'EMERGENCIAL', 'GARANTIA');
CREATE TYPE ordens_servico_origem_abertura_enum AS ENUM (
    'MANUAL', 'MANUTENCAO_PREVENTIVA_SUGERIDA', 'VIAGEM_INTERROMPIDA', 'CHECKLIST_REPROVADO',
    'SUGESTAO_IA'
    -- vocabulário extensível (D120) — CHECKLIST_REPROVADO já reservado, ver Reconciliações acima
);
CREATE TYPE ordens_servico_causa_enum AS ENUM ('DESGASTE', 'QUEBRA', 'ACIDENTE', 'MAU_USO', 'INSPECAO', 'RECALL');
CREATE TYPE ordens_servico_status_enum AS ENUM (
    'ABERTA', 'EM_DIAGNOSTICO', 'AGUARDANDO_APROVACAO', 'AGUARDANDO_PECA', 'EM_EXECUCAO',
    'CONCLUIDA', 'FECHADA', 'CANCELADA'
);

CREATE TABLE ordens_servico (
    id                              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                       UUID NOT NULL REFERENCES tenants(id),
    codigo                          TEXT NOT NULL,

    veiculo_tracionador_id          UUID NOT NULL REFERENCES veiculos_tracionadores(id),
    composicao_veicular_id          UUID REFERENCES composicoes_veiculares(id),   -- quando aplicável
    fornecedor_executor_id          UUID REFERENCES fornecedores(id),

    tipo                            ordens_servico_tipo_enum NOT NULL,
    origem_abertura                 ordens_servico_origem_abertura_enum NOT NULL DEFAULT 'MANUAL',
    descricao_problema              TEXT NOT NULL,

    causa                           ordens_servico_causa_enum,                    -- só quando tipo = CORRETIVA
    causa_raiz                      TEXT,
    diagnostico_tecnico             TEXT,
    mecanico_id                     UUID REFERENCES usuarios(id),

    -- Previsto × Realizado (D086) — nunca um "custo_total" digitável
    custo_previsto                  NUMERIC(14,2),   -- soma dos itens estimados; recalculado pela aplicação
    custo_realizado                 NUMERIC(14,2),   -- soma dos itens realizados; congela em FECHADA

    necessita_aprovacao             BOOLEAN NOT NULL DEFAULT FALSE,
    evidencia_conclusao_exigida     BOOLEAN NOT NULL DEFAULT FALSE,

    status                          ordens_servico_status_enum NOT NULL DEFAULT 'ABERTA',
    data_inicio_execucao            TIMESTAMPTZ,
    data_conclusao                  TIMESTAMPTZ,

    -- Reconciliado nesta rodada (ver Reconciliações acima) — denormalização de exibição; a leitura
    -- real e imutável vive em `leituras_hodometro` (fleet), origem = 'ORDEM_SERVICO'
    hodometro_abertura_km           NUMERIC(10,2),
    hodometro_conclusao_km          NUMERIC(10,2),

    -- Reconciliado (Lote Financeiro, Parte 1) — opcional; junto com fornecedor_executor_id, habilita
    -- a Conta a Pagar automática no fechamento (006-financeiro.md)
    centro_custo_id                 UUID REFERENCES centros_custo(id),

    criado_em                       TIMESTAMPTZ NOT NULL DEFAULT now(),
    criado_por                      UUID,
    atualizado_em                   TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_por                  UUID,
    excluido_em                     TIMESTAMPTZ,

    CONSTRAINT uq_ordens_servico_tenant_id_codigo UNIQUE (tenant_id, codigo),
    CONSTRAINT ck_ordens_servico_causa_so_corretiva CHECK (causa IS NULL OR tipo = 'CORRETIVA')
);

CREATE INDEX idx_ordens_servico_tenant_id_veiculo_id ON ordens_servico (tenant_id, veiculo_tracionador_id) WHERE excluido_em IS NULL;
CREATE INDEX idx_ordens_servico_tenant_id_status ON ordens_servico (tenant_id, status) WHERE excluido_em IS NULL;
CREATE INDEX idx_ordens_servico_data_inicio_execucao ON ordens_servico (data_inicio_execucao);
CREATE INDEX idx_ordens_servico_data_conclusao ON ordens_servico (data_conclusao);
CREATE INDEX idx_ordens_servico_fornecedor_executor_id ON ordens_servico (fornecedor_executor_id);
CREATE INDEX idx_ordens_servico_tenant_id_tipo ON ordens_servico (tenant_id, tipo);
```

`custo_previsto`/`custo_realizado` não são `GENERATED` (ao contrário de `viagens.margem_prevista`):
dependem de `SUM()` sobre `itens_ordem_servico`, uma tabela filha — PostgreSQL não permite coluna
gerada referenciar outra tabela. Recalculados pela aplicação a cada inserção/alteração de item
(trigger `AFTER INSERT/UPDATE/DELETE ON itens_ordem_servico` é uma opção válida, a confirmar em
`MIGRATIONS.md`) — em qualquer caso, **nunca um campo que o usuário digita diretamente**.

## `ordens_servico_status_history`

```sql
CREATE TABLE ordens_servico_status_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    ordem_servico_id UUID NOT NULL REFERENCES ordens_servico(id),
    status          TEXT NOT NULL,
    usuario_id      UUID,
    origem          TEXT NOT NULL,
    observacao      TEXT,   -- obrigatória (validação de aplicação) em CANCELADA/AGUARDANDO_APROVACAO
    data_hora       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_ordens_servico_status_history_os_id ON ordens_servico_status_history (ordem_servico_id, data_hora);
```

Volume "Médio" (uma OS gera bem menos transições que uma Viagem) — não particionada neste lote;
reavaliar se o volume real divergir do esperado (mesmo critério de `viagens`/`entregas`, Lote 4).

## `itens_ordem_servico`

```sql
CREATE TYPE itens_ordem_servico_categoria_custo_enum AS ENUM (
    'PECAS', 'PNEUS', 'SERVICOS', 'TERCEIROS', 'MAO_DE_OBRA_INTERNA', 'MAO_DE_OBRA_TERCEIRIZADA',
    'DESLOCAMENTO', 'OUTROS'
);

CREATE TABLE itens_ordem_servico (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),
    ordem_servico_id    UUID NOT NULL REFERENCES ordens_servico(id),
    categoria_custo     itens_ordem_servico_categoria_custo_enum NOT NULL,
    descricao           TEXT NOT NULL,
    peca_estoque_id     UUID REFERENCES pecas_estoque(id),
    quantidade          NUMERIC(10,2) NOT NULL CHECK (quantidade > 0),
    valor_unitario       NUMERIC(14,2) NOT NULL,
    valor_total          NUMERIC(14,2) GENERATED ALWAYS AS (quantidade * valor_unitario) STORED
    -- "Item de OS nunca existe sem OS": garantido por ordem_servico_id UUID NOT NULL
);

CREATE INDEX idx_itens_ordem_servico_ordem_servico_id ON itens_ordem_servico (ordem_servico_id);
```

## `aprovacoes_custo`

Preparada para workflow em níveis (`nivel`) mesmo usando apenas um nível hoje — nenhuma migração
de schema necessária quando aprovação em cascata for implementada.

```sql
CREATE TYPE aprovacoes_custo_decisao_enum AS ENUM ('APROVADO', 'REJEITADO');

CREATE TABLE aprovacoes_custo (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),
    ordem_servico_id    UUID NOT NULL REFERENCES ordens_servico(id),
    nivel               INTEGER NOT NULL DEFAULT 1,   -- preparação para workflow multi-nível futuro
    decisao             aprovacoes_custo_decisao_enum NOT NULL,
    justificativa       TEXT,
    ator_id             UUID NOT NULL REFERENCES usuarios(id),
    data_hora           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_aprovacoes_custo_ordem_servico_id ON aprovacoes_custo (ordem_servico_id, nivel);
```

## `solicitacoes_peca`

```sql
CREATE TYPE solicitacoes_peca_status_enum AS ENUM ('SOLICITADA', 'RECEBIDA', 'CANCELADA');

CREATE TABLE solicitacoes_peca (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),
    ordem_servico_id    UUID NOT NULL REFERENCES ordens_servico(id),
    fornecedor_id       UUID NOT NULL REFERENCES fornecedores(id),
    status              solicitacoes_peca_status_enum NOT NULL DEFAULT 'SOLICITADA',
    prazo_previsto      DATE
);
```

## `pecas_estoque` e `movimentacoes_estoque`

`pecas_estoque.quantidade_disponivel` é projeção (D081) — fonte de verdade é
`movimentacoes_estoque`, nunca editada diretamente.

```sql
CREATE TABLE pecas_estoque (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id),
    nome                    TEXT NOT NULL,
    quantidade_disponivel   INTEGER NOT NULL DEFAULT 0,   -- recalculada pela aplicação a cada movimentação
    estoque_minimo          INTEGER,
    custo_medio             NUMERIC(14,2)
);

CREATE TYPE movimentacoes_estoque_tipo_enum AS ENUM ('ENTRADA', 'SAIDA');

CREATE TABLE movimentacoes_estoque (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),
    peca_estoque_id     UUID NOT NULL REFERENCES pecas_estoque(id),
    tipo                movimentacoes_estoque_tipo_enum NOT NULL,
    quantidade          INTEGER NOT NULL CHECK (quantidade > 0),
    ordem_servico_id    UUID REFERENCES ordens_servico(id),
    data_hora           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_movimentacoes_estoque_peca_estoque_id ON movimentacoes_estoque (peca_estoque_id, data_hora);
```

Invariante "saída nunca gera saldo negativo" — mesma abordagem de `leituras_hodometro`: trigger ou
validação de aplicação antes do `INSERT`, não um `CHECK` de linha (precisa conhecer o saldo
acumulado).

## Integração com Frota — nunca copiar dados do veículo

`ordens_servico` referencia `veiculo_tracionador_id`/`composicao_veicular_id` por FK viva — nenhuma
coluna `placa`/`modelo` duplicada aqui. Quando a OS precisar exibir esses dados (tela, relatório), a
consulta faz `JOIN` com `veiculos_tracionadores`; se um snapshot histórico for necessário no futuro
(ex: OS muito antiga, veículo já vendido/renomeado), seguiria o mesmo padrão de
`viagens.placa_veiculo_snapshot` — não antecipado aqui porque o Data Dictionary Funcional
(`004-manutencao.md`) não define um snapshot para Ordem de Serviço; criar um agora seria inventar
estrutura fora da origem (D101/D102).

## `checklists` e `checklists_status_history`

Sem "Modelo de Checklist" configurável nesta fundação (ver domain doc, "O que não faz") — `itens`
guarda a resposta inline em JSONB, mesmo princípio de `entregas.endereco_entrega` (`003-operacao.md`)
para dado estruturado que não precisa de tabela própria ainda. `referencia_tipo`/`referencia_id` é
referência polimórfica (mesmo padrão de `anexos`/`comentarios`, `003-operacao.md`) — sem FK física,
já que aponta ora para `viagens`, ora (futuramente) para `ordens_servico`.

```sql
CREATE TYPE checklists_tipo_enum AS ENUM (
    'MOTORISTA_SAIDA', 'MOTORISTA_RETORNO', 'OFICINA', 'ADMINISTRATIVO', 'CARREGAMENTO', 'DESCARGA'
);
CREATE TYPE checklists_referencia_tipo_enum AS ENUM ('VIAGEM', 'ORDEM_SERVICO');
CREATE TYPE checklists_status_enum AS ENUM (
    'PENDENTE', 'EM_PREENCHIMENTO', 'CONCLUIDO', 'APROVADO', 'REPROVADO'
);

CREATE TABLE checklists (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                   UUID NOT NULL REFERENCES tenants(id),
    codigo                      TEXT NOT NULL,
    tipo                        checklists_tipo_enum NOT NULL,
    referencia_tipo             checklists_referencia_tipo_enum NOT NULL,
    referencia_id               UUID NOT NULL,   -- polimórfico, sem FK de banco (mesmo padrão de anexos/comentarios)
    veiculo_tracionador_id      UUID NOT NULL REFERENCES veiculos_tracionadores(id),
    motorista_id                UUID REFERENCES motoristas(id),   -- nulo para OFICINA/ADMINISTRATIVO
    itens                       JSONB NOT NULL DEFAULT '[]',   -- [{descricao, critico, resposta}]
    status                      checklists_status_enum NOT NULL DEFAULT 'PENDENTE',
    checklist_reprovado_id      UUID REFERENCES checklists(id),   -- origem, quando criado por reprovação
    criado_em                   TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em                TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_checklists_tenant_id_codigo UNIQUE (tenant_id, codigo)
);

CREATE INDEX idx_checklists_tenant_id_referencia ON checklists (tenant_id, referencia_tipo, referencia_id);
CREATE INDEX idx_checklists_tenant_id_status ON checklists (tenant_id, status);

CREATE TABLE checklists_status_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),   -- D174/D193
    checklist_id    UUID NOT NULL REFERENCES checklists(id),
    status          TEXT NOT NULL,
    usuario_id      UUID,
    origem          TEXT NOT NULL,   -- 'sistema' (avaliação automática) / usuário (preenchimento manual)
    observacao      TEXT,   -- obrigatória (aplicação) em REPROVADO
    data_hora       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_checklists_status_history_tenant_id ON checklists_status_history (tenant_id);
CREATE INDEX idx_checklists_status_history_checklist_id ON checklists_status_history (checklist_id);
```

## Constraints de integridade — resumo

| Regra de negócio | Constraint física |
|---|---|
| Item de OS nunca sem OS | `itens_ordem_servico.ordem_servico_id UUID NOT NULL` |
| Causa só para Corretiva | `ck_ordens_servico_causa_so_corretiva` |
| Custo total nunca digitável | Sem coluna `custo_total`; `custo_previsto`/`custo_realizado` recalculados pela aplicação a partir de `itens_ordem_servico` |
| Saída de estoque nunca negativa | Trigger/validação de aplicação |
| Plano Preventivo sempre tem um alvo (veículo ou categoria) | `ck_planos_manutencao_preventiva_alvo` |

## Preparação para abertura automática (sem alterar schema depois)

`ordens_servico.origem_abertura` já cobre os quatro gatilhos automáticos pedidos —
`MANUTENCAO_PREVENTIVA_SUGERIDA`, `VIAGEM_INTERROMPIDA` (pane), `CHECKLIST_REPROVADO` (reservado,
ver Reconciliações) e `SUGESTAO_IA` (já antecipando `Sugestão de IA`,
[`../dictionary/012-ia.md`](../dictionary/012-ia.md)) — todos vocabulário de um único Enum
extensível (D120-style); nenhum gatilho novo exigirá `ALTER TABLE`.

## Como este arquivo cresce

Concluído para o escopo original deste lote; `checklists`/`checklists_status_history` adicionadas
numa reconciliação posterior (ver nota no topo). Próximo: `006-financeiro.md`.
