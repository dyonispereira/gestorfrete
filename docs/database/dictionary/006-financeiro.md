# 006 — Financeiro

Atributos distintivos das 11 entidades de
[`../../domain/006-financeiro.md`](../../domain/006-financeiro.md) (ver aquele arquivo para a
reconciliação de nomes, D076, contra a lista originalmente estimada em `ENTITY_CATALOG.md`).
Atributos universais (D069), Padrões de atributo/Atributos Críticos (D077/D081) e a regra de que
indicadores agregados nunca são atributos operacionais (D090) não são repetidos aqui — ver
[`README.md`](./README.md). Máquinas de estado canônicas (Faturamento, Contas a Pagar):
[`../../flows/005-FINANCEIRO.md`](../../flows/005-FINANCEIRO.md) (D035).

## Divisão conceitual

| Divisão pedida | Onde vive |
|---|---|
| **Financeiro Operacional** (Receita Prevista/Realizada, Custos Previstos/Realizados, Margem, Resultado por viagem) | **Não neste arquivo** — já são atributos da própria `Viagem` em [`002-operacao.md`](./002-operacao.md) (D086/D098), atualizados agora nesta rodada (`CUSTO_REALIZADO`, `RECEITA_REALIZADA`, `MARGEM_PREVISTA`, `MARGEM_REALIZADA`, `DESVIO_FINANCEIRO`). Este arquivo só documenta as entidades que **alimentam** esses atributos (Conta a Receber, Rateio de Despesa) |
| **Financeiro Administrativo** (Contas a Pagar/Receber, Fluxo de Caixa, Centros de Custo, Plano de Contas, Conciliação, Forma de Pagamento) | Este arquivo — `Conta a Pagar`, `Conta a Receber`, `Rateio de Despesa`, `Conciliação Bancária`, `Lançamento de Extrato Bancário`, `Plano de Contas`, `Forma de Pagamento`, `Posição de Caixa`. **Centro de Custo** já existe em [`001-cadastros.md`](./001-cadastros.md) (D076 — não duplicado) |
| **Faturamento** (Fatura, Boleto/PIX/Cartão, Baixa, Estorno, Inadimplência) | Este arquivo — `Fatura`, `Conta a Receber` (parcelas), `Forma de Pagamento` (Boleto/PIX/Cartão são valores do Enum, não entidades próprias), `Estorno Financeiro`. "Baixa" é a transição `→ Recebida`/`→ Paga` já modelada no `STATUS` de `Conta a Receber`/`Conta a Pagar`, não um campo novo. "Inadimplência" não é um atributo — é a condição de `Conta a Receber.STATUS = Vencida` sustentada além do prazo, cujo indicador (taxa de inadimplência) é calculado em `analytics` |
| **Indicadores** (EBITDA, Rentabilidade, Resultado por placa/cliente/motorista/viagem) | **Nunca neste arquivo** (D090) — nenhum desses aparece como `Atributo` em nenhuma tabela abaixo. `Resultado por Viagem` já existe como `VIAGEM.MARGEM_REALIZADA` (é uma instância, não uma agregação — permitido, ver nota em `002-operacao.md`); `Resultado por placa/cliente/motorista`, `EBITDA` e `Rentabilidade` consolidada são cálculos de `analytics` sobre os dados brutos deste arquivo, nunca campos aqui |

---

## Fatura

Dono: `financial` · Natureza: Transactional Data · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| FATURA.VIAGEM_ID / ENTREGA_ID | Viagem ou Entrega faturada | Referência | Sim (um dos dois) | Capturado (sistema) | Não | Interno | Depende do modo de faturamento do contrato (por viagem inteira ou por entrega, [`005-FINANCEIRO.md`](../../flows/005-FINANCEIRO.md), Fluxos alternativos) |
| FATURA.CLIENTE_ID | Cliente | Referência | Sim | Capturado (sistema) | Não | Interno | FK |
| FATURA.NUMERO_FATURA | Número da fatura | Texto Curto | Sim | Capturado (sistema) | Não | Interno | Único por tenant, para sempre (D084 — nunca reaproveitado, mesmo após `Cancelada`) |
| FATURA.VALOR_TOTAL | Valor total faturado | Monetário | Sim | Capturado, no momento da emissão (transição `AGUARDANDO_FATURAMENTO → FATURADA`) | Não — imutável após emitida; correção é por Estorno Financeiro (D100) | Financeiro | D097 — valor do quê (total faturado desta Fatura), em qual moeda (BRL, D075), em qual momento (emissão). **Atributo Crítico (D077)** — ver Governança abaixo |
| FATURA.DATA_EMISSAO | Data de emissão | Data | Sim | Capturado (sistema) | Não | Interno | Granularidade: dia (D074) |
| FATURA.FORMA_PAGAMENTO_ID | Forma de pagamento combinada | Referência | Sim | Informado | Não | Interno | FK para Forma de Pagamento |
| FATURA.STATUS | Status | Enum | Sim | Calculado | Sim | Interno | Valores: `Emitida`/`Cancelada` — cancelamento gera nova Fatura, nunca reabre a anterior |

### Governança do atributo crítico `VALOR_TOTAL` (D077)

| Quem altera? | Quando muda? | Quem pode visualizar? | Quem nunca altera? |
|---|---|---|---|
| `financial` (Faturista), uma única vez, na emissão | Nunca muda depois de emitida — correção é sempre um novo Estorno Financeiro, nunca edição (D100) | Financeiro sempre; demais perfis conforme RBAC | Frontend (D027); Motorista, Gestor Operacional (apenas consultam) |

---

## Conta a Receber

Dono: `financial` · Natureza: Transactional Data · Parte do agregado Fatura.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| CONTA_RECEBER.FATURA_ID | Fatura | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| CONTA_RECEBER.NUMERO_PARCELA | Número da parcela | Inteiro | Sim | Capturado (sistema) | Não | Interno | 1 para pagamento à vista; N para parcelamento |
| CONTA_RECEBER.VALOR | Valor da parcela | Monetário | Sim | Capturado, na criação (rateio do `VALOR_TOTAL` da Fatura) | Não | Financeiro | D097 — valor desta parcela, moeda BRL (D075), no momento da emissão da Fatura. Soma de todas as parcelas de uma Fatura = `FATURA.VALOR_TOTAL` |
| CONTA_RECEBER.DATA_VENCIMENTO | Data de vencimento | Data | Sim | Calculado (prazo do contrato/Forma de Pagamento) | Não | Interno | Granularidade: dia (D074) |
| CONTA_RECEBER.DATA_RECEBIMENTO | Data de recebimento | Data/Hora | Não | Capturado (confirmação de pagamento) | Não | Interno | Granularidade: segundo (D074) |
| CONTA_RECEBER.STATUS | Status | Enum | Sim | Calculado | Sim | Interno | Valores: `Pendente`/`Vencida`/`Parcialmente Recebida`/`Recebida`/`Conciliada`. **Atributo Crítico (D077)** — mesmo tratamento de `STATUS_FINANCEIRO` em `002-operacao.md`: imutável após `Conciliada` (D100), correção por Estorno Financeiro. **Reconciliado (Lote Financeiro, Parte 2.1)**: `Parcialmente Recebida` é valor novo — baixa parcial real de uma parcela isolada |
| CONTA_RECEBER.VALOR_RECEBIDO | Valor recebido (acumulado) | Monetário | Sim | Capturado, acumulado a cada baixa | Não | Financeiro | Reconciliado (Lote Financeiro, Parte 2.1) — soma de todas as baixas (parciais ou totais) já confirmadas nesta parcela. `0 <= VALOR_RECEBIDO <= VALOR`; saldo em aberto = `VALOR - VALOR_RECEBIDO`. Default `0` na criação |
| CONTA_RECEBER.COMPETENCIA | Competência (período contábil) | Data | Sim | Informado, explícito na criação | Não | Financeiro | Reconciliado (Lote Financeiro, Parte 1) — mês/ano de referência contábil; **nunca inferido** de `DATA_VENCIMENTO`. Granularidade armazenada: dia, sempre normalizado ao primeiro dia do mês de competência |

---

## Conta a Pagar

Dono: `financial` · Natureza: Transactional Data · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| CONTA_PAGAR.FORNECEDOR_ID | Fornecedor | Referência | Sim | Informado | Não | Interno | FK — [`001-cadastros.md`](./001-cadastros.md) |
| CONTA_PAGAR.CENTRO_CUSTO_ID | Centro de Custo | Referência | Sim | Informado | Não | Interno | FK — [`001-cadastros.md`](./001-cadastros.md), D076 |
| CONTA_PAGAR.ORIGEM | Origem do lançamento | Enum | Sim | Capturado (sistema) | Não | Interno | Valores: Viagem/Ordem de Serviço/Abastecimento/Compra/Ajuste Manual (D099 — nunca "sem origem"; `Ajuste Manual` exige justificativa e auditoria reforçada) |
| CONTA_PAGAR.VIAGEM_ID / ORDEM_SERVICO_ID | Origem específica | Referência | Não | Capturado (sistema) | Não | Interno | Preenchido quando `ORIGEM` é Viagem ou Ordem de Serviço |
| CONTA_PAGAR.VALOR | Valor da despesa | Monetário | Sim | Informado (nota fiscal do fornecedor) ou Capturado (evento de origem) | Não | Financeiro | D097 — valor desta despesa, moeda BRL (D075), no momento do lançamento |
| CONTA_PAGAR.DATA_VENCIMENTO | Data de vencimento | Data | Sim | Informado | Não | Interno | Granularidade: dia (D074) |
| CONTA_PAGAR.PLANO_CONTAS_ID | Categoria contábil | Referência | Sim | Informado | Não | Interno | FK para Plano de Contas |
| CONTA_PAGAR.STATUS | Status | Enum | Sim | Calculado (transições da máquina de estados) | Sim, em `ContaPagarStatusHistory` (D017/D018) | Interno | Valores completos: `005-FINANCEIRO.md`. **Atributo Crítico (D077)** — imutável após `Conciliada` (D100) |
| CONTA_PAGAR.COMPETENCIA | Competência (período contábil) | Data | Sim | Informado, explícito na criação | Não | Financeiro | Reconciliado (Lote Financeiro, Parte 1) — mesmo princípio de `CONTA_RECEBER.COMPETENCIA`, nunca inferido de `DATA_VENCIMENTO` |
| CONTA_PAGAR.VEICULO_TRACIONADOR_ID | Veículo Tracionador | Referência | Não | Informado, ou Capturado quando a origem é Ordem de Serviço | Não | Interno | Reconciliado (Lote Financeiro, Parte 1) — FK opcional para `veiculos_tracionadores`. Dimensão direta só em Conta a Pagar (Conta a Receber deriva via Fatura → Viagem, sem duplicar) |
| CONTA_PAGAR.MOTORISTA_ID | Motorista | Referência | Não | Informado | Não | Interno | Reconciliado (Lote Financeiro, Parte 1) — FK opcional para `motoristas`. **Nunca herdado automaticamente** de `VIAGEM_ID`/da Ordem de Serviço — só preenchido quando o lançamento é atribuível ao motorista por si só (ex.: multa, reembolso) |

---

## Aprovação de Despesa

Dono: `financial` · Natureza: Transactional Data · Parte do agregado Conta a Pagar.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| APROVACAO_DESPESA.CONTA_PAGAR_ID | Conta a Pagar | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| APROVACAO_DESPESA.DECISAO | Decisão | Enum | Sim | Informado (Financeiro/Gestor) | Não (registro pontual, imutável) | Interno | Valores: Aprovado/Rejeitado — mesma estrutura de `Aprovação de Custo` ([`004-manutencao.md`](./004-manutencao.md)) |
| APROVACAO_DESPESA.JUSTIFICATIVA | Justificativa | Texto Longo | Não, obrigatório quando `Rejeitado` | Informado | Não | Interno | |
| APROVACAO_DESPESA.ATOR_ID | Ator responsável | Referência | Sim | Capturado (sistema) | Não | Interno | |
| APROVACAO_DESPESA.DATA_HORA | Data/hora da decisão | Data/Hora | Sim | Capturado (sistema) | Não | Interno | Granularidade: segundo (D074) |

> A alçada que determina se uma Conta a Pagar `NECESSITA_APROVACAO` é o mesmo parâmetro de tenant
> (`settings`) já referenciado em [`004-manutencao.md`](./004-manutencao.md) para a Ordem de
> Serviço — não duplicado aqui.

---

## Rateio de Despesa

Dono: `financial` · Natureza: Transactional Data · Parte do agregado Conta a Pagar.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| RATEIO_DESPESA.CONTA_PAGAR_ID | Conta a Pagar | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| RATEIO_DESPESA.CENTRO_CUSTO_ID / VIAGEM_ID | Alvo do rateio | Referência | Sim | Informado | Não | Interno | Um por linha — a mesma Conta a Pagar gera N linhas de Rateio |
| RATEIO_DESPESA.CRITERIO | Critério de rateio | Enum | Sim | Informado (configurado no Centro de Custo) | Não | Interno | Valores: Km rodado/Número de viagens/Peso transportado |
| RATEIO_DESPESA.VALOR_RATEADO | Valor rateado | Monetário | Sim | Calculado (proporcional ao critério) | Não | Financeiro | D097 — valor desta fração, moeda BRL (D075). Soma de todas as linhas = `CONTA_PAGAR.VALOR`. Alimenta `VIAGEM.CUSTO_REALIZADO` quando o alvo é uma Viagem ([`002-operacao.md`](./002-operacao.md)) |

---

## Lançamento de Extrato Bancário

Dono: `financial` · Natureza: Transactional Data · Histórica (D037/D083) · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| LANCAMENTO_EXTRATO.CONTA_BANCARIA_ID | Conta Bancária | Referência | Sim | Capturado (sistema) | Não | Interno | D189 — FK, imutável; gap identificado ao modelar a camada relacional |
| LANCAMENTO_EXTRATO.VALOR | Valor | Monetário | Sim | Importado (OFX/CSV do banco/gateway) | **É ele próprio o histórico** — nunca editado (D037) | Financeiro | D097 — valor do lançamento bancário, moeda BRL (D075), na data do extrato |
| LANCAMENTO_EXTRATO.DATA | Data do lançamento | Data | Sim | Importado | Não | Interno | Granularidade: dia (D074) |
| LANCAMENTO_EXTRATO.DESCRICAO_BRUTA | Descrição bruta do banco | Texto Longo | Sim | Importado | Não | Interno | Texto exatamente como veio do extrato, sem normalização |
| LANCAMENTO_EXTRATO.STATUS | Status | Enum | Sim | Calculado | Não | Interno | Valores: `Não Conciliado`/`Conciliado` |

## Conciliação Bancária

Dono: `financial` · Natureza: Transactional Data · Histórica (D037/D083) · Parte do agregado Conta
a Pagar ou Conta a Receber (nunca ambos).

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| CONCILIACAO_BANCARIA.LANCAMENTO_EXTRATO_ID | Lançamento de Extrato Bancário | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável; usado no máximo uma vez |
| CONCILIACAO_BANCARIA.CONTA_PAGAR_ID / CONTA_RECEBER_ID | Lançamento conciliado | Referência | Sim (um dos dois) | Capturado (sistema) | Não | Interno | Exatamente um dos dois, nunca ambos |
| CONCILIACAO_BANCARIA.DIVERGENCIA | Houve divergência? | Booleano | Sim | Calculado (comparação de valores) | Não | Interno | Quando `Sim`, gera Comentário obrigatório (D023) explicando a divergência |
| CONCILIACAO_BANCARIA.DATA_HORA | Data/hora da conciliação | Data/Hora | Sim | Capturado (sistema) | Não | Interno | Granularidade: segundo (D074). A partir daqui, D100 — o lançamento conciliado é imutável |

---

## Estorno Financeiro

Dono: `financial` · Natureza: Transactional Data · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| ESTORNO_FINANCEIRO.FATURA_ID / CONTA_PAGAR_ID / CONTA_RECEBER_ID | Lançamento original | Referência | Sim (exatamente um) | Capturado (sistema) | Não | Interno | D099 — todo Estorno tem origem explícita |
| ESTORNO_FINANCEIRO.VALOR | Valor estornado | Monetário | Sim | Informado | Não | Financeiro | D097 — valor estornado, moeda BRL (D075), no momento do estorno. Nunca excede o valor original |
| ESTORNO_FINANCEIRO.MOTIVO | Motivo | Texto Longo | Sim | Informado | Não | Interno | Obrigatório (D007) |
| ESTORNO_FINANCEIRO.DATA_HORA | Data/hora | Data/Hora | Sim | Capturado (sistema) | Não | Interno | Granularidade: segundo (D074) |

---

## Forma de Pagamento

Dono: `financial` · Natureza: Reference Data (D036) · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| FORMA_PAGAMENTO.NOME | Nome | Texto Curto | Sim | Informado | Não | Interno | Único por tenant. Valores típicos: PIX/Boleto/Cartão/Transferência/Dinheiro — não um Enum fechado no código, é um cadastro, para permitir que o tenant adicione formas novas sem alteração de sistema |
| FORMA_PAGAMENTO.STATUS | Status | Enum | Sim | Informado | Não | Interno | Valores: `Ativa`/`Inativa` |

## Plano de Contas

Dono: `financial` · Natureza: Reference Data (D036) · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| PLANO_CONTAS.CODIGO_CONTABIL | Código contábil | Texto Curto | Sim | Informado | Não | Interno | Único por tenant |
| PLANO_CONTAS.NOME | Nome | Texto Curto | Sim | Informado | Não | Interno | Ex: Combustível, Manutenção, Pedágio, Administrativo |
| PLANO_CONTAS.TIPO | Tipo | Enum | Sim | Informado | Não | Interno | D184 — Valores: `Receita`/`Despesa`. Reconcilia o que a modelagem relacional chamou de "Categoria Financeira" — mesma entidade, não duplicada |
| PLANO_CONTAS.CATEGORIA_PAI_ID | Categoria pai | Referência | Não | Informado | Não | Interno | D184 — auto-referência opcional; hierarquia de categorias contábeis. Sem ciclos (uma categoria nunca é ancestral dela mesma) |
| PLANO_CONTAS.STATUS | Status | Enum | Sim | Informado | Não | Interno | Valores: `Ativo`/`Inativo` |

## Posição de Caixa

Dono: `financial` · Natureza: Read Model (projeção, D081) — nunca a fonte de verdade de nenhuma
Conta a Pagar/Receber individual.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| POSICAO_CAIXA.DATA_REFERENCIA | Data de referência | Data | Sim | Capturado (sistema) | Não | Interno | Granularidade: dia (D074) — a projeção é sempre "a partir desta data" |
| POSICAO_CAIXA.SALDO_PROJETADO | Saldo projetado | Monetário | Sim | Derivado (D081 — soma de Contas a Receber pendentes menos Contas a Pagar pendentes, por data) | Não — projeção, sempre recalculada | Financeiro | D097 — saldo projetado, moeda BRL (D075), a partir de `DATA_REFERENCIA`. **Não é o Fluxo de Caixa/DRE consolidado de `analytics` (D090)** — é uma leitura rápida operacional do dia a dia do Financeiro |
| POSICAO_CAIXA.ATUALIZADO_EM | Última recomputação | Data/Hora | Sim | Capturado (sistema) | Não | Interno | Granularidade: segundo (D074) |

## Conta Bancária (D189 — nova, identificada ao modelar a camada relacional)

Dono: `financial` · Natureza: Reference Data (D036) · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| CONTA_BANCARIA.BANCO | Banco | Texto Curto | Sim | Informado | Não | Interno | |
| CONTA_BANCARIA.AGENCIA | Agência | Texto Curto | Sim | Informado | Não | Interno | |
| CONTA_BANCARIA.NUMERO_CONTA | Número da conta | Texto Curto | Sim | Informado | Não | Confidencial | Único por tenant |
| CONTA_BANCARIA.TIPO | Tipo | Enum | Sim | Informado | Não | Interno | Valores: `Corrente`/`Poupança` |
| CONTA_BANCARIA.STATUS | Status | Enum | Sim | Informado | Não | Interno | Valores: `Ativa`/`Inativa` |

## Como este documento cresce

Mesmo princípio de todo o dicionário: um arquivo `NNN-categoria.md` por vez, na ordem do roadmap
(ver [`README.md`](./README.md)). Próximo: `007-fiscal.md`.
