# 005 — Financeiro

## Objetivo

Documentar o ciclo financeiro completo do GestorFrete — da Cotação ao BI — incluindo Contas a
Pagar, Rateios, Centro de Custo, Conciliação, PIX e Boletos, e a separação entre **valores
previstos e realizados** que sustenta o cálculo de margem real de cada viagem (não apenas margem
estimada). Este documento é a referência canônica do Status Financeiro introduzido em
[`002-VIAGEM.md`](./002-VIAGEM.md) (D020) e da convergência que define `ENCERRADA` (D019).

## Pré-condições

- Tabela de Preço vigente.
- Centro de Custo cadastrado (ao menos um, por veículo/filial).
- Conta bancária ou gateway de recebimento configurado (PIX/boleto).

## Gatilho inicial

Uma Cotação é criada a partir de uma Solicitação de Viagem (ver
[`002-VIAGEM.md`](./002-VIAGEM.md)), **ou** uma Despesa é lançada independentemente de viagem
(Contas a Pagar administrativas, ex: aluguel de pátio).

## Máquina de Estados — Faturamento

Estas são as mesmas quatro estados já introduzidos como Status Financeiro em
[`002-VIAGEM.md`](./002-VIAGEM.md) (D020) — este documento é a referência canônica e completa;
`002-VIAGEM.md` não redefine, apenas resume (ver [`INDEX.md`](./INDEX.md), Convenções).

### Estados

`AGUARDANDO_FATURAMENTO`, `FATURADA`, `AGUARDANDO_RECEBIMENTO`, `RECEBIDA`.

```
AGUARDANDO_FATURAMENTO → FATURADA → AGUARDANDO_RECEBIMENTO → RECEBIDA
```

### Transições válidas

| De | Para | Gatilho |
|---|---|---|
| `AGUARDANDO_FATURAMENTO` | `FATURADA` | Canhoto(s) registrado(s) e CT-e emitido |
| `FATURADA` | `AGUARDANDO_RECEBIMENTO` | Cobrança enviada ao cliente (PIX/boleto/outro) |
| `AGUARDANDO_RECEBIMENTO` | `RECEBIDA` | Pagamento do cliente confirmado (conciliado) |

### Transições inválidas (normativas)

- **Não é permitido** faturar sem ao menos um Canhoto registrado.
- **Não é permitido** pular `AGUARDANDO_RECEBIMENTO` e ir direto de `FATURADA` para `RECEBIDA` — o
  recebimento é sempre um evento próprio, nunca implícito.
- **Não é permitido** marcar `RECEBIDA` sem conciliação bancária correspondente (ver Máquina de
  Estados — Contas a Pagar/Receber, Conciliação, abaixo).

**Reconciliado (Lote Financeiro, Parte 2.1)**: dentro de `AGUARDANDO_RECEBIMENTO`, cada Conta a
Receber (parcela) individual ganhou um sub-estado `PARCIALMENTE_RECEBIDO` (baixa parcial real de
uma única parcela — `docs/domain/006-financeiro.md`) — isso não altera esta máquina de estados da
Viagem: `AGUARDANDO_RECEBIMENTO → RECEBIDA` só acontece quando **todas** as parcelas da Fatura
estão com saldo zerado, nunca no meio de uma baixa parcial de qualquer parcela individual.

## Máquina de Estados — Contas a Pagar

### Estados

`LANCADA`, `AGUARDANDO_APROVACAO`, `APROVADA`, `PAGA`, `CONCILIADA`, `REJEITADA`.

```
LANCADA ──(valor acima da alçada)──► AGUARDANDO_APROVACAO ──(aprovado)──► APROVADA → PAGA → CONCILIADA
   │                                        │
   │(valor dentro da alçada)                └──(rejeitado)──► REJEITADA
   └─────────────────────────────────────► APROVADA
```

### Transições válidas

| De | Para | Gatilho |
|---|---|---|
| `LANCADA` | `AGUARDANDO_APROVACAO` | Valor da despesa excede a alçada do lançador |
| `LANCADA` | `APROVADA` | Valor dentro da alçada — aprovação automática |
| `AGUARDANDO_APROVACAO` | `APROVADA` | Gestor/Financeiro aprova |
| `AGUARDANDO_APROVACAO` | `REJEITADA` | Gestor/Financeiro rejeita, com motivo obrigatório |
| `APROVADA` | `PAGA` | Pagamento efetuado (PIX/boleto/transferência) |
| `PAGA` | `CONCILIADA` | Extrato bancário confere com o pagamento registrado |

### Transições inválidas (normativas)

- **Não é permitido** pagar (`→ PAGA`) uma despesa `LANCADA` sem passar por `APROVADA` — mesmo
  despesas de baixo valor têm aprovação automática registrada, nunca implícita.
- **Não é permitido** conciliar (`→ CONCILIADA`) sem um `PAGA` correspondente.
- **Não é permitido** reabrir uma despesa `REJEITADA` — uma nova despesa é lançada, referenciando a
  anterior.

## Histórico de Transições

Por D017/D018, ambas as máquinas acima (Faturamento e Contas a Pagar) geram histórico append-only:
`FaturamentoStatusHistory` e `ContaPagarStatusHistory`, ambas com `id`, `entidade_id`, `status`,
`usuario`, `origem`, `data_hora`, `observacao` (obrigatória em `REJEITADA`).

## Receita e Custo: Previsto vs. Realizado

Decisão central deste documento: toda viagem carrega **dois pares de valores**, nunca um único
valor "atual" que se sobrescreve.

| Conceito | Quando é apurado | Fonte |
|---|---|---|
| **Receita Prevista** | Na Aprovação da Cotação | Tabela de Preço / Contrato de Frete |
| **Receita Realizada** | Quando o Status Financeiro atinge `RECEBIDA` | Valor efetivamente recebido (pode divergir da Receita Prevista por desconto, multa, etc.) |
| **Custo Previsto** | Na Programação da viagem | Estimativa de combustível, pedágio, motorista, manutenção rateada |
| **Custo Realizado** | Acumulado conforme a viagem executa | Soma de Abastecimentos (ver [`006-ABASTECIMENTO.md`](./006-ABASTECIMENTO.md)), pedágios, Ordens de Serviço rateadas, Adiantamento/Haver |

A partir desses quatro valores:

- **Margem Prevista** = Receita Prevista − Custo Previsto (calculada na Programação, antes da
  execução).
- **Margem Realizada** = Receita Realizada − Custo Realizado — **só é definitiva quando a Viagem
  atinge `ENCERRADA`** (D019): antes disso, Custo Realizado e Receita Realizada ainda podem mudar.
- **Desvio Financeiro** = Margem Realizada − Margem Prevista (absoluto e percentual).

Nenhum desses quatro valores é sobrescrito — cada atualização de Custo Realizado (ex: novo
abastecimento registrado) insere um novo valor acumulado, preservando o valor anterior no histórico
(mesmo princípio de D018 aplicado a valores monetários, não apenas a status).

## Rateio

Custos não diretamente atribuíveis a uma única viagem (ex: manutenção preventiva agendada por
quilometragem do veículo, não por viagem específica; despesa administrativa de um Centro de Custo
compartilhado) são distribuídos proporcionalmente entre as viagens do período — o critério de rateio
(por km rodado, por número de viagens, por peso transportado) é configurável por Centro de Custo.

## Conciliação

Processo de conferência entre o extrato bancário (PIX, boleto, transferência) e os registros de
Contas a Pagar (`PAGA → CONCILIADA`) e Contas a Receber (`AGUARDANDO_RECEBIMENTO → RECEBIDA`).
Discrepâncias geram Ocorrência financeira para investigação manual.

## Fluxo principal

1. **Cotação** `[nenhum status financeiro ainda]` — valor calculado a partir da Tabela de Preço.
2. **Aprovada** — Receita Prevista fixada.
3. **Programada** — Custo Previsto calculado; Margem Prevista disponível para o Comercial/Gestor.
4. **Executada** — Custo Realizado acumula conforme Abastecimentos, pedágios e outras despesas da
   viagem são registrados.
5. **Faturada** `[Status Financeiro: AGUARDANDO_FATURAMENTO → FATURADA]`.
6. **Recebida** `[Status Financeiro: AGUARDANDO_RECEBIMENTO → RECEBIDA]` — Receita Realizada fixada.
7. **Encerrada** `[Viagem atinge ENCERRADA — D019]` — Margem Realizada e Desvio Financeiro
   calculados de forma definitiva.
8. **BI** — indicadores de rentabilidade, ciclo financeiro e inadimplência alimentados.

Em paralelo, independente de viagem: **Contas a Pagar** seguem sua própria máquina de estados
(despesas administrativas, compras de peça — ver [`003-MANUTENCAO.md`](./003-MANUTENCAO.md) —, e
demais custos rateados).

## Fluxos alternativos

- **Faturamento por entrega individual** (não pela viagem inteira): quando o contrato comercial
  define faturamento por entrega concluída em viagens multi-drop, cada Entrega gera seu próprio
  ciclo `AGUARDANDO_FATURAMENTO → ... → RECEBIDA`, e a convergência para `ENCERRADA` da Viagem
  exige que todos os sub-ciclos estejam `RECEBIDA`.
- **Antecipação de recebível**: cliente ou transportadora antecipa o recebimento via instituição
  financeira — `RECEBIDA` é atingida antes do prazo comercial original, com custo de antecipação
  lançado como despesa.

## Fluxos de exceção

- **Inadimplência**: cliente não paga dentro do prazo — a viagem permanece indefinidamente em
  `AGUARDANDO_RECEBIMENTO`, gerando alerta e, após prazo configurável, Ocorrência de cobrança; a
  Viagem correspondente nunca atinge `ENCERRADA` enquanto isso persistir (consequência direta de
  D019 — este é o comportamento correto, não um bug: viagem não paga não deveria parecer encerrada).
- **CT-e cancelado após faturamento**: reabre a necessidade de reemissão fiscal (ver
  [`009-FISCAL.md`](./009-FISCAL.md)) — o Faturamento já emitido é estornado e um novo ciclo se
  inicia.
- **Divergência na conciliação**: valor recebido diferente do faturado (desconto não combinado,
  taxa de gateway) — gera Ocorrência financeira; `RECEBIDA` só é confirmada após a divergência ser
  tratada (baixa parcial, renegociação, etc.).

## Eventos publicados

| Evento | Gerado quando |
|---|---|
| `FaturamentoGerado` | Transição `AGUARDANDO_FATURAMENTO → FATURADA` — já catalogado em [`../product/EVENT_MAP.md`](../product/EVENT_MAP.md) |
| `RecebimentoConfirmado` | Transição `AGUARDANDO_RECEBIMENTO → RECEBIDA` — já catalogado |
| `ContaAPagarRegistrada` | Despesa lançada — já catalogado |
| `ContaAReceberRegistrada` | Valor a receber lançado — já catalogado |
| `ContaAPagarAprovada` | Transição para `APROVADA` (novo) |
| `ContaAPagarRejeitada` | Transição para `REJEITADA` (novo) |
| `ContaAPagarConciliada` | Transição para `CONCILIADA` (novo) |
| `CustoRealizadoAtualizado` | Novo custo acumulado a uma viagem (novo) |
| `MargemCalculada` | Margem Prevista ou Realizada recalculada (novo) |

## Eventos consumidos

| Evento | Publicado por | Efeito |
|---|---|---|
| `CanhotoRegistrado` | `documents` | Habilita transição para `FATURADA` |
| `CTeEmitido` | `documents` | Condição para faturamento |
| `OrdemServicoFechada` | `maintenance` | Custo rateado incorporado ao Custo Realizado da(s) viagem(ns) |
| `AbastecimentoRegistrado` | `freight`/`fleet` (ver [`006-ABASTECIMENTO.md`](./006-ABASTECIMENTO.md)) | Custo incorporado ao Custo Realizado |

## Permissões

| Etapa | Quem executa |
|---|---|
| Cotação, aprovação comercial | Comercial |
| Lançamento de despesa | Qualquer perfil operacional autorizado (Almoxarife, Analista de Frota) |
| Aprovação de despesa acima da alçada | Financeiro |
| Faturamento, recebimento, conciliação | Financeiro, Faturista |
| Consulta somente leitura | Auditor |

## Auditoria

Toda transição das duas máquinas de estado, e toda atualização de Custo/Receita Previsto ou
Realizado, é registrada em `audit` (D007).

## Notificações

- Financeiro: despesa aguardando aprovação, divergência de conciliação.
- Gestor Operacional: viagem com margem realizada abaixo da prevista (desvio negativo).
- Cliente: fatura emitida, lembrete de vencimento.

## Capacidades Transversais

1. **Timeline Universal** (D022): `FaturamentoStatusHistory` + `ContaPagarStatusHistory` +
   histórico de atualizações de Custo/Receita Previsto e Realizado, integrados à Timeline Universal
   da Viagem (ver [`002-VIAGEM.md`](./002-VIAGEM.md)).
2. **Comentários** (D023): aplicável — Financeiro registra contexto de negociação/desconto;
   visibilidade interna.
3. **Anexos** (D024): comprovante de pagamento, boleto, nota fiscal de despesa, extrato conciliado.
4. **Favoritos** (D025): filtros como "contas a receber vencendo esta semana", "viagens com desvio
   financeiro negativo".
5. **Pesquisa Global** (D026): número da fatura, nome do cliente/fornecedor, número da viagem.

## Regras de negócio relacionadas

- D001 — soft delete em todas as entidades financeiras.
- D007 — auditoria obrigatória.
- D015/D016/D017/D018 — máquinas de estado com histórico append-only.
- D019/D020 — Faturamento é uma das três dimensões que convergem para `ENCERRADA`.
- D022–D026 — capacidades transversais aplicadas na seção acima.

## SLA

| Etapa | Prazo |
|---|---|
| Faturamento após canhoto + CT-e | A definir por política comercial |
| Recebimento após faturamento | Conforme prazo de pagamento do contrato |
| Aprovação de despesa acima da alçada | A definir |
| Conciliação após pagamento | Até 48 horas |

## Indicadores Gerados

- Receita Prevista vs. Realizada (desvio)
- Custo Previsto vs. Realizado (desvio)
- Margem Prevista, Margem Realizada, Desvio Financeiro — por viagem, cliente, veículo, período
- Prazo médio de recebimento
- Inadimplência por cliente
- Fluxo de Caixa e DRE consolidados

## Riscos

- Inadimplência prolongada mantendo viagens indefinidamente fora de `ENCERRADA`.
- Divergência de conciliação não tratada a tempo.
- Custo Realizado subestimado por atraso no registro de Abastecimento/pedágio.
- Rateio configurado incorretamente distorcendo a margem por viagem.

## KPIs impactados

- Ciclo financeiro médio da viagem (ver [`002-VIAGEM.md`](./002-VIAGEM.md)).
- Margem real da operação (não apenas prevista).
- Inadimplência.
- Capital de giro necessário (função do prazo médio de recebimento vs. pagamento).

## Critérios de encerramento

- Não há "encerramento" próprio deste fluxo — ele é contínuo por natureza (Contas a Pagar/Receber
  fluem permanentemente). O encerramento relevante é o de cada Viagem individual (`ENCERRADA`,
  D019) e o fechamento periódico de Fluxo de Caixa/DRE (mensal, por convenção contábil).

## Pontos de integração

- `freight` (Status Financeiro da Viagem), `documents` (CT-e/Canhoto como gatilho de faturamento),
  `maintenance` (custos de OS rateados), `drivers` (adiantamento/haver).
- Gateway de pagamento (PIX, boleto) — fora do escopo eletrônico desta fundação.
- Conta bancária para conciliação — integração futura (Open Finance ou extrato manual).

## Requisitos futuros

- Integração Open Finance para conciliação automática.
- IA sinalizando risco de inadimplência antes do vencimento (ver
  [`../product/VISION.md`](../product/VISION.md), capítulo 24).
- Integração com GestorContábil para lançamentos contábeis automáticos (ver
  [`../product/VISION.md`](../product/VISION.md), capítulo 20).
