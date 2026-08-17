# 004 — Manutenção

Atributos distintivos das 8 entidades de [`../../domain/004-manutencao.md`](../../domain/004-manutencao.md).
Atributos universais (D069) e Padrões de atributo/Atributos Críticos (D077/D081) não são repetidos
aqui — ver [`README.md`](./README.md). Máquina de estados canônica da Ordem de Serviço:
[`../../flows/003-MANUTENCAO.md`](../../flows/003-MANUTENCAO.md) (D035).

---

## Ordem de Serviço

Dono: `maintenance` · Natureza: Transactional Data · Aggregate Root.

O pedido de atenção especial ("separar claramente: abertura; diagnóstico; orçamento; aprovação;
execução; encerramento") não é uma mudança na máquina de estados — é a organização dos atributos
por fase, dentro da mesma entidade. Cada atributo abaixo é rotulado com sua fase de origem.

| Atributo | Nome | Tipo Conceitual | Fase | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|---|
| ORDEM_SERVICO.VEICULO_TRACIONADOR_ID | Veículo | Referência | Abertura | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| ORDEM_SERVICO.TIPO | Tipo | Enum | Abertura | Sim | Informado/Calculado (automática quando preventiva) | Não | Interno | Valores: `Preventiva`/`Corretiva`/`Emergencial`/`Garantia` — atributo independente do status; todas seguem a mesma máquina de estados (`003-MANUTENCAO.md`) |
| ORDEM_SERVICO.ORIGEM_ABERTURA | Origem da abertura | Enum | Abertura | Sim | Capturado (sistema) | Não | Interno | Valores: Manual/`ManutencaoPreventivaSugerida`/`ViagemInterrompida`/`ChecklistReprovado`/Garantia — rastreia o gatilho real (ver ponto 2, Preventiva, abaixo) |
| ORDEM_SERVICO.DESCRICAO_PROBLEMA | Descrição do problema relatado | Texto Longo | Abertura | Sim | Informado | Não | Interno | O que foi relatado, distinto do diagnóstico técnico |
| ORDEM_SERVICO.CAUSA | Causa imediata (quando Corretiva) | Enum | Diagnóstico | Não, obrigatório quando `TIPO = Corretiva` | Informado (Mecânico) | Não | Interno | Valores: Desgaste/Quebra/Acidente/Mau uso/Inspeção/Recall — ver ponto 3, Corretiva, abaixo |
| ORDEM_SERVICO.CAUSA_RAIZ | Causa raiz (quando Corretiva) | Texto Longo | Diagnóstico | Não | Informado (Mecânico/Analista de Frota) | Não | Interno | D089 — distinta da Causa imediata: ex. Causa imediata "Quebra", Causa Raiz "Lubrificação inadequada". Alimenta indicadores de confiabilidade (calculados em `analytics`, D090 — não persistidos aqui) |
| ORDEM_SERVICO.DIAGNOSTICO_TECNICO | Diagnóstico técnico | Texto Longo | Diagnóstico | Não | Informado (Mecânico) | Não | Interno | |
| ORDEM_SERVICO.MECANICO_ID | Mecânico responsável | Referência | Diagnóstico | Não | Informado | Sim (reatribuição gera novo registro) | Interno | FK para Funcionário — ver D085: se a reatribuição ganhar vigência temporal própria, vira entidade dedicada; hoje é referência simples de baixo volume de troca |
| ORDEM_SERVICO.CUSTO_PREVISTO | Custo Previsto (orçamento) | Monetário | Orçamento | Não | Calculado (soma dos Itens de OS estimados) | Sim, quando revisado antes da aprovação | Financeiro | Moeda: BRL (D075). D086 — par de `CUSTO_REALIZADO`, mesmo princípio de Receita Prevista/Realizada da Viagem (`002-operacao.md`). Comparado contra a Alçada de Aprovação de Manutenção — ver ponto 5, Aprovação, abaixo |
| ORDEM_SERVICO.NECESSITA_APROVACAO | Necessita aprovação? | Booleano | Aprovação | Sim | Calculado (`CUSTO_PREVISTO` > alçada configurada) | Não | Interno | Ver ponto 5, Aprovação, abaixo |
| ORDEM_SERVICO.EVIDENCIA_CONCLUSAO_EXIGIDA | Evidência de conclusão exigida? | Booleano | Aprovação/Execução | Sim | Informado (parâmetro do tenant, ver ponto 5) | Não | Interno | D088 — quando `Sim` e `TIPO = Preventiva`, a transição para `CONCLUIDA` exige ao menos um Anexo (checklist, foto, nota fiscal ou assinatura — D024) ou um Comentário (D023) registrado; não obrigatório por padrão em todo tenant |
| ORDEM_SERVICO.STATUS | Status | Enum | Todas | Sim | Calculado (transições da máquina de estados) | Sim, em `OrdemServicoStatusHistory` (D017/D018) | Interno | Valores completos e transições: `003-MANUTENCAO.md`. **Atributo Crítico (D077)** — ver Governança abaixo |
| ORDEM_SERVICO.DATA_INICIO_EXECUCAO | Início da execução | Data/Hora | Execução | Não | Capturado (sistema, na transição para `EM_EXECUCAO`) | Não | Interno | Granularidade: segundo (D074) |
| ORDEM_SERVICO.DATA_CONCLUSAO | Conclusão | Data/Hora | Execução | Não | Capturado (sistema, na transição para `CONCLUIDA`) | Não | Interno | Granularidade: segundo (D074); junto com `DATA_INICIO_EXECUCAO` é o dado bruto a partir do qual `analytics` calcula MTTR — o indicador em si não é persistido aqui (D090) |
| ORDEM_SERVICO.CUSTO_REALIZADO | Custo Realizado (consolidado) | Monetário | Encerramento | Não, obrigatório em `FECHADA` | Calculado (soma dos Itens de OS realizados, por categoria — ver ponto 4, Custos, abaixo) | Não (congela em `FECHADA`) | Financeiro | Moeda: BRL (D075). D086 — par de `CUSTO_PREVISTO`; o desvio entre os dois é indicador de BI (precisão de orçamento/eficiência da oficina), não um terceiro campo persistido (D090). Fonte de verdade para o lançamento no Centro de Custo (`financial`), publicado por evento, nunca lido diretamente (D008) |
| ORDEM_SERVICO.CODIGO | Código funcional | Texto Curto | — (universal, D069) | Sim | Capturado (sistema) | Não | Interno | Reforço de D084 aqui: mesmo uma OS `Cancelada`, seu código nunca é reaproveitado por outra OS |

### Governança do atributo crítico `STATUS` (D077)

| Quem altera? | Quando muda? | Quem pode visualizar? | Quem nunca altera? |
|---|---|---|---|
| Mecânico (`ABERTA`→`EM_DIAGNOSTICO`→`EM_EXECUCAO`→`CONCLUIDA`); Gestor Operacional/Analista de Frota (aprovação, `AGUARDANDO_APROVACAO`→`EM_DIAGNOSTICO`); Almoxarife (transições envolvendo `AGUARDANDO_PECA`); Analista de Frota (`CONCLUIDA`→`FECHADA`) | A cada transição válida da máquina de estados (ver `003-MANUTENCAO.md`) | Conforme RBAC; Auditor sempre em modo leitura | Frontend sozinho (D027); `financial` (só lê o evento de fechamento, nunca escreve o status da OS) |

---

## 2. Preventiva — gatilhos de `Plano de Manutenção Preventiva`

A manutenção preventiva **nunca nasce manualmente por padrão** — `ORDEM_SERVICO.ORIGEM_ABERTURA`
para uma OS `Preventiva` é sempre `ManutencaoPreventivaSugerida`, nunca `Manual`. O domínio original
(`docs/domain/004-manutencao.md`) descrevia o Plano como avaliado apenas "por km ou tempo" — esta
rodada amplia explicitamente o leque de gatilhos possíveis, sem contradizer o que já existia (é uma
expansão do mesmo atributo, não uma reconciliação de nomes conflitantes, D076 não se aplica aqui).

Dono: `maintenance` · Natureza: Reference Data (D036) · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| PLANO_MANUTENCAO_PREVENTIVA.VEICULO_TRACIONADOR_ID / CATEGORIA_VEICULO_ID | Escopo do plano | Referência | Sim (um dos dois) | Informado | Não | Interno | Específico a um veículo ou aplicado a toda uma Categoria |
| PLANO_MANUTENCAO_PREVENTIVA.TIPO_GATILHO | Tipo de gatilho | Enum | Sim | Informado | Não | Interno | Valores: Quilometragem/Horas de motor/Dias/Calendário (data fixa)/Motor (horas de operação do motor, distinto de km rodado)/Telemetria (evento externo, quando disponível)/Recomendação do fabricante. Cada plano tem exatamente um tipo de gatilho — planos compostos (ex: "o que ocorrer primeiro entre km e dias") são múltiplos Planos vinculados ao mesmo Tipo de Serviço, não um único atributo multivalorado |
| PLANO_MANUTENCAO_PREVENTIVA.VALOR_INTERVALO | Valor do intervalo | Decimal | Sim | Informado | Não | Interno | Unidade depende de `TIPO_GATILHO` (km, horas ou dias); maior que zero |
| PLANO_MANUTENCAO_PREVENTIVA.TIPO_SERVICO_ID | Tipo de serviço a executar | Referência | Sim | Informado | Não | Interno | FK para Tipo de Serviço |
| PLANO_MANUTENCAO_PREVENTIVA.STATUS | Status | Enum | Sim | Informado | Não | Interno | Valores: `Ativo`/`Inativo` |

---

## Entrega e correlatas menores

### Item de Ordem de Serviço

Dono: `maintenance` · Natureza: Transactional Data · Parte do agregado Ordem de Serviço.

Esta é a entidade que materializa **4. Custos** — cada linha pertence a exatamente uma categoria de
custo, permitindo o indicador de custo por placa segmentado corretamente.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| ITEM_ORDEM_SERVICO.ORDEM_SERVICO_ID | Ordem de Serviço | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| ITEM_ORDEM_SERVICO.CATEGORIA_CUSTO | Categoria de custo | Enum | Sim | Informado | Não | Financeiro | Valores fechados: Peças/Pneus/Serviços/Terceiros/Mão de Obra Interna/Mão de Obra Terceirizada/Deslocamento/Outros. "Pneus" aqui é a categoria financeira do custo dentro da OS — o dado técnico do pneu em si continua vivendo em `Pneu`/`Posicionamento de Pneu` ([`005-pneus.md`](./005-pneus.md), planejado), sem conflito de posse (D033/D034): esta linha só referencia o custo, não os atributos do pneu |
| ITEM_ORDEM_SERVICO.DESCRICAO | Descrição | Texto Curto | Sim | Informado | Não | Interno | |
| ITEM_ORDEM_SERVICO.PECA_EM_ESTOQUE_ID | Peça em Estoque referenciada | Referência | Não | Informado | Não | Interno | Preenchido apenas quando `CATEGORIA_CUSTO = Peças` e a peça vem do Almoxarifado |
| ITEM_ORDEM_SERVICO.QUANTIDADE | Quantidade | Decimal | Sim | Informado | Não | Interno | Maior que zero |
| ITEM_ORDEM_SERVICO.VALOR_UNITARIO | Valor unitário | Monetário | Sim | Informado | Não | Financeiro | Moeda: BRL (D075) |
| ITEM_ORDEM_SERVICO.VALOR_TOTAL | Valor total | Monetário | Sim | Calculado (`QUANTIDADE × VALOR_UNITARIO`) | Não | Financeiro | Moeda: BRL (D075) — soma por `CATEGORIA_CUSTO` alimenta `ORDEM_SERVICO.CUSTO_REALIZADO` — nunca soma/mantém saldo de estoque (D087): esta linha representa consumo, não estoque, que é exclusivo de Peça em Estoque/Movimentação de Estoque, abaixo |

### Solicitação de Peça

Dono: `maintenance` · Natureza: Transactional Data · Parte do agregado Ordem de Serviço.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| SOLICITACAO_PECA.ORDEM_SERVICO_ID | Ordem de Serviço | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| SOLICITACAO_PECA.FORNECEDOR_ID | Fornecedor | Referência | Sim | Informado | Não | Interno | FK — [`001-cadastros.md`](./001-cadastros.md) |
| SOLICITACAO_PECA.STATUS | Status | Enum | Sim | Informado/Calculado | Sim | Interno | Valores: `Solicitada`/`Recebida`/`Cancelada` |
| SOLICITACAO_PECA.PRAZO_PREVISTO | Prazo previsto de entrega | Data | Não | Informado | Não | Interno | Granularidade: dia (D074) |

### Peça em Estoque

Dono: `maintenance` · Natureza: Reference Data (D036, identidade estável, quantidade variável) ·
Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| PECA_ESTOQUE.NOME | Nome | Texto Curto | Sim | Informado | Não | Interno | |
| PECA_ESTOQUE.QUANTIDADE_DISPONIVEL | Quantidade disponível | Inteiro | Sim | Derivado (D081 — projeção; soma das Movimentações de Estoque) | Não — a fonte da verdade é `Movimentação de Estoque` (D083) | Interno | Nunca editado diretamente; sempre recalculado a partir do histórico append-only |
| PECA_ESTOQUE.ESTOQUE_MINIMO | Estoque mínimo | Inteiro | Não | Informado | Não | Interno | Gatilho de `PecaAbaixoDoEstoqueMinimo` |
| PECA_ESTOQUE.CUSTO_MEDIO | Custo médio | Monetário | Não | Calculado (média ponderada das entradas) | Não | Financeiro | Moeda: BRL (D075) |

### Movimentação de Estoque

Dono: `maintenance` · Natureza: Transactional Data · Histórica (D037/D083) · Parte do agregado
Peça em Estoque.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| MOVIMENTACAO_ESTOQUE.PECA_ESTOQUE_ID | Peça em Estoque | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| MOVIMENTACAO_ESTOQUE.TIPO | Tipo de movimentação | Enum | Sim | Informado | **É ela própria o histórico** — nunca editada (D037) | Interno | Valores: Entrada/Saída |
| MOVIMENTACAO_ESTOQUE.QUANTIDADE | Quantidade | Inteiro | Sim | Informado | Não | Interno | Maior que zero; toda Saída exige saldo suficiente disponível no momento |
| MOVIMENTACAO_ESTOQUE.ORDEM_SERVICO_ID | Ordem de Serviço associada | Referência | Não | Capturado (sistema) | Não | Interno | Preenchido quando a Saída é para uma OS |
| MOVIMENTACAO_ESTOQUE.DATA_HORA | Data/hora | Data/Hora | Sim | Capturado (sistema) | Não | Interno | Granularidade: segundo (D074) |

### Tipo de Serviço

Dono: `maintenance` · Natureza: Reference Data (D036) · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| TIPO_SERVICO.NOME | Nome | Texto Curto | Sim | Informado | Não | Interno | Único por tenant. Ex: Troca de óleo, Alinhamento |
| TIPO_SERVICO.STATUS | Status | Enum | Sim | Informado | Não | Interno | Valores: `Ativo`/`Inativo` |

### Aprovação de Custo

Dono: `maintenance` · Natureza: Transactional Data · Parte do agregado Ordem de Serviço. Ver
**5. Aprovação**, abaixo, para a regra completa que gera esta entidade.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| APROVACAO_CUSTO.ORDEM_SERVICO_ID | Ordem de Serviço | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| APROVACAO_CUSTO.DECISAO | Decisão | Enum | Sim | Informado (Gestor/Analista de Frota) | Não (registro pontual, imutável após criado) | Interno | Valores: Aprovado/Rejeitado — decisão explícita, nunca implícita (D010) |
| APROVACAO_CUSTO.JUSTIFICATIVA | Justificativa | Texto Longo | Não, obrigatório quando `Rejeitado` | Informado | Não | Interno | |
| APROVACAO_CUSTO.ATOR_ID | Ator responsável | Referência | Sim | Capturado (sistema) | Não | Interno | Quem decidiu — condição de D080/D085: esta entidade já responde "quem alterou" |
| APROVACAO_CUSTO.DATA_HORA | Data/hora da decisão | Data/Hora | Sim | Capturado (sistema) | Não | Interno | Granularidade: segundo (D074) |

---

## 5. Aprovação — alçada configurável por tenant

`ORDEM_SERVICO.NECESSITA_APROVACAO` é calculado comparando `CUSTO_PREVISTO` contra uma **Alçada de
Aprovação de Manutenção** — um valor configurável por tenant (e, no futuro, por perfil/categoria de
veículo, ver Requisitos futuros de `003-MANUTENCAO.md`). Esse limite **não é um atributo de
`maintenance`**: é um parâmetro de configuração do tenant, de posse do bounded context `settings`
(D033/D034) — `maintenance` apenas o lê no momento do diagnóstico, nunca o duplica. Ainda não existe
uma entidade própria de Parâmetro/Configuração documentada (`010-administracao.md`, planejado,
cobrirá `settings`); registrado aqui como dependência explícita para não ser esquecido quando aquele
arquivo for escrito — mesmo cuidado já tomado com `tracking` em `003-frota.md`. Mesma origem para
`ORDEM_SERVICO.EVIDENCIA_CONCLUSAO_EXIGIDA` (D088) — outro parâmetro de política do tenant, lido por
`maintenance`, não duplicado.

| Atributo (referência futura, hoje só nomeado) | Nome | Tipo Conceitual | Observações |
|---|---|---|---|
| CONFIGURACAO_TENANT.ALCADA_APROVACAO_MANUTENCAO | Alçada de aprovação de manutenção | Monetário | Moeda: BRL (D075). Dono: `settings`. A ser detalhado em `010-administracao.md` |

## Como este documento cresce

Mesmo princípio de todo o dicionário: um arquivo `NNN-categoria.md` por vez, na ordem do roadmap
(ver [`README.md`](./README.md)). Próximo: `005-pneus.md`.
