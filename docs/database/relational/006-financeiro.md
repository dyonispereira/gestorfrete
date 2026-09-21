# 006 — Financeiro

Traduz para SQL as 12 entidades de
[`../dictionary/006-financeiro.md`](../dictionary/006-financeiro.md) (11 originais + `Conta
Bancária`, D189). As 8 regras de [`../README.md`](../README.md) já se aplicam a toda tabela.

## Separação Operacional × Administrativo (pedido explícito)

| | Onde vive | Dono |
|---|---|---|
| **Financeiro Operacional** (Receita/Custo Previsto/Realizado, Margem) | Colunas da própria `viagens` (`003-operacao.md`, Lote 4) — nunca duplicado aqui | `freight` |
| **Financeiro Administrativo** (Contas a Pagar/Receber, Caixa, Banco, Pagamentos, Recebimentos) | Este arquivo | `financial` |

A Viagem continua dona da operação; o Financeiro continua dono do dinheiro — nenhuma tabela deste
lote guarda receita/custo/margem de viagem, e nenhuma coluna de `viagens` guarda saldo bancário.

## Reconciliações antes de desenhar (D076)

| Sugerido nesta rodada | Decisão |
|---|---|
| `lancamentos_financeiros` (genérico) | Não criado — `faturas`, `contas_pagar`, `contas_receber` já são entidades próprias e específicas (D033/D034); um "lançamento" genérico duplicaria as três |
| `parcelas_financeiras` | É `contas_receber` — já modelada como uma linha por parcela (`numero_parcela`) desde `006-financeiro.md` |
| `recebimentos` / `pagamentos` | São as transições para `RECEBIDA`/`PAGA` dentro de `contas_receber_status_history`/`contas_pagar_status_history` (criadas abaixo, mesmo padrão de `ordens_servico_status_history`) — não uma tabela de "recebimento" separada da conta que ele quita |
| `adiantamentos_motorista`, `haveres_motorista` | **Não modelados** (D190) — nunca foram formalizados como entidade em nenhuma categoria do Domain, mesmo já citados como pertencentes a `drivers` desde a reconciliação original de `006-financeiro.md`. Fora do escopo de um lote financeiro; registrado para retomar quando `drivers`/Cadastros for revisitado |
| `movimentacoes_caixa` | Não modelada — `Posição de Caixa` já deriva diretamente de `contas_pagar`/`contas_receber` pendentes (ver definição na entidade), sem um livro-caixa intermediário; nada no Data Dictionary Funcional prevê um caixa físico/petty cash separado |
| `centros_resultado` | Não modelado — `Centro de Custo` (`001-cadastros.md`) já cumpre esse papel hoje; nenhuma entidade distinta de "Centro de Resultado" existe em nenhuma categoria do Domain (D101/D102 — não criada aqui só por conveniência) |
| `contas_bancarias` | **Confirmado como gap real** (D189) — corrigido na origem antes deste arquivo (ver `../domain/006-financeiro.md`) |
| `posicoes_caixa` ("caso seja materializada futuramente") | Já é uma entidade própria desde `006-financeiro.md` (Sprint 08) — modelada abaixo, não é "futura" |
| `competencia` em `contas_pagar`/`contas_receber` (Lote Financeiro, Parte 1) | **Reconciliado** — não existia em nenhuma camada; adicionada agora como campo `DATE NOT NULL` explícito em ambas, nunca inferido de `data_vencimento`/`data_emissao`. Fundação para DRE/fluxo de caixa gerencial (`analytics`, D090), sem duplicar o indicador aqui |
| `veiculo_tracionador_id`/`motorista_id` em `contas_pagar` (Lote Financeiro, Parte 1) | **Reconciliado, só em Contas a Pagar** — Conta a Receber nasce de Fatura → Viagem, então veículo/motorista já são deriváveis sem duplicar a dimensão; Conta a Pagar frequentemente nasce solta (combustível, pedágio, manutenção), sem Viagem para derivar de |

---

## `formas_pagamento`

```sql
CREATE TABLE formas_pagamento (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    nome            TEXT NOT NULL,   -- PIX/Boleto/Cartão/Transferência/Dinheiro — cadastro, não Enum fechado
    status          TEXT NOT NULL DEFAULT 'ATIVA',

    CONSTRAINT uq_formas_pagamento_tenant_id_nome UNIQUE (tenant_id, nome)
);
```

## `plano_contas`

Já enriquecido com `tipo`/`categoria_pai_id` (D184) — reconcilia o que teria sido pedido como
"Categoria Financeira".

```sql
CREATE TYPE plano_contas_tipo_enum AS ENUM ('RECEITA', 'DESPESA');

CREATE TABLE plano_contas (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),
    codigo_contabil     TEXT NOT NULL,
    nome                TEXT NOT NULL,
    tipo                plano_contas_tipo_enum NOT NULL,
    categoria_pai_id    UUID REFERENCES plano_contas(id),
    status              TEXT NOT NULL DEFAULT 'ATIVO',

    CONSTRAINT uq_plano_contas_tenant_id_codigo UNIQUE (tenant_id, codigo_contabil)
);

CREATE INDEX idx_plano_contas_categoria_pai_id ON plano_contas (categoria_pai_id);
```

"Categoria não pode ser pai dela mesma" (nem de um ancestral) — sem ciclo expressável em `CHECK`
simples (precisaria recursão); validado por trigger `BEFORE INSERT/UPDATE` percorrendo
`categoria_pai_id` até a raiz, ou na aplicação — detalhe de implementação em `MIGRATIONS.md`.

## `contas_bancarias` (D189)

```sql
CREATE TYPE contas_bancarias_tipo_enum AS ENUM ('CORRENTE', 'POUPANCA');

CREATE TABLE contas_bancarias (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    banco           TEXT NOT NULL,
    agencia         TEXT NOT NULL,
    numero_conta    TEXT NOT NULL,
    tipo            contas_bancarias_tipo_enum NOT NULL,
    status          TEXT NOT NULL DEFAULT 'ATIVA',

    CONSTRAINT uq_contas_bancarias_tenant_id_numero UNIQUE (tenant_id, numero_conta)
);
```

## `faturas`

```sql
CREATE TYPE faturas_status_enum AS ENUM ('EMITIDA', 'CANCELADA');

CREATE TABLE faturas (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id),
    numero_fatura           TEXT NOT NULL,
    viagem_id               UUID REFERENCES viagens(id),
    entrega_id              UUID REFERENCES entregas(id),   -- 1 dos 2 obrigatório (faturamento por viagem OU por entrega)
    cliente_id              UUID NOT NULL REFERENCES clientes(id),
    valor_total             NUMERIC(14,2) NOT NULL,
    data_emissao            DATE NOT NULL,
    forma_pagamento_id      UUID NOT NULL REFERENCES formas_pagamento(id),
    status                  faturas_status_enum NOT NULL DEFAULT 'EMITIDA',
    criado_em               TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_faturas_tenant_id_numero UNIQUE (tenant_id, numero_fatura),
    CONSTRAINT ck_faturas_origem CHECK (viagem_id IS NOT NULL OR entrega_id IS NOT NULL)
    -- valor_total imutável após emitida (D100): reforçado na aplicação, correção via Estorno Financeiro
);

CREATE INDEX idx_faturas_tenant_id_cliente_id ON faturas (tenant_id, cliente_id);
```

## `contas_receber` e `contas_receber_status_history`

```sql
CREATE TYPE contas_receber_status_enum AS ENUM ('PENDENTE', 'VENCIDA', 'RECEBIDA', 'CONCILIADA');

CREATE TABLE contas_receber (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),
    fatura_id           UUID NOT NULL REFERENCES faturas(id),
    numero_parcela      INTEGER NOT NULL,
    valor               NUMERIC(14,2) NOT NULL,
    data_vencimento     DATE NOT NULL,
    data_recebimento    TIMESTAMPTZ,
    status              contas_receber_status_enum NOT NULL DEFAULT 'PENDENTE',
    competencia         DATE NOT NULL,   -- Reconciliado (Lote Financeiro, Parte 1) — explícito, nunca inferido de data_vencimento

    CONSTRAINT uq_contas_receber_fatura_id_parcela UNIQUE (fatura_id, numero_parcela)
    -- imutável após CONCILIADA (D100): reforçado na aplicação
);

CREATE TABLE contas_receber_status_history (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),   -- D174/D193
    conta_receber_id    UUID NOT NULL REFERENCES contas_receber(id),
    status              TEXT NOT NULL,
    usuario_id          UUID,
    data_hora           TIMESTAMPTZ NOT NULL DEFAULT now()
    -- transição para 'RECEBIDA' AQUI é o "recebimento" pedido — não uma tabela própria
);

CREATE INDEX idx_contas_receber_status_history_tenant_id ON contas_receber_status_history (tenant_id);
CREATE INDEX idx_contas_receber_tenant_id_status ON contas_receber (tenant_id, status);
CREATE INDEX idx_contas_receber_data_vencimento ON contas_receber (data_vencimento) WHERE status IN ('PENDENTE', 'VENCIDA');
```

## `contas_pagar`, `contas_pagar_status_history`, `aprovacoes_despesa`, `rateios_despesa`

```sql
CREATE TYPE contas_pagar_origem_enum AS ENUM ('VIAGEM', 'ORDEM_SERVICO', 'ABASTECIMENTO', 'COMPRA', 'AJUSTE_MANUAL');
CREATE TYPE contas_pagar_status_enum AS ENUM ('LANCADA', 'AGUARDANDO_APROVACAO', 'APROVADA', 'PAGA', 'CONCILIADA', 'REJEITADA');

CREATE TABLE contas_pagar (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),
    fornecedor_id       UUID NOT NULL REFERENCES fornecedores(id),
    centro_custo_id     UUID NOT NULL REFERENCES centros_custo(id),
    origem              contas_pagar_origem_enum NOT NULL,
    viagem_id           UUID REFERENCES viagens(id),
    ordem_servico_id    UUID REFERENCES ordens_servico(id),
    veiculo_tracionador_id  UUID REFERENCES veiculos_tracionadores(id),   -- Reconciliado (Lote Financeiro, Parte 1) — dimensão direta, opcional
    motorista_id        UUID REFERENCES motoristas(id),                  -- Reconciliado — opcional, nunca herdado automaticamente da Viagem
    valor               NUMERIC(14,2) NOT NULL,
    data_vencimento     DATE NOT NULL,
    competencia         DATE NOT NULL,   -- Reconciliado — explícito, nunca inferido de data_vencimento
    plano_contas_id     UUID NOT NULL REFERENCES plano_contas(id),
    status              contas_pagar_status_enum NOT NULL DEFAULT 'LANCADA',
    criado_em           TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ck_contas_pagar_origem_especifica
        CHECK (origem NOT IN ('VIAGEM', 'ORDEM_SERVICO')
               OR (origem = 'VIAGEM' AND viagem_id IS NOT NULL)
               OR (origem = 'ORDEM_SERVICO' AND ordem_servico_id IS NOT NULL))
    -- "todo lançamento tem origem explícita" (D099): garantido pelo enum NOT NULL + este CHECK
);

CREATE TABLE contas_pagar_status_history (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),   -- D174/D193
    conta_pagar_id      UUID NOT NULL REFERENCES contas_pagar(id),
    status              TEXT NOT NULL,
    usuario_id          UUID,
    observacao          TEXT,   -- obrigatória (aplicação) em REJEITADA
    data_hora           TIMESTAMPTZ NOT NULL DEFAULT now()
    -- transição para 'PAGA' AQUI é o "pagamento" pedido — não uma tabela própria
);

CREATE TABLE aprovacoes_despesa (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),   -- D174/D193
    conta_pagar_id      UUID NOT NULL REFERENCES contas_pagar(id),
    decisao             TEXT NOT NULL,   -- 'APROVADO'/'REJEITADO'
    justificativa       TEXT,
    ator_id             UUID NOT NULL REFERENCES usuarios(id),
    data_hora           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE rateios_despesa (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),   -- D174/D193
    conta_pagar_id      UUID NOT NULL REFERENCES contas_pagar(id),
    centro_custo_id     UUID REFERENCES centros_custo(id),
    viagem_id           UUID REFERENCES viagens(id),
    criterio            TEXT NOT NULL,   -- 'KM_RODADO'/'NUMERO_VIAGENS'/'PESO_TRANSPORTADO'
    valor_rateado       NUMERIC(14,2) NOT NULL,

    CONSTRAINT ck_rateios_despesa_alvo CHECK (centro_custo_id IS NOT NULL OR viagem_id IS NOT NULL)
);

CREATE INDEX idx_contas_pagar_tenant_id_status ON contas_pagar (tenant_id, status);
CREATE INDEX idx_contas_pagar_fornecedor_id ON contas_pagar (fornecedor_id);
CREATE INDEX idx_contas_pagar_status_history_tenant_id ON contas_pagar_status_history (tenant_id);
CREATE INDEX idx_aprovacoes_despesa_tenant_id ON aprovacoes_despesa (tenant_id);
CREATE INDEX idx_rateios_despesa_tenant_id ON rateios_despesa (tenant_id);
CREATE INDEX idx_rateios_despesa_conta_pagar_id ON rateios_despesa (conta_pagar_id);
```

`rateios_despesa.viagem_id`, quando preenchido, é a via física pela qual `viagens.custo_realizado`
(Financeiro Operacional, `003-operacao.md`) é alimentado — a aplicação soma os rateios desta tabela
e escreve o resultado em `viagens.custo_realizado`; `rateios_despesa` continua pertencendo a
`financial`, `viagens.custo_realizado` continua pertencendo a `freight` (D033/D034 preservado mesmo
com o dado fluindo entre os dois).

## `lancamentos_extrato_bancario` e `conciliacoes_bancarias`

```sql
CREATE TABLE lancamentos_extrato_bancario (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),
    conta_bancaria_id   UUID NOT NULL REFERENCES contas_bancarias(id),   -- D189
    valor               NUMERIC(14,2) NOT NULL,
    data                DATE NOT NULL,
    descricao_bruta     TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'NAO_CONCILIADO'
);

CREATE TABLE conciliacoes_bancarias (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                   UUID NOT NULL REFERENCES tenants(id),
    lancamento_extrato_id       UUID NOT NULL REFERENCES lancamentos_extrato_bancario(id),
    conta_pagar_id              UUID REFERENCES contas_pagar(id),
    conta_receber_id            UUID REFERENCES contas_receber(id),
    divergencia                 BOOLEAN NOT NULL DEFAULT FALSE,
    data_hora                   TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_conciliacoes_bancarias_lancamento_extrato_id UNIQUE (lancamento_extrato_id),
    CONSTRAINT ck_conciliacoes_bancarias_alvo_exclusivo
        CHECK ((conta_pagar_id IS NOT NULL)::int + (conta_receber_id IS NOT NULL)::int = 1)
);
```

## `estornos_financeiros`

```sql
CREATE TABLE estornos_financeiros (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),
    fatura_id           UUID REFERENCES faturas(id),
    conta_pagar_id      UUID REFERENCES contas_pagar(id),
    conta_receber_id    UUID REFERENCES contas_receber(id),
    valor               NUMERIC(14,2) NOT NULL,
    motivo              TEXT NOT NULL,
    data_hora           TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ck_estornos_financeiros_alvo_exclusivo
        CHECK ((fatura_id IS NOT NULL)::int + (conta_pagar_id IS NOT NULL)::int
               + (conta_receber_id IS NOT NULL)::int = 1)
);
```

## `posicoes_caixa`

Read model (D081) — nunca fonte de verdade; sem `criado_por` (só processo automático escreve).

```sql
CREATE TABLE posicoes_caixa (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),
    data_referencia     DATE NOT NULL,
    saldo_projetado     NUMERIC(14,2) NOT NULL,
    atualizado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_posicoes_caixa_tenant_id_data UNIQUE (tenant_id, data_referencia)
);
```

Nunca confundir com Fluxo de Caixa/DRE consolidado (D090) — esta tabela é só a leitura rápida
operacional do Financeiro, derivada de `contas_pagar`/`contas_receber` pendentes; qualquer indicador
estatístico/consolidado real vive em `analytics` (`011-bi.md`), fora deste lote.

## Constraints de integridade — resumo

| Regra de negócio | Constraint física |
|---|---|
| Todo lançamento tem origem explícita (D099) | `contas_pagar.origem NOT NULL` + `ck_contas_pagar_origem_especifica` |
| Fatura imutável após emitida (D100) | Reforçado na aplicação — correção via `estornos_financeiros` |
| Conta a Receber/Pagar imutável após Conciliada (D100) | Idem |
| Conciliação aponta para exatamente um alvo | `ck_conciliacoes_bancarias_alvo_exclusivo` |
| Estorno aponta para exatamente um lançamento original | `ck_estornos_financeiros_alvo_exclusivo` |
| Categoria contábil sem ciclo (D184) | Trigger/validação de aplicação |

## Como este arquivo cresce

Concluído para o escopo deste lote. Próximo: `007-fiscal.md`.
