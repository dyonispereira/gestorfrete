# 002 — Operação

Entidades do núcleo operacional do GestorFrete, em torno da Viagem — o aggregate root mais
importante do sistema. Template oficial definido em [`README.md`](./README.md) — este arquivo foi
escrito com as 18 primeiras seções do template, antes dos 4 campos adicionados a partir de
`003-frota.md` (ver nota de inconsistência pendente em `README.md`).
Ver [`ENTITY_CATALOG.md`](./ENTITY_CATALOG.md) para o índice completo desta categoria.

---

## Viagem

- **Objetivo**: Núcleo do sistema — representa o transporte de uma carga de uma origem a um ou mais
  destinos, do planejamento ao encerramento financeiro pleno.
- **Responsabilidades**: Orquestrar Entregas, Ocorrências e Romaneio; manter as três dimensões de
  status (Operacional/Fiscal/Financeiro, D020) e o status composto `ENCERRADA` (D019); ser a raiz do
  agregado central do sistema.
- **O que não faz**: Não emite documento fiscal sozinha (delega a `documents`); não processa
  pagamento (delega a `financial`); não calcula rota (delega a `routing`).
- **Aggregate Root**: Sim — o aggregate root mais importante do sistema (ver `AGGREGATES.md`, a ser
  escrito).
- **Bounded Context proprietário**: `freight`
- **Principais relacionamentos**: Motorista, Veículo Tracionador, Implemento, Cliente
  (referenciados por ID, D033/D034); Entrega, Ocorrência, Romaneio, Alocação de Recurso da Viagem
  (filhos do agregado).
- **Eventos que publica**: `ViagemCriada`, `ViagemDespachada`, `ColetaRealizada`,
  `EntregaRealizada`, `OcorrenciaRegistrada`, `ViagemReatribuida`, `ViagemConcluida`,
  `ViagemInterrompida`, `ViagemCancelada`, `ViagemEncerrada` — todos já catalogados em
  [`../product/EVENT_MAP.md`](../product/EVENT_MAP.md).
- **Eventos que consome**: `ChecklistReprovado` (publicado por `maintenance`).
- **Invariantes**: uma Viagem deve possuir exatamente um Veículo Tracionador ativo por vez (exemplo
  oficial registrado para `INVARIANTS.md`); `ENCERRADA` nunca é atingida sem a convergência das três
  dimensões (D019); lista completa em `INVARIANTS.md` (a ser escrito).
- **Regras de negócio associadas**: D015–D021 (máquina de estados, histórico, tri-status), D033/D034
  (Viagem pertence exclusivamente a `freight`).
- **Estados**: Status Operacional, Status Fiscal, Status Financeiro e o status composto `ENCERRADA`
  — detalhados em [`../flows/002-VIAGEM.md`](../flows/002-VIAGEM.md) (D035, fonte canônica).
- **Auditoria**: D007, com volume de transições maior que qualquer outra entidade do sistema.
- **Linha do tempo (Timeline Universal)**: a mais rica do sistema — ver `002-VIAGEM.md`,
  Capacidades Transversais.
- **Anexos suportados**: foto de avaria, foto de canhoto físico, XML/PDF fiscal (D024).
- **Comentários suportados**: Sim (D023).
- **KPIs relacionados**: praticamente todos os indicadores operacionais e financeiros do sistema —
  ver `002-VIAGEM.md`, Indicadores Gerados.
- **Documentos canônicos relacionados**: `002-VIAGEM.md` (D035 — fonte canônica do ciclo da
  viagem).
- **Evoluções futuras previstas**: alocação sugerida por IA; origem via Marketplace (ver
  [`../product/VISION.md`](../product/VISION.md)).
- **Snapshot Histórico (D038)**: a Viagem guarda uma fotografia dos dados relevantes no momento em
  que foram usados — nome do Motorista, placa do Veículo Tracionador, dados do Cliente, valor do
  frete (Receita Prevista) e a Tabela de Preço aplicada — mesmo que os cadastros de origem mudem
  depois. Sem isso, um relatório histórico de uma viagem de anos atrás mudaria de conteúdo se o
  motorista fosse renomeado ou a tabela de preço fosse revisada hoje, o que é inaceitável para
  auditoria.

## Entrega

- **Objetivo**: Representa uma parada de entrega dentro de uma Viagem (suporta multi-drop).
- **Responsabilidades**: Rastrear conferência, Canhoto e estado terminal (`Concluída`/`Devolvida`/
  `Cancelada`) de uma parada específica.
- **O que não faz**: Não existe fora de uma Viagem; não decide sozinha o Status Operacional da
  Viagem — a Viagem consolida o estado de todas as suas Entregas.
- **Aggregate Root**: Não — parte do agregado Viagem.
- **Bounded Context proprietário**: `freight`
- **Principais relacionamentos**: Viagem (N:1); Canhoto (1:1, quando concluída); Ocorrência (1:N,
  quando aplicável); Janela de Entrega (1:1).
- **Eventos que publica**: `EntregaRealizada`, `EntregaRecusada`, `ReentregaAgendada` (já
  catalogados).
- **Eventos que consome**: Nenhum.
- **Invariantes**: uma Entrega só atinge `Concluída` com Canhoto associado; uma Viagem só avança
  para `FINALIZADA` quando todas as suas Entregas estão em estado terminal (já registrado em
  `002-VIAGEM.md`).
- **Regras de negócio associadas**: D015/D016.
- **Estados**: `Pendente` / `Concluída` / `Recusada` / `Devolvida` / `Cancelada`.
- **Auditoria**: D007.
- **Linha do tempo**: parte da timeline da Viagem.
- **Anexos suportados**: foto do canhoto, foto de avaria (D024).
- **Comentários suportados**: Sim, ligado a ocorrência de recusa (D023).
- **KPIs relacionados**: taxa de devolução/reentrega.
- **Documentos canônicos relacionados**: `002-VIAGEM.md`.
- **Evoluções futuras previstas**: fluxo próprio de Devolução, quando o volume justificar (já
  antecipado em `002-VIAGEM.md`, Requisitos futuros).

## Coleta

- **Objetivo**: Representa o ato de retirar a carga na origem, abrindo a execução da Viagem (ver
  [`../product/GLOSSARY.md`](../product/GLOSSARY.md)).
- **Responsabilidades**: Registrar hora, local e conferência da carga coletada.
- **O que não faz**: Não é uma entidade com ciclo de vida independente — é um marco dentro do ciclo
  da Viagem.
- **Aggregate Root**: Não — parte do agregado Viagem (registro de marco, não entidade rica).
- **Bounded Context proprietário**: `freight`
- **Principais relacionamentos**: Viagem (N:1).
- **Eventos que publica**: `ColetaRealizada` (já catalogado).
- **Eventos que consome**: Nenhum.
- **Invariantes**: uma Coleta só ocorre com a Viagem em `EM_DESLOCAMENTO` ou `CARREGANDO`.
- **Regras de negócio associadas**: D015/D016.
- **Estados**: Não aplicável — marco pontual, sem ciclo de vida próprio.
- **Auditoria**: D007.
- **Linha do tempo**: parte da timeline da Viagem.
- **Anexos suportados**: foto da carga na coleta (D024).
- **Comentários suportados**: Sim (D023).
- **KPIs relacionados**: tempo entre início de deslocamento e coleta.
- **Documentos canônicos relacionados**: `002-VIAGEM.md`.
- **Evoluções futuras previstas**: Nenhuma isolada.

## Ocorrência

- **Objetivo**: Registra qualquer imprevisto relevante ocorrido durante uma Viagem (atraso, avaria,
  pane, sinistro).
- **Responsabilidades**: Guardar tipo, descrição e evidência; ser o elo entre a Viagem e fluxos de
  exceção (Manutenção, Financeiro).
- **O que não faz**: Não decide sozinha a transição da Viagem para `INTERROMPIDA` — essa é uma
  decisão do Gestor Operacional, apenas informada pela Ocorrência.
- **Aggregate Root**: Não — parte do agregado Viagem.
- **Bounded Context proprietário**: `freight`
- **Principais relacionamentos**: Viagem (N:1); pode originar uma Ordem de Serviço (referência
  cruzada por evento, nunca por posse — D033/D034).
- **Eventos que publica**: `OcorrenciaRegistrada`, `AvariaRegistrada` (já catalogados).
- **Eventos que consome**: Nenhum.
- **Invariantes**: toda Ocorrência pertence a exatamente uma Viagem.
- **Regras de negócio associadas**: D015/D016, D007.
- **Estados**: `Aberta` / `Resolvida`.
- **Auditoria**: D007.
- **Linha do tempo**: parte da timeline da Viagem; também aparece na timeline da OS gerada, quando
  aplicável.
- **Anexos suportados**: foto, obrigatória em Avaria (D024).
- **Comentários suportados**: Sim (D023).
- **KPIs relacionados**: taxa de ocorrências por viagem.
- **Documentos canônicos relacionados**: `002-VIAGEM.md`.
- **Evoluções futuras previstas**: categorização automática por IA.

## Romaneio

- **Objetivo**: Lista detalhada dos itens/volumes de uma carga, anexada ao CT-e (ver
  [`../product/GLOSSARY.md`](../product/GLOSSARY.md)).
- **Responsabilidades**: Agrupar Item de Carga; usado na conferência de coleta e entrega.
- **O que não faz**: Não substitui o CT-e, o documento fiscal formal.
- **Aggregate Root**: Não — parte do agregado Viagem.
- **Bounded Context proprietário**: `freight`
- **Principais relacionamentos**: Viagem (1:1, ou 1:N em multi-carga); Item de Carga (1:N).
- **Eventos que publica**: Nenhum diretamente.
- **Eventos que consome**: Nenhum.
- **Invariantes**: deve ter ao menos um Item de Carga.
- **Regras de negócio associadas**: D015/D016.
- **Estados**: Não aplicável.
- **Auditoria**: D007.
- **Linha do tempo**: parte da timeline da Viagem.
- **Anexos suportados**: foto do romaneio físico, quando aplicável (D024).
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: `002-VIAGEM.md`, [`../flows/009-FISCAL.md`](../flows/009-FISCAL.md)
  (referenciado pelo CT-e).
- **Evoluções futuras previstas**: OCR automático do romaneio físico.

## Item de Carga

- **Objetivo**: Linha de um Romaneio (item/volume específico).
- **Responsabilidades**: Guardar descrição, peso e quantidade.
- **O que não faz**: Não existe fora de um Romaneio.
- **Aggregate Root**: Não — parte do agregado Viagem (via Romaneio).
- **Bounded Context proprietário**: `freight`
- **Principais relacionamentos**: Romaneio (N:1).
- **Eventos que publica**: Nenhum.
- **Eventos que consome**: Nenhum.
- **Invariantes**: peso e quantidade devem ser maiores que zero.
- **Regras de negócio associadas**: D005/D006.
- **Estados**: Segue o Romaneio.
- **Auditoria**: D007.
- **Linha do tempo**: parte do Romaneio/Viagem.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: Nenhum.
- **Evoluções futuras previstas**: Nenhuma isolada.

## Canhoto

- **Objetivo**: Comprovante de entrega assinado pelo destinatário (ver
  [`../product/GLOSSARY.md`](../product/GLOSSARY.md)) — gatilho do faturamento.
- **Responsabilidades**: Guardar assinatura/foto; ligar-se à Entrega concluída.
- **O que não faz**: Não emite o Faturamento sozinho — apenas habilita a transição em
  [`../flows/005-FINANCEIRO.md`](../flows/005-FINANCEIRO.md).
- **Aggregate Root**: Não — parte do agregado Viagem (via Entrega).
- **Bounded Context proprietário**: `freight` — **correção de consistência**: o EVENT_MAP.md
  anterior listava `CanhotoRegistrado` sob `documents`; como o Canhoto é parte do agregado Viagem
  (D033/D034), o evento foi movido para a seção `freight` (ver nota em `EVENT_MAP.md`).
- **Principais relacionamentos**: Entrega (1:1).
- **Eventos que publica**: `CanhotoRegistrado` (já catalogado, reatribuído a `freight` nesta
  revisão).
- **Eventos que consome**: Nenhum.
- **Invariantes**: uma Entrega só é `Concluída` com Canhoto associado.
- **Regras de negócio associadas**: D015/D016; não recebe número funcional próprio (D029) — segue o
  número da Viagem a que pertence.
- **Estados**: `Pendente` / `Registrado`.
- **Auditoria**: D007.
- **Linha do tempo**: parte da timeline da Viagem/Entrega.
- **Anexos suportados**: foto do canhoto físico, assinatura digital (D024).
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: canhotos pendentes, tempo entre entrega e canhoto.
- **Documentos canônicos relacionados**: `002-VIAGEM.md`, `005-FINANCEIRO.md`.
- **Evoluções futuras previstas**: OCR automático (ver
  [`../flows/010-APP_MOTORISTA.md`](../flows/010-APP_MOTORISTA.md)).

## Contrato de Frete

- **Objetivo**: Acordo comercial entre Cliente e transportadora que baliza as condições de fretes
  futuros (preço, prazo, SLA).
- **Responsabilidades**: Ser referenciado por Cotação/Viagem para aplicar condições
  pré-negociadas.
- **O que não faz**: Não substitui a Tabela de Preço — o contrato pode referenciar uma tabela
  específica.
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `freight`
- **Principais relacionamentos**: Cliente (N:1); Tabela de Preço (referenciada).
- **Eventos que publica**: `ContratoDeFreteCriado`, `ContratoDeFreteEncerrado` (novos).
- **Eventos que consome**: Nenhum.
- **Invariantes**: vigência válida (data de fim posterior à data de início).
- **Regras de negócio associadas**: D001, D005/D006.
- **Estados**: `Ativo` / `Encerrado`.
- **Auditoria**: D007.
- **Linha do tempo**: criação, viagens executadas sob o contrato (por referência).
- **Anexos suportados**: contrato assinado (D024).
- **Comentários suportados**: Sim, negociação (D023).
- **KPIs relacionados**: volume de fretes por contrato.
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: renovação automática.

## Cotação

- **Objetivo**: Valor calculado para uma Solicitação de Frete antes da aprovação — origem de uma
  Viagem.
- **Responsabilidades**: Aplicar Tabela de Preço/Contrato às condições concretas (origem, destino,
  carga); registrar a Receita Prevista (ver `005-FINANCEIRO.md`).
- **O que não faz**: Não é a Viagem em si — a Viagem só existe após a Cotação ser aprovada.
- **Aggregate Root**: Sim (até ser aprovada e originar uma Viagem, quando passa a ser referenciada
  por ela).
- **Bounded Context proprietário**: `freight`
- **Principais relacionamentos**: Cliente, Tabela de Preço, Contrato de Frete (referenciados); Item
  de Cotação (1:N); Viagem (0..1, após aprovação).
- **Eventos que publica**: `CotacaoCriada`, `CotacaoAprovada`, `CotacaoRecusada` (novos).
- **Eventos que consome**: Nenhum.
- **Invariantes**: valor total maior que zero; uma Cotação `Aprovada` não pode ser alterada — gera
  uma nova Cotação (mesmo princípio de imutabilidade pós-terminal já usado em outros fluxos).
- **Regras de negócio associadas**: D001, D005/D006, D017/D018 (histórico de revisão de valor antes
  da aprovação).
- **Estados**: `Rascunho` / `Aprovada` / `Recusada` / `Expirada`.
- **Auditoria**: D007.
- **Linha do tempo**: criação, revisões, aprovação.
- **Anexos suportados**: proposta em PDF (D024).
- **Comentários suportados**: Sim, negociação (D023).
- **KPIs relacionados**: taxa de conversão de cotação em viagem.
- **Documentos canônicos relacionados**: `005-FINANCEIRO.md` (Receita Prevista).
- **Evoluções futuras previstas**: simulador de frete self-service (ver
  [`../product/PRODUCT_MAP.md`](../product/PRODUCT_MAP.md)).

## Item de Cotação

- **Objetivo**: Linha de uma Cotação (ex: valor do frete, pedágio previsto, taxas).
- **Responsabilidades**: Compor o valor total da Cotação.
- **O que não faz**: Não existe fora de uma Cotação.
- **Aggregate Root**: Não.
- **Bounded Context proprietário**: `freight`
- **Principais relacionamentos**: Cotação (N:1).
- **Eventos que publica**: Nenhum.
- **Eventos que consome**: Nenhum.
- **Invariantes**: valor maior ou igual a zero.
- **Regras de negócio associadas**: D005/D006.
- **Estados**: Segue a Cotação.
- **Auditoria**: D007.
- **Linha do tempo**: parte da Cotação.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: Nenhum.
- **Evoluções futuras previstas**: Nenhuma isolada.

## Solicitação de Frete

- **Objetivo**: Registro inicial da necessidade de transporte, antes de qualquer cálculo de valor —
  gatilho inicial de `002-VIAGEM.md`.
- **Responsabilidades**: Guardar origem, destino(s), tipo de carga e prazo desejado.
- **O que não faz**: Não calcula valor — isso é a Cotação.
- **Aggregate Root**: Sim (até originar uma Cotação).
- **Bounded Context proprietário**: `freight`
- **Principais relacionamentos**: Cliente (N:1); Cotação (0..1, após processamento).
- **Eventos que publica**: `SolicitacaoDeFreteRegistrada` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: deve ter ao menos uma origem e um destino.
- **Regras de negócio associadas**: D005/D006.
- **Estados**: `Registrada` / `Cotada` / `Descartada`.
- **Auditoria**: D007.
- **Linha do tempo**: criação, cotação gerada.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Sim (D023).
- **KPIs relacionados**: tempo entre solicitação e cotação.
- **Documentos canônicos relacionados**: `002-VIAGEM.md`.
- **Evoluções futuras previstas**: originada automaticamente a partir do Marketplace (ver
  [`../product/VISION.md`](../product/VISION.md)).

## Janela de Entrega

- **Objetivo**: Intervalo de tempo combinado para uma entrega específica (ex: "entre 14h e 17h").
- **Responsabilidades**: Ser referenciada por uma Entrega para cálculo de SLA/atraso.
- **O que não faz**: Não substitui o SLA geral da Viagem — é específica de uma parada.
- **Aggregate Root**: Não — parte do agregado Viagem (via Entrega).
- **Bounded Context proprietário**: `freight`
- **Principais relacionamentos**: Entrega (1:1).
- **Eventos que publica**: Nenhum diretamente.
- **Eventos que consome**: Nenhum.
- **Invariantes**: hora final maior que hora inicial.
- **Regras de negócio associadas**: D005/D006.
- **Estados**: Não aplicável.
- **Auditoria**: D007.
- **Linha do tempo**: parte da Entrega.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: percentual de entregas dentro da janela combinada.
- **Documentos canônicos relacionados**: `002-VIAGEM.md`.
- **Evoluções futuras previstas**: renegociação de janela pelo Portal do Cliente.

## Ponto de Parada da Viagem

- **Objetivo**: Representa uma parada geográfica planejada da Viagem (coleta, entrega, posto,
  pedágio).
- **Responsabilidades**: Ordenar a sequência de paradas de uma Viagem multi-drop/multi-coleta.
- **O que não faz**: Não é a Posição de Veículo em tempo real (ver `008-rastreamento.md`, a ser
  escrito) — é planejamento, não execução.
- **Aggregate Root**: Não — parte do agregado Viagem.
- **Bounded Context proprietário**: `freight`
- **Principais relacionamentos**: Viagem (N:1); pode originar uma Entrega ou Coleta.
- **Eventos que publica**: Nenhum diretamente.
- **Eventos que consome**: Nenhum.
- **Invariantes**: a sequência (ordem) é única dentro da mesma Viagem.
- **Regras de negócio associadas**: D005/D006.
- **Estados**: `Planejado` / `Concluído`.
- **Auditoria**: D007.
- **Linha do tempo**: parte da Viagem.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: aderência ao planejamento (planejado vs. real).
- **Documentos canônicos relacionados**: `002-VIAGEM.md`, [`../flows/008-RASTREAMENTO.md`](../flows/008-RASTREAMENTO.md).
- **Evoluções futuras previstas**: roteirização automática (Mapbox).

## Alocação de Recurso da Viagem

- **Objetivo**: Registra qual Motorista, Veículo Tracionador e Implemento estão associados a uma
  Viagem em um dado momento — inclusive o histórico de reatribuições.
- **Responsabilidades**: Suportar Troca de Cavalo/Troca de Motorista sem perder o histórico de quem
  executou cada trecho.
- **O que não faz**: Não decide a reatribuição sozinha — é o registro de uma decisão do Gestor
  Operacional.
- **Aggregate Root**: Não — parte do agregado Viagem.
- **Bounded Context proprietário**: `freight`
- **Principais relacionamentos**: Viagem (N:1); Motorista, Veículo Tracionador, Implemento
  (referenciados por ID).
- **Eventos que publica**: `ViagemReatribuida` (já catalogado).
- **Eventos que consome**: Nenhum.
- **Invariantes**: exatamente uma Alocação de Recurso `Vigente` por Viagem em cada instante (nunca
  duas simultâneas) — reforça o invariante oficial "uma Viagem deve possuir exatamente um Veículo
  Tracionador ativo".
- **Regras de negócio associadas**: D017/D018 (histórico append-only de reatribuições).
- **Estados**: `Vigente` / `Substituída`.
- **Auditoria**: D007.
- **Linha do tempo**: parte da timeline da Viagem.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Sim, motivo da troca (D023).
- **KPIs relacionados**: taxa de reatribuição por viagem.
- **Documentos canônicos relacionados**: `002-VIAGEM.md`.
- **Evoluções futuras previstas**: sugestão de realocação por IA.
