# 004 — Manutenção

Entidades de manutenção (Ordem de Serviço e correlatas) do GestorFrete. Template completo de 22
campos (ver [`README.md`](./README.md)). Ver [`ENTITY_CATALOG.md`](./ENTITY_CATALOG.md) para o
índice completo desta categoria.

**Reconciliação (9 entidades, era 8)**: `Checklist` estava referenciada desde a fundação por
`ChecklistReprovado`/`ChecklistAprovado` (`../product/EVENT_MAP.md`) e por `Trip.status_operacional
= AGUARDANDO_CHECKLIST` (`freight`), mas nunca tinha sido formalizada como entidade própria — a nota
em [`../database/relational/005-manutencao.md`](../database/relational/005-manutencao.md) dizia
explicitamente "não modelado neste lote" (D101/D102: nenhuma tabela nasce sem a entidade existir
aqui primeiro). Formalizada agora porque o desbloqueio real de `AGUARDANDO_CHECKLIST → LIBERADA`
(gap identificado nos Lotes Operação e Documentos Fiscais) depende dela.

---

## Ordem de Serviço

- **Objetivo**: Documento interno que formaliza a execução de um serviço de manutenção sobre um
  veículo (ver [`../product/GLOSSARY.md`](../product/GLOSSARY.md)).
- **Responsabilidades**: Orquestrar diagnóstico, aprovação, peças e execução; sua máquina de
  estados canônica está em [`../flows/003-MANUTENCAO.md`](../flows/003-MANUTENCAO.md) (D035).
- **O que não faz**: Não compra peça diretamente (delega a Solicitação de Peça); não lança o custo
  no Centro de Custo sozinha (publica evento consumido por `financial`).
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `maintenance`
- **Principais relacionamentos**: Veículo Tracionador, Fornecedor, Funcionário/Mecânico
  (referenciados por ID); Item de Ordem de Serviço, Solicitação de Peça, Aprovação de Custo (filhos
  do agregado).
- **Eventos que publica**: `OrdemServicoAberta`, `OrdemServicoAprovacaoPendente`,
  `OrdemServicoConcluida`, `OrdemServicoFechada`, `OrdemServicoCancelada` (já catalogados em
  [`../product/EVENT_MAP.md`](../product/EVENT_MAP.md)).
- **Eventos que consome**: `ViagemInterrompida` (`freight` — pane em rota), `ChecklistReprovado`
  (checklist de oficina/saída).
- **Invariantes**: uma OS `Fechada` nunca é reaberta (ver `003-MANUTENCAO.md`, transições
  inválidas).
- **Regras de negócio associadas**: D015–D018 (máquina de estados + histórico).
- **Estados**: Ver `003-MANUTENCAO.md` (fonte canônica, D035).
- **Auditoria**: D007.
- **Linha do tempo (Timeline Universal)**: ver `003-MANUTENCAO.md`, Capacidades Transversais.
- **Anexos suportados**: foto do defeito, nota fiscal da peça (D024).
- **Comentários suportados**: Sim (D023).
- **KPIs relacionados**: MTTR, custo de manutenção por veículo/km.
- **Documentos canônicos relacionados**: `003-MANUTENCAO.md`.
- **Evoluções futuras previstas**: integração eletrônica com fornecedores.
- **Dependências obrigatórias**: Veículo Tracionador.
- **Dependências proibidas**: Cliente, CT-e (D033/D034 — a OS nunca precisa saber quem é o cliente
  do frete nem do documento fiscal da viagem).
- **Dono da Timeline**: Aggregate Ordem de Serviço (este próprio).
- **Capacidade Offline**: Não (D039) — execução tipicamente em ambiente conectado, distinto do app
  do motorista em rota.

## Item de Ordem de Serviço

- **Objetivo**: Linha de uma OS — peça ou serviço específico executado.
- **Responsabilidades**: Guardar quantidade, valor unitário; referenciar Peça em Estoque quando
  aplicável, ou representar mão de obra.
- **O que não faz**: Não existe fora de uma OS.
- **Aggregate Root**: Não — parte do agregado Ordem de Serviço.
- **Bounded Context proprietário**: `maintenance`
- **Principais relacionamentos**: Ordem de Serviço (N:1); Peça em Estoque (0..1:1, quando
  aplicável); Tipo de Serviço (N:1).
- **Eventos que publica**: Nenhum diretamente.
- **Eventos que consome**: Nenhum.
- **Invariantes**: quantidade e valor devem ser maiores que zero.
- **Regras de negócio associadas**: D005/D006.
- **Estados**: Segue a Ordem de Serviço.
- **Auditoria**: D007.
- **Linha do tempo**: parte da OS.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: custo de peças vs. mão de obra.
- **Documentos canônicos relacionados**: Nenhum.
- **Evoluções futuras previstas**: Nenhuma isolada.
- **Dependências obrigatórias**: Ordem de Serviço.
- **Dependências proibidas**: Cliente, CT-e, Financeiro (diretamente — o custo total é agregado e
  só então publicado via evento).
- **Dono da Timeline**: Aggregate Ordem de Serviço.
- **Capacidade Offline**: Não.

## Solicitação de Peça

- **Objetivo**: Registra a necessidade de compra de uma peça não disponível em estoque para uma OS.
- **Responsabilidades**: Ligar a OS a um Fornecedor; acompanhar prazo de entrega.
- **O que não faz**: Não é a compra em si (fora do escopo eletrônico desta fundação) — é o registro
  da necessidade.
- **Aggregate Root**: Não — parte do agregado Ordem de Serviço.
- **Bounded Context proprietário**: `maintenance`
- **Principais relacionamentos**: Ordem de Serviço (N:1); Fornecedor (N:1, ver
  [`001-cadastros.md`](./001-cadastros.md)).
- **Eventos que publica**: `PecaSolicitada` (já catalogado).
- **Eventos que consome**: Nenhum.
- **Invariantes**: toda Solicitação de Peça pertence a exatamente uma OS.
- **Regras de negócio associadas**: D005/D006.
- **Estados**: `Solicitada` / `Recebida` / `Cancelada`.
- **Auditoria**: D007.
- **Linha do tempo**: parte da OS.
- **Anexos suportados**: pedido de compra (D024).
- **Comentários suportados**: Sim, acompanhamento de prazo (D023).
- **KPIs relacionados**: prazo médio de entrega de fornecedor.
- **Documentos canônicos relacionados**: `003-MANUTENCAO.md`.
- **Evoluções futuras previstas**: cotação eletrônica automatizada.
- **Dependências obrigatórias**: Ordem de Serviço, Fornecedor.
- **Dependências proibidas**: Cliente, CT-e, Financeiro.
- **Dono da Timeline**: Aggregate Ordem de Serviço.
- **Capacidade Offline**: Não.

## Peça em Estoque

- **Objetivo**: Representa um item de peça/insumo disponível no Almoxarifado.
- **Responsabilidades**: Guardar quantidade disponível, custo médio, estoque mínimo.
- **O que não faz**: Não decide sozinha quando comprar — a ação parte de Solicitação de
  Peça/Movimentação de Estoque quando o estoque mínimo é atingido.
- **Aggregate Root**: Sim — entidade de **Referência** (D036) cuja quantidade muda, mas cuja
  identidade é estável.
- **Bounded Context proprietário**: `maintenance`
- **Principais relacionamentos**: Movimentação de Estoque (1:N); Item de Ordem de Serviço
  (referenciado).
- **Eventos que publica**: `PecaAbaixoDoEstoqueMinimo` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: quantidade nunca é negativa.
- **Regras de negócio associadas**: D001, D005/D006.
- **Estados**: Não aplicável — quantidade é um valor, não um status.
- **Auditoria**: D007.
- **Linha do tempo**: cadastro, movimentações vinculadas.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: giro de estoque, itens em ruptura.
- **Documentos canônicos relacionados**: `003-MANUTENCAO.md`.
- **Evoluções futuras previstas**: reposição automática sugerida.
- **Dependências obrigatórias**: Fornecedor (padrão, opcional).
- **Dependências proibidas**: Cliente, CT-e, Financeiro, Viagem.
- **Dono da Timeline**: Aggregate Peça em Estoque (este próprio).
- **Capacidade Offline**: Consulta Offline — o Almoxarife pode precisar consultar disponibilidade
  sem sinal, mas a baixa em si tipicamente exige conexão.

## Movimentação de Estoque

- **Objetivo**: Registro histórico (D037) de entrada/saída de uma Peça em Estoque.
- **Responsabilidades**: Ser a fonte de verdade do saldo de uma Peça em Estoque (soma das
  movimentações).
- **O que não faz**: Não é editável — apenas inserida.
- **Aggregate Root**: Não — parte do agregado Peça em Estoque; entidade **Histórica** (D037).
- **Bounded Context proprietário**: `maintenance`
- **Principais relacionamentos**: Peça em Estoque (N:1); Ordem de Serviço (0..1, quando é saída
  para uma OS).
- **Eventos que publica**: `MovimentacaoDeEstoqueRegistrada` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: toda saída deve ter quantidade suficiente disponível no momento — nunca gera
  saldo negativo.
- **Regras de negócio associadas**: D017/D018/D037.
- **Estados**: Não aplicável.
- **Auditoria**: D007.
- **Linha do tempo**: parte da Peça em Estoque.
- **Anexos suportados**: nota fiscal de entrada (D024).
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: giro de estoque.
- **Documentos canônicos relacionados**: `003-MANUTENCAO.md`.
- **Evoluções futuras previstas**: Nenhuma isolada.
- **Dependências obrigatórias**: Peça em Estoque.
- **Dependências proibidas**: Cliente, CT-e, Financeiro, Viagem.
- **Dono da Timeline**: Aggregate Peça em Estoque.
- **Capacidade Offline**: Não.

## Plano de Manutenção Preventiva

- **Objetivo**: Define regras de recorrência (por km ou tempo) que disparam a sugestão de abertura
  de uma OS preventiva.
- **Responsabilidades**: Ser avaliado periodicamente contra a Leitura de Hodômetro do veículo (ver
  [`003-frota.md`](./003-frota.md)).
- **O que não faz**: Não abre a OS diretamente — publica um evento que o fluxo de abertura de OS
  consome (D032).
- **Aggregate Root**: Sim — entidade de **Referência** (D036).
- **Bounded Context proprietário**: `maintenance`
- **Principais relacionamentos**: Categoria de Veículo (N:1, opcional) ou Veículo Tracionador (N:1,
  específico).
- **Eventos que publica**: `ManutencaoPreventivaSugerida` (a formalizar em
  `shared/DOMAIN_EVENTS.md`).
- **Eventos que consome**: `HodometroAtualizado` (`fleet`).
- **Invariantes**: intervalo de recorrência maior que zero (em km ou dias).
- **Regras de negócio associadas**: D001, D005/D006, D008 (reage a evento, nunca lê a tabela de
  outro módulo diretamente).
- **Estados**: `Ativo` / `Inativo`.
- **Auditoria**: D007.
- **Linha do tempo**: criação, alterações, OSs geradas (por referência).
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Sim (D023).
- **KPIs relacionados**: percentual de manutenção preventiva vs. corretiva.
- **Documentos canônicos relacionados**: `003-MANUTENCAO.md`.
- **Evoluções futuras previstas**: sugestão dinâmica por IA (ver
  [`../product/VISION.md`](../product/VISION.md)).
- **Dependências obrigatórias**: Categoria de Veículo ou Veículo Tracionador.
- **Dependências proibidas**: Cliente, CT-e, Financeiro, Viagem.
- **Dono da Timeline**: Aggregate Plano de Manutenção Preventiva (este próprio).
- **Capacidade Offline**: Não.

## Tipo de Serviço

- **Objetivo**: Catálogo dos tipos de serviço de manutenção possíveis (troca de óleo, alinhamento,
  etc.).
- **Responsabilidades**: Ser referenciado por Item de Ordem de Serviço.
- **O que não faz**: Não define o custo — isso é o valor no Item de Ordem de Serviço.
- **Aggregate Root**: Sim — entidade de **Referência** (D036).
- **Bounded Context proprietário**: `maintenance`
- **Principais relacionamentos**: Item de Ordem de Serviço (referenciado).
- **Eventos que publica**: `TipoDeServicoCadastrado` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: nome único por tenant.
- **Regras de negócio associadas**: D001, D005/D006.
- **Estados**: `Ativo` / `Inativo`.
- **Auditoria**: D007.
- **Linha do tempo**: cadastro, alterações.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: frequência por tipo de serviço.
- **Documentos canônicos relacionados**: Nenhum.
- **Evoluções futuras previstas**: Nenhuma prevista.
- **Dependências obrigatórias**: Nenhuma.
- **Dependências proibidas**: Cliente, CT-e, Financeiro, Viagem.
- **Dono da Timeline**: Aggregate Tipo de Serviço (este próprio).
- **Capacidade Offline**: Consulta Offline.

## Aprovação de Custo

- **Objetivo**: Registro formal da decisão de um Gestor sobre um custo de OS acima da alçada.
- **Responsabilidades**: Guardar decisão (aprovado/rejeitado), justificativa, ator.
- **O que não faz**: Não substitui a transição de estado da OS — é o registro que a acompanha.
- **Aggregate Root**: Não — parte do agregado Ordem de Serviço.
- **Bounded Context proprietário**: `maintenance`
- **Principais relacionamentos**: Ordem de Serviço (N:1).
- **Eventos que publica**: Nenhum diretamente — a transição já é coberta por
  `OrdemServicoAprovacaoPendente`/`OrdemServicoConcluida`.
- **Eventos que consome**: Nenhum.
- **Invariantes**: toda Aprovação de Custo pertence a exatamente uma OS.
- **Regras de negócio associadas**: D007, D010 (decisão explícita, nunca implícita).
- **Estados**: Não aplicável — registro pontual.
- **Auditoria**: D007.
- **Linha do tempo**: parte da OS.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Sim, justificativa da decisão (D023).
- **KPIs relacionados**: tempo médio de aprovação.
- **Documentos canônicos relacionados**: `003-MANUTENCAO.md`.
- **Evoluções futuras previstas**: alçada configurável por tenant.
- **Dependências obrigatórias**: Ordem de Serviço.
- **Dependências proibidas**: Cliente, CT-e, Financeiro, Viagem.
- **Dono da Timeline**: Aggregate Ordem de Serviço.
- **Capacidade Offline**: Não.

## Checklist

- **Objetivo**: Registrar a verificação estruturada de um veículo/carga num ponto de controle
  (saída, retorno, oficina, carregamento, descarga, ou periódica administrativa) e formalizar sua
  aprovação ou reprovação (ver [`../product/GLOSSARY.md`](../product/GLOSSARY.md)).
- **Responsabilidades**: Coletar respostas item a item contra um conjunto de itens de verificação;
  decidir Aprovado/Reprovado; gatilhar o efeito correspondente na entidade referenciada (libera
  `AGUARDANDO_CHECKLIST → LIBERADA` na Viagem quando `TIPO = MOTORISTA_SAIDA`; bloqueia conclusão de
  Ordem de Serviço quando `TIPO = OFICINA`). Máquina de estados canônica em
  [`../flows/007-CHECKLIST.md`](../flows/007-CHECKLIST.md) (D035).
- **O que não faz**: Não decide por si só o que é "item crítico" fora do próprio registro do item
  (sem um "Modelo de Checklist" com aprovação/versionamento próprios nesta fundação — cada item
  carrega sua própria flag `crítico`, deliberadamente simples); não altera o estado de Viagem/Ordem
  de Serviço diretamente — publica o evento correspondente, quem aplica a transição é o dono da
  entidade referenciada (mesmo princípio de D116, `tracking` é observacional).
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `maintenance`
- **Principais relacionamentos**: Viagem ou Ordem de Serviço (referência polimórfica — `TIPO_
  REFERENCIA`/`REFERENCIA_ID`, mesmo padrão de Anexo/Comentário, D024/D023); Veículo Tracionador,
  Motorista (referenciados por ID, capturados no momento da criação — não ressincronizam, mesmo
  princípio de snapshot da Viagem, D038); Item de Checklist (parte do agregado, não entidade própria
  nesta fundação — ver "O que não faz").
- **Eventos que publica**: `ChecklistIniciado`, `ChecklistConcluido`, `ChecklistAprovado`,
  `ChecklistReprovado` (já catalogados em [`../product/EVENT_MAP.md`](../product/EVENT_MAP.md)).
- **Eventos que consome**: Nenhum — reage ao estado da entidade referenciada, não a eventos de
  outros bounded contexts (mesma disciplina de D105: interpretar estado, não side-effect de evento).
- **Invariantes**: um Checklist `Aprovado`/`Reprovado` nunca é reaberto — uma reprovação sempre gera
  um novo registro `Pendente` referenciando o reprovado, nunca reescreve o original (mesmo princípio
  de D017/D018 aplicado à própria entidade, não só ao histórico).
- **Regras de negócio associadas**: D015–D018 (máquina de estados + histórico).
- **Estados**: Ver `007-CHECKLIST.md` (fonte canônica, D035) — `Pendente → Em Preenchimento →
  Concluído → {Aprovado, Reprovado}`.
- **Auditoria**: D007 — observação obrigatória em `Reprovado`.
- **Linha do tempo (Timeline Universal)**: sim, na Viagem/Ordem de Serviço referenciada.
- **Anexos suportados**: foto de item reprovado (D024).
- **Comentários suportados**: Não nesta fundação — a observação da reprovação já cumpre esse papel.
- **KPIs relacionados**: taxa de reprovação por tipo, tempo médio de preenchimento.
- **Documentos canônicos relacionados**: `007-CHECKLIST.md`.
- **Evoluções futuras previstas**: Modelo de Checklist configurável por tenant (itens/pesos/
  criticidade versionados), hoje fora de escopo (ver "O que não faz").
- **Dependências obrigatórias**: Veículo Tracionador; Viagem ou Ordem de Serviço (a referência).
- **Dependências proibidas**: Cliente, CT-e, Financeiro (mesmo isolamento de Ordem de Serviço acima).
- **Dono da Timeline**: Aggregate Checklist (este próprio), consumido pela Timeline do referenciado.
- **Capacidade Offline**: Sim, para `TIPO ∈ {MOTORISTA_SAIDA, MOTORISTA_RETORNO, CARREGAMENTO,
  DESCARGA}` (preenchido pelo app do motorista, mesmo padrão de D039) — não modelado nesta fundação
  (o preenchimento aqui é sempre síncrono via API; sincronização offline é escopo de `mobile`).
