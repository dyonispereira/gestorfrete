# 006 — Financeiro

Entidades do ciclo financeiro administrativo do GestorFrete (Faturamento, Contas a Pagar/Receber,
Conciliação Bancária) — distintas do **Financeiro Operacional** (Receita/Custo Previsto/Realizado,
Margem), que já vive como atributo da própria Viagem em
[`002-operacao.md`](./002-operacao.md) (D019/D020, D086). Template completo de 22 campos (ver
[`README.md`](./README.md)). Máquinas de estado canônicas (Faturamento e Contas a Pagar):
[`../flows/005-FINANCEIRO.md`](../flows/005-FINANCEIRO.md) (D035).

**Nota de reconciliação (D076)**: `Centro de Custo` já existe em
[`001-cadastros.md`](./001-cadastros.md), com bounded context proprietário `financial` desde o
início — não é recriado aqui. As entidades abaixo o referenciam, mas o cadastro em si permanece
único (D033/D034).

**Gap identificado ao modelar a camada relacional (D189)**: `Lançamento de Extrato Bancário` nunca
teve uma FK para qual conta bancária o extrato pertence — um tenant pode ter mais de uma conta.
Corrigido aqui, antes de `relational/006-financeiro.md` (D103): nova entidade **Conta Bancária**,
abaixo. Total: **12 entidades** (11 originais + Conta Bancária), não as 12 originalmente estimadas
no índice de `README.md` por outro motivo (mesma disciplina de não inflar contagem já seguida em
`ENTITY_CATALOG.md`/`RBAC_MATRIX.md` — a coincidência numérica com a estimativa original é isso
mesmo, uma coincidência, não uma correção ao valor estimado).

**Reconciliado (Lote Financeiro, Parte 1)**: duas lacunas reais identificadas antes de implementar
— **Competência** (período contábil) não existia em nenhuma camada; agora é campo explícito em
Conta a Pagar e Conta a Receber (nunca inferido de `DATA_VENCIMENTO`/`DATA_EMISSAO` — fundação para
DRE, fluxo de caixa gerencial e fechamento mensal, ainda que esses indicadores em si continuem
vivendo em `analytics`, D090). E Conta a Pagar ganha **Veículo Tracionador**/**Motorista** como
dimensão direta e opcional — decisão deliberadamente assimétrica: Conta a Receber nasce de Fatura →
Viagem, então veículo/motorista já são deriváveis via Viagem sem duplicar a dimensão; Conta a Pagar
frequentemente nasce solta (combustível, pedágio, manutenção sem viagem associada), onde não há
Viagem alguma para derivar de. `MOTORISTA_ID` nunca é herdado automaticamente de uma Viagem
associada — só é preenchido quando o próprio lançamento é atribuível ao motorista (ex.: multa,
reembolso), nunca por inferência.

---

## Fatura

- **Objetivo**: Representa o documento de cobrança emitido ao Cliente para uma Viagem (ou conjunto
  de Entregas, no fluxo alternativo de faturamento por entrega) — o artefato concreto criado na
  transição `AGUARDANDO_FATURAMENTO → FATURADA` do Status Financeiro da Viagem.
- **Responsabilidades**: Guardar valor faturado, data de emissão, forma de pagamento combinada;
  originar uma ou mais Contas a Receber (parcelamento).
- **O que não faz**: Não é o mesmo que o Status Financeiro da Viagem (esse é o ciclo macro, já
  modelado em `002-operacao.md`) — é o documento concreto emitido dentro desse ciclo; não substitui
  o CT-e (documento fiscal, `documents`).
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `financial`
- **Principais relacionamentos**: Viagem ou Entrega (referenciada, N:1 — depende do modo de
  faturamento do contrato); Cliente (referenciado); Forma de Pagamento (referenciada); Conta a
  Receber (1:N, filhas do agregado).
- **Eventos que publica**: `FaturamentoGerado` (já catalogado em
  [`../product/EVENT_MAP.md`](../product/EVENT_MAP.md)).
- **Eventos que consome**: `CanhotoRegistrado`, `CTeEmitido` (`documents`/`freight`) — condições que
  habilitam a emissão.
- **Invariantes**: uma Fatura só é emitida com ao menos um Canhoto registrado e o CT-e
  correspondente emitido; valor faturado maior que zero.
- **Regras de negócio associadas**: D019/D020 (Status Financeiro da Viagem), D097 (todo valor
  monetário indica do quê, em qual moeda e em qual momento), D098 (Receita Prevista não é
  substituída pela Fatura — coexistem).
- **Estados**: `Emitida` / `Cancelada` (cancelamento gera nova Fatura, nunca reabre a anterior —
  mesmo princípio de imutabilidade pós-terminal já usado em Cotação).
- **Auditoria**: D007.
- **Linha do tempo**: parte da Timeline Universal da Viagem (D022).
- **Anexos suportados**: PDF da fatura, comprovante de envio ao cliente (D024).
- **Comentários suportados**: Sim, negociação de prazo/desconto (D023).
- **KPIs relacionados**: prazo médio entre emissão e recebimento (o indicador em si vive em
  `analytics`, D090 — aqui só o dado bruto).
- **Documentos canônicos relacionados**: `005-FINANCEIRO.md`.
- **Evoluções futuras previstas**: emissão eletrônica direta ao gateway de cobrança (PIX/boleto
  automatizado).
- **Dependências obrigatórias**: Viagem (ou Entrega), Cliente, Forma de Pagamento.
- **Dependências proibidas**: Ordem de Serviço, Pneu, CT-e (referenciado apenas por evento, nunca
  lido diretamente — D008).
- **Dono da Timeline**: Aggregate Viagem (a Fatura contribui à timeline da Viagem, não tem timeline
  própria isolada).
- **Capacidade Offline**: Não (D039) — emissão exige conectividade e integração com gateway.

## Conta a Receber

- **Objetivo**: Representa uma parcela a receber de uma Fatura — suporta parcelamento (uma Fatura
  pode gerar N Contas a Receber).
- **Responsabilidades**: Rastrear vencimento, valor, status de recebimento de cada parcela
  individualmente.
- **O que não faz**: Não é a Fatura em si — várias Contas a Receber podem pertencer à mesma Fatura.
- **Aggregate Root**: Não — parte do agregado Fatura.
- **Bounded Context proprietário**: `financial`
- **Principais relacionamentos**: Fatura (N:1); Conciliação Bancária (0..1, quando `Recebida`).
- **Eventos que publica**: `ContaAReceberRegistrada`, `RecebimentoConfirmado` (já catalogados).
- **Eventos que consome**: Nenhum.
- **Invariantes**: soma das parcelas de uma Fatura é igual ao valor total faturado; uma Conta a
  Receber `Conciliada` nunca é editada diretamente (D100) — correção é por Estorno Financeiro.
  **Reconciliado (Lote Financeiro, Parte 2.1)**: `0 < valor da baixa <= saldo em aberto`
  (`VALOR - VALOR_RECEBIDO`) em toda chamada de baixa — nunca um valor negativo, zero, ou maior que
  o saldo restante.
- **Regras de negócio associadas**: D019/D020, D098 (Receita Realizada, quando `Recebida`, coexiste
  com a Receita Prevista da Viagem — nunca a substitui no histórico), D100. **Reconciliado**:
  `COMPETENCIA` (período contábil, mês/ano) é campo explícito, informado na criação — nunca
  inferido de `DATA_VENCIMENTO`. Veículo/Motorista **não** são dimensão direta aqui — deriváveis via
  Fatura → Viagem, sem duplicar (ver nota de reconciliação no topo deste arquivo).
- **Estados**: `Pendente` / `Vencida` / `Parcialmente Recebida` / `Recebida` / `Conciliada` — reflete
  as mesmas transições de `AGUARDANDO_RECEBIMENTO → RECEBIDA` descritas em `005-FINANCEIRO.md`, no
  nível de cada parcela. **Reconciliado (Lote Financeiro, Parte 2.1)**: `Parcialmente Recebida` é
  um estado novo, não documentado até aqui — o desenho original tratava "recebimento parcial"
  como resolvido inteiramente pelo parcelamento (N Contas a Receber por Fatura, cada uma binária:
  recebida ou não). Isso deixava de cobrir o caso real de uma ÚNICA parcela ser paga em partes
  (ex.: cliente paga R$ 4.000 de uma parcela de R$ 10.000 e promete o restante depois) — gap
  identificado a partir de uso real do Faturamento, não antecipado no desenho original. `Parcialmente
  Recebida` nunca é rebaixada para `Vencida` mesmo com `DATA_VENCIMENTO` passada — já existe
  progresso real registrado (`VALOR_RECEBIDO > 0`), e "vencida" esconderia isso. `Conciliada` só é
  alcançável a partir de `Recebida` (saldo zerado) — uma parcela parcialmente recebida nunca concilia
  parcialmente, mesmo tratamento de imutabilidade/D100 já aplicado ao resto do ciclo. Decisão de V1,
  revisitável se o negócio precisar de conciliação bancária parcial no futuro.
- **Auditoria**: D007.
- **Linha do tempo**: parte da Fatura/Viagem.
- **Anexos suportados**: comprovante de recebimento (D024).
- **Comentários suportados**: Sim, negociação de atraso (D023).
- **KPIs relacionados**: inadimplência (calculada em `analytics`, D090).
- **Documentos canônicos relacionados**: `005-FINANCEIRO.md`.
- **Evoluções futuras previstas**: antecipação de recebível via instituição financeira (já
  antecipado em `005-FINANCEIRO.md`, Fluxos alternativos).
- **Dependências obrigatórias**: Fatura.
- **Dependências proibidas**: Ordem de Serviço, Pneu, Cliente (diretamente — acessa via Fatura).
- **Dono da Timeline**: Aggregate Viagem (via Fatura).
- **Capacidade Offline**: Não.

## Conta a Pagar

- **Objetivo**: Representa uma despesa lançada — vinculada a uma Viagem/Ordem de Serviço (custo
  rateado) ou administrativa (independente de viagem, ex: aluguel de pátio).
- **Responsabilidades**: Orquestrar aprovação (quando acima da alçada), pagamento e conciliação —
  máquina de estados canônica em `005-FINANCEIRO.md` (D035).
- **O que não faz**: Não decide sozinha a alçada de aprovação — parâmetro de `settings`, mesma
  observação já registrada em [`004-manutencao.md`](../database/dictionary/004-manutencao.md) para
  a Ordem de Serviço.
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `financial`
- **Principais relacionamentos**: Fornecedor (referenciado); Centro de Custo (referenciado,
  [`001-cadastros.md`](./001-cadastros.md)); Viagem/Ordem de Serviço (referenciados, quando
  aplicável); Veículo Tracionador/Motorista (referenciados, quando aplicável — **Reconciliado**,
  dimensão direta e opcional, ver nota no topo deste arquivo); Aprovação de Despesa, Rateio de
  Despesa (filhos do agregado).
- **Eventos que publica**: `ContaAPagarRegistrada`, `ContaAPagarAprovada`, `ContaAPagarRejeitada`,
  `ContaAPagarConciliada` (já catalogados).
- **Eventos que consome**: `OrdemServicoFechada` (`maintenance`), `AbastecimentoRegistrado`
  (`freight`/`fleet`) — geram Conta a Pagar automaticamente quando o custo se torna devido.
  **Conectado (Lote Financeiro, Parte 1)**: `OrdemServicoFechada` — só quando a OS fechada tem
  Fornecedor Executor **e** Centro de Custo preenchidos (ambos NOT NULL nesta tabela); OS 100% mão
  de obra interna, sem Fornecedor, não gera Conta a Pagar automática — não é uma "conta a pagar" no
  sentido literal (não há título a pagar a ninguém), fica fora desta automação por decisão, não por
  limitação. Idempotente: a mesma OS nunca gera duas Contas a Pagar, mesmo se `FECHADA` for
  reprocessada. `AbastecimentoRegistrado` segue sem consumidor (fora de escopo desta Parte).
  **Decisão de Competência (V1, revisitável)**: a Conta a Pagar automática usa o mês em que a OS foi
  fechada como `COMPETENCIA` — regra objetiva e auditável (o custo é consolidado exatamente nesse
  momento), mas é uma decisão de V1, não uma verdade contábil universal. Cenários futuros podem
  exigir competência diferente da data de fechamento (ex.: serviço prestado num mês, nota fiscal
  emitida no seguinte) — quando isso for pedido, a Conta a Pagar automática precisa aceitar uma
  competência explícita vinda da própria OS (ainda não modelada), em vez de sempre inferir do
  fechamento.
- **Invariantes**: uma Conta a Pagar `Rejeitada` nunca é reaberta — nova Conta a Pagar é lançada,
  referenciando a anterior; toda Conta a Pagar tem origem explícita (D099). **Reconciliado**:
  `COMPETENCIA` é campo explícito, informado na criação — nunca inferido de `DATA_VENCIMENTO`.
  `MOTORISTA_ID` nunca é herdado automaticamente da Viagem associada, mesmo quando `VIAGEM_ID` está
  preenchido — só setado quando o lançamento é atribuível ao motorista por si só.
- **Regras de negócio associadas**: D001, D007, D099 (origem obrigatória), D100 (imutável após
  `Conciliada`).
- **Estados**: `LANCADA` / `AGUARDANDO_APROVACAO` / `APROVADA` / `PAGA` / `CONCILIADA` /
  `REJEITADA` — completo em `005-FINANCEIRO.md`.
- **Auditoria**: D007.
- **Linha do tempo (Timeline Universal)**: própria, quando administrativa; funde-se à da Viagem/OS
  quando originada de uma delas.
- **Anexos suportados**: nota fiscal do fornecedor, comprovante de pagamento (D024).
- **Comentários suportados**: Sim (D023).
- **KPIs relacionados**: custo administrativo por Centro de Custo.
- **Documentos canônicos relacionados**: `005-FINANCEIRO.md`.
- **Evoluções futuras previstas**: integração Open Finance para pagamento automatizado.
- **Dependências obrigatórias**: Fornecedor, Centro de Custo.
- **Dependências proibidas**: Cliente, CT-e.
- **Dono da Timeline**: Aggregate Conta a Pagar (este próprio) ou Viagem/Ordem de Serviço, quando
  originada de uma delas (D022, agregação por referência).
- **Capacidade Offline**: Não.

## Aprovação de Despesa

- **Objetivo**: Registro formal da decisão de um Gestor/Financeiro sobre uma Conta a Pagar acima da
  alçada — mesmo papel que Aprovação de Custo cumpre para a Ordem de Serviço
  ([`004-manutencao.md`](./004-manutencao.md)).
- **Responsabilidades**: Guardar decisão (aprovado/rejeitado), justificativa, ator.
- **O que não faz**: Não substitui a transição de estado da Conta a Pagar — é o registro que a
  acompanha.
- **Aggregate Root**: Não — parte do agregado Conta a Pagar.
- **Bounded Context proprietário**: `financial`
- **Principais relacionamentos**: Conta a Pagar (N:1).
- **Eventos que publica**: Nenhum diretamente — já coberto por `ContaAPagarAprovada`/
  `ContaAPagarRejeitada`.
- **Eventos que consome**: Nenhum.
- **Invariantes**: toda Aprovação de Despesa pertence a exatamente uma Conta a Pagar; decisão
  explícita, nunca implícita (D010).
- **Regras de negócio associadas**: D007, D010.
- **Estados**: Não aplicável — registro pontual.
- **Auditoria**: D007.
- **Linha do tempo**: parte da Conta a Pagar.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Sim, justificativa (D023).
- **KPIs relacionados**: tempo médio de aprovação.
- **Documentos canônicos relacionados**: `005-FINANCEIRO.md`.
- **Evoluções futuras previstas**: alçada configurável por tenant/perfil (mesma evolução já prevista
  para Aprovação de Custo).
- **Dependências obrigatórias**: Conta a Pagar.
- **Dependências proibidas**: Cliente, CT-e, Viagem (diretamente — acessa via Conta a Pagar).
- **Dono da Timeline**: Aggregate Conta a Pagar.
- **Capacidade Offline**: Não.

## Rateio de Despesa

- **Objetivo**: Distribui uma Conta a Pagar não diretamente atribuível a uma única Viagem entre
  múltiplos Centros de Custo/Viagens, proporcionalmente a um critério configurável.
- **Responsabilidades**: Guardar o critério (km rodado, número de viagens, peso transportado) e o
  valor resultante por Centro de Custo/Viagem.
- **O que não faz**: Não decide o critério sozinho — é configurado no Centro de Custo
  ([`001-cadastros.md`](./001-cadastros.md)).
- **Aggregate Root**: Não — parte do agregado Conta a Pagar.
- **Bounded Context proprietário**: `financial`
- **Principais relacionamentos**: Conta a Pagar (N:1); Centro de Custo, Viagem (referenciados, N:N).
- **Eventos que publica**: `CustoRealizadoAtualizado` (já catalogado — quando o rateio impacta o
  Custo Realizado de uma Viagem).
- **Eventos que consome**: Nenhum.
- **Invariantes**: soma dos valores rateados é igual ao valor total da Conta a Pagar.
- **Regras de negócio associadas**: D005/D006.
- **Estados**: Não aplicável.
- **Auditoria**: D007.
- **Linha do tempo**: parte da Conta a Pagar.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: `005-FINANCEIRO.md`.
- **Evoluções futuras previstas**: sugestão de critério de rateio por IA.
- **Dependências obrigatórias**: Conta a Pagar.
- **Dependências proibidas**: Cliente, CT-e.
- **Dono da Timeline**: Aggregate Conta a Pagar.
- **Capacidade Offline**: Não.

## Lançamento de Extrato Bancário

- **Objetivo**: Registro histórico (D037) de cada linha importada do extrato bancário (PIX, boleto,
  transferência) — a matéria-prima da Conciliação Bancária.
- **Responsabilidades**: Guardar valor, data, descrição bruta, origem (banco/gateway).
- **O que não faz**: Não decide sozinho a que Conta a Pagar/Receber corresponde — isso é a
  Conciliação Bancária.
- **Aggregate Root**: Sim — entidade **Histórica** (D037), mas com identidade própria (não é filha
  de Conta a Pagar/Receber, porque pode não ter correspondência ainda no momento da importação).
- **Bounded Context proprietário**: `financial`
- **Principais relacionamentos**: Conta Bancária (N:1, D189 — nova, ver abaixo); Conciliação
  Bancária (0..1, quando já conciliado).
- **Eventos que publica**: `ExtratoBancarioImportado` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: nunca editado após importado — apenas inserido (D037); duplicidade de importação
  é um risco a mitigar (mesma linha de extrato importada duas vezes), não uma invariante em si.
- **Regras de negócio associadas**: D017/D018/D037.
- **Estados**: `Não Conciliado` / `Conciliado`.
- **Auditoria**: D007.
- **Linha do tempo**: própria, referenciada pela Conta a Pagar/Receber quando conciliado.
- **Anexos suportados**: arquivo OFX/CSV original importado (D024).
- **Comentários suportados**: Não crítico, mas suportado, para registrar divergência (D023).
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: `005-FINANCEIRO.md`.
- **Evoluções futuras previstas**: integração Open Finance, eliminando a importação manual de
  OFX/CSV.
- **Dependências obrigatórias**: Nenhuma.
- **Dependências proibidas**: Cliente, CT-e, Viagem (diretamente — a ligação é via Conciliação
  Bancária).
- **Dono da Timeline**: Aggregate Lançamento de Extrato Bancário (este próprio).
- **Capacidade Offline**: Não.

## Conciliação Bancária

- **Objetivo**: Registro histórico (D037) do vínculo entre um Lançamento de Extrato Bancário e uma
  Conta a Pagar (`PAGA → CONCILIADA`) ou Conta a Receber (`Recebida → Conciliada`).
- **Responsabilidades**: Formalizar a conferência; registrar divergência quando o valor não bate
  exatamente.
- **O que não faz**: Não decide sozinha — é sempre uma ação humana confirmada (Financeiro), mesmo
  quando sugerida automaticamente por correspondência de valor/data.
- **Aggregate Root**: Não — entidade de ligação, referenciada tanto por Conta a Pagar/Receber quanto
  por Lançamento de Extrato Bancário; tratada como parte do agregado que a criou (Conta a
  Pagar/Receber).
- **Bounded Context proprietário**: `financial`
- **Principais relacionamentos**: Conta a Pagar (0..1); Conta a Receber (0..1); Lançamento de
  Extrato Bancário (1:1) — exatamente um dos dois primeiros, nunca ambos.
- **Eventos que publica**: `ContaAPagarConciliada` (já catalogado); `ContaAReceberConciliada` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: um Lançamento de Extrato Bancário só é referenciado por uma Conciliação Bancária
  (não pode ser usado duas vezes).
- **Regras de negócio associadas**: D017/D018/D037, D100 (o registro conciliado nunca é reescrito —
  divergência gera Estorno Financeiro, não edição).
- **Estados**: Não aplicável — registro pontual, imutável após criado.
- **Auditoria**: D007.
- **Linha do tempo**: parte da Conta a Pagar/Receber correspondente.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Sim, registro da divergência quando houver (D023).
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: `005-FINANCEIRO.md`.
- **Evoluções futuras previstas**: sugestão automática de correspondência via IA.
- **Dependências obrigatórias**: Lançamento de Extrato Bancário, e exatamente uma de Conta a
  Pagar/Conta a Receber.
- **Dependências proibidas**: Cliente, CT-e, Viagem (diretamente).
- **Dono da Timeline**: Aggregate Conta a Pagar ou Conta a Receber correspondente.
- **Capacidade Offline**: Não.

## Estorno Financeiro

- **Objetivo**: Registra a reversão de um lançamento financeiro já conciliado ou fechado — o
  mecanismo oficial de correção pós-imutabilidade (D100).
- **Responsabilidades**: Referenciar o lançamento original (Conta a Pagar, Conta a Receber ou
  Fatura); guardar motivo e valor estornado.
- **O que não faz**: Não edita o lançamento original — cria um novo registro que o neutraliza
  contabilmente, preservando ambos no histórico.
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `financial`
- **Principais relacionamentos**: Conta a Pagar, Conta a Receber ou Fatura (referenciados,
  exatamente um).
- **Eventos que publica**: `EstornoFinanceiroRegistrado` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: todo Estorno Financeiro tem origem explícita (D099) e motivo obrigatório (D007);
  valor do estorno nunca excede o valor original.
- **Regras de negócio associadas**: D001 (soft delete — o lançamento original nunca é excluído),
  D099, D100.
- **Estados**: Não aplicável — registro pontual, imutável após criado.
- **Auditoria**: D007.
- **Linha do tempo**: parte do lançamento original.
- **Anexos suportados**: justificativa documental (D024).
- **Comentários suportados**: Sim (D023).
- **KPIs relacionados**: taxa de estorno (calculada em `analytics`, D090).
- **Documentos canônicos relacionados**: `005-FINANCEIRO.md`.
- **Evoluções futuras previstas**: fluxo de aprovação próprio para estornos acima de um valor,
  análogo à Aprovação de Despesa.
- **Dependências obrigatórias**: Conta a Pagar, Conta a Receber ou Fatura (exatamente um).
- **Dependências proibidas**: Cliente, CT-e, Viagem (diretamente).
- **Dono da Timeline**: Aggregate do lançamento original.
- **Capacidade Offline**: Não.

## Forma de Pagamento

- **Objetivo**: Catálogo dos meios de pagamento/recebimento aceitos (PIX, Boleto, Cartão,
  Transferência, Dinheiro).
- **Responsabilidades**: Ser referenciada por Fatura/Conta a Pagar/Conta a Receber.
- **O que não faz**: Não processa o pagamento em si — isso é o gateway (fora do escopo eletrônico
  desta fundação).
- **Aggregate Root**: Sim — entidade de **Referência** (D036).
- **Bounded Context proprietário**: `financial`
- **Principais relacionamentos**: Fatura, Conta a Pagar, Conta a Receber (referenciadas).
- **Eventos que publica**: `FormaDePagamentoCadastrada` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: nome único por tenant.
- **Regras de negócio associadas**: D001, D005/D006.
- **Estados**: `Ativa` / `Inativa`.
- **Auditoria**: D007.
- **Linha do tempo**: cadastro, alterações.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: distribuição de recebimentos por forma de pagamento.
- **Documentos canônicos relacionados**: Nenhum.
- **Evoluções futuras previstas**: integração eletrônica direta por forma de pagamento (gateway
  PIX/boleto).
- **Dependências obrigatórias**: Nenhuma.
- **Dependências proibidas**: Cliente, CT-e, Viagem.
- **Dono da Timeline**: Aggregate Forma de Pagamento (este próprio).
- **Capacidade Offline**: Consulta Offline.

## Plano de Contas

- **Objetivo**: Catálogo de categorização contábil (ex: "Combustível", "Manutenção", "Pedágio",
  "Administrativo") usado para classificar Contas a Pagar/Receber — mesmo conceito que apareceu
  nomeado "Categoria Financeira" na modelagem relacional (D184); reconciliado (D076) em vez de
  duplicado.
- **Responsabilidades**: Ser referenciado por Conta a Pagar/Receber; suportar DRE e relatórios
  contábeis (consumidos por `analytics`, D090 — o Plano de Contas em si é cadastro, não indicador);
  desde D184, classificar-se como Receita ou Despesa e organizar-se em hierarquia (categoria pai/
  filha), sem precisar de uma segunda entidade para isso.
- **O que não faz**: Não calcula o DRE sozinho — é apenas a estrutura de categorização que o
  `analytics` consome.
- **Aggregate Root**: Sim — entidade de **Referência** (D036).
- **Bounded Context proprietário**: `financial`
- **Principais relacionamentos**: Conta a Pagar, Conta a Receber (referenciadas); Plano de Contas
  pai (auto-referência, D184, opcional — hierarquia).
- **Eventos que publica**: `PlanoDeContasAtualizado` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: código contábil único por tenant; uma categoria nunca é pai dela mesma, nem de
  um de seus próprios ancestrais (sem ciclo na hierarquia, D184).
- **Regras de negócio associadas**: D001, D005/D006, D184.
- **Estados**: `Ativo` / `Inativo`.
- **Auditoria**: D007.
- **Linha do tempo**: cadastro, alterações.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: Nenhum direto (fonte de categorização para indicadores de `analytics`).
- **Documentos canônicos relacionados**: Nenhum.
- **Evoluções futuras previstas**: integração com GestorContábil (ver
  [`../product/VISION.md`](../product/VISION.md), capítulo 20).
- **Dependências obrigatórias**: Nenhuma.
- **Dependências proibidas**: Cliente, CT-e, Viagem.
- **Dono da Timeline**: Aggregate Plano de Contas (este próprio).
- **Capacidade Offline**: Consulta Offline.

## Posição de Caixa

- **Objetivo**: Visão consolidada e derivada do saldo de caixa projetado (Contas a Pagar/Receber em
  aberto, por período), para consulta rápida pelo Financeiro — operacional, distinta do
  Fluxo de Caixa/DRE consolidado de `analytics` (D090).
- **Responsabilidades**: Agregar Contas a Pagar/Receber pendentes por data prevista.
- **O que não faz**: Não é a fonte de verdade de nenhuma Conta a Pagar/Receber individual — é uma
  projeção (read model), mantida por `financial` a partir dos próprios agregados que já possui
  (D081, mesmo princípio de `Disponibilidade do Veículo`, [`003-frota.md`](./003-frota.md)).
- **Aggregate Root**: Não — é um read model, não pertence a nenhum agregado transacional.
- **Bounded Context proprietário**: `financial`
- **Principais relacionamentos**: Conta a Pagar, Conta a Receber (agregadas por data/status).
- **Eventos que publica**: Nenhum — é consumidora.
- **Eventos que consome**: Todos os eventos de Conta a Pagar/Receber (D032).
- **Invariantes**: reflete, com o menor atraso possível, a combinação dos eventos consumidos —
  nunca editada diretamente.
- **Regras de negócio associadas**: D032, D081, D090 (não é DRE/EBITDA — é só saldo projetado por
  data, um dado operacional do dia a dia do Financeiro, não um indicador estratégico de BI).
- **Estados**: Não aplicável — é ela própria um valor consolidado.
- **Auditoria**: D007 — de quando cada recomputação ocorreu.
- **Linha do tempo**: Não aplicável — não tem timeline própria.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: capital de giro necessário (calculado em `analytics`, a partir destes
  dados).
- **Documentos canônicos relacionados**: `005-FINANCEIRO.md`.
- **Evoluções futuras previstas**: projeção preditiva por IA (sazonalidade, inadimplência esperada).
- **Dependências obrigatórias**: Conta a Pagar e Conta a Receber, por evento.
- **Dependências proibidas**: Cliente, CT-e, Viagem — nunca lê as tabelas desses módulos
  diretamente, só consome eventos (D008).
- **Dono da Timeline**: Não aplicável (sem timeline própria).
- **Capacidade Offline**: Não.

---

> **Entidade nova abaixo (D189), identificada ao modelar a camada relacional
> (`docs/database/relational/006-financeiro.md`).**

## Conta Bancária

- **Objetivo**: Representa uma conta bancária do tenant (corrente, poupança) usada para
  recebimentos e pagamentos — um tenant pode ter mais de uma.
- **Responsabilidades**: Ser referenciada por `Lançamento de Extrato Bancário` (qual conta o extrato
  pertence) e, opcionalmente, por Conta a Pagar/Receber (conta de origem/destino preferencial).
- **O que não faz**: Não processa a transação bancária em si — isso é o gateway/banco real, fora do
  escopo eletrônico desta fundação; aqui é só o cadastro.
- **Aggregate Root**: Sim — entidade de **Referência** (D036).
- **Bounded Context proprietário**: `financial`
- **Principais relacionamentos**: Lançamento de Extrato Bancário (1:N).
- **Eventos que publica**: `ContaBancariaCadastrada` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: número da conta único por tenant.
- **Regras de negócio associadas**: D001, D005/D006.
- **Estados**: `Ativa` / `Inativa`.
- **Auditoria**: D007.
- **Linha do tempo**: cadastro, alterações.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: integração Open Finance (conexão direta com o banco).
- **Dependências obrigatórias**: Nenhuma.
- **Dependências proibidas**: Cliente, CT-e, Viagem, Pneu.
- **Dono da Timeline**: Aggregate Conta Bancária (este próprio).
- **Capacidade Offline**: Consulta Offline.
