# 002 — Viagem

## Objetivo

Documentar a vida útil completa de uma Viagem — da solicitação do frete ao encerramento e consumo
por BI — incluindo todos os caminhos alternativos e de exceção que uma operação real de
transportadora enfrenta. Este é o fluxo mais central do GestorFrete: `freight` é o core domain (ver
[`../architecture/ddd.md`](../architecture/ddd.md)), e praticamente todo outro fluxo de negócio
(Financeiro, Abastecimento, Checklist, Rastreamento, Fiscal, App Motorista) acontece **em função**
do estado de uma Viagem. Por isso este documento é a referência canônica da máquina de estados de
Viagem — os demais fluxos a referenciam, nunca a redefinem (ver [`INDEX.md`](./INDEX.md),
Convenções).

## Pré-condições

- Cliente (Embarcador) cadastrado.
- Tabela de Preço vigente para a rota/tipo de carga.
- Ao menos um Motorista e um Veículo aptos (habilitação/documentação em dia) existem no tenant.

## Gatilho inicial

Uma Solicitação de frete é criada — por um Cliente via Portal do Cliente/Marketplace (fases
futuras), pelo Comercial a partir de um contrato fechado, ou pelo Gestor Operacional diretamente
para operação recorrente.

## Máquina de Estados — Viagem

Por D020, Viagem possui **três dimensões de status independentes e coexistentes** — Operacional,
Fiscal e Financeiro —, cada uma com sua própria máquina de estados evoluindo em paralelo, mais um
**status composto** (`ENCERRADA`) derivado da convergência das três (D019). A maioria dos TMS do
mercado considera a viagem terminada quando o caminhão retorna; o GestorFrete considera encerrada
apenas quando as três dimensões convergem — inclusive quando o dinheiro efetivamente entra.

### Status Operacional

#### Estados

`RASCUNHO`, `PLANEJADA`, `AGUARDANDO_CHECKLIST`, `LIBERADA`, `EM_DESLOCAMENTO`, `CARREGANDO`,
`EM_TRANSITO`, `EM_ENTREGA`, `FINALIZADA` — fluxo principal. `INTERROMPIDA`, `CANCELADA` — estados
de exceção, alcançáveis a partir de múltiplos pontos do fluxo principal.

```
RASCUNHO → PLANEJADA → AGUARDANDO_CHECKLIST → LIBERADA → EM_DESLOCAMENTO → CARREGANDO
                                                                                 │
                                                                                 ▼
                                            FINALIZADA ◄── EM_ENTREGA ◄──► EM_TRANSITO

  (a partir de qualquer estado entre EM_DESLOCAMENTO e EM_ENTREGA)
       │
       ▼
  INTERROMPIDA ──(retoma o estado anterior)──► [estado de onde interrompeu]
       │
       └──(perda definitiva)──► CANCELADA

  (a partir de RASCUNHO, PLANEJADA, AGUARDANDO_CHECKLIST ou LIBERADA)
       └──(cancelamento antes do início)──► CANCELADA
```

**Sub-ciclo de múltiplas entregas (multi-drop)**: para viagens com mais de um ponto de entrega,
`EM_TRANSITO` e `EM_ENTREGA` se alternam uma vez por parada
(`EM_TRANSITO → EM_ENTREGA → EM_TRANSITO → EM_ENTREGA → ...`) até a última parada ser concluída.
Isso **não** é uma transição inválida — é o comportamento esperado do sub-ciclo. A Viagem só avança
para `FINALIZADA` quando **todas** as Entregas (sub-entidade, uma por parada) estão em estado
terminal: `Concluída`, `Devolvida` ou `Cancelada`.

#### Transições válidas

| De | Para | Gatilho |
|---|---|---|
| `RASCUNHO` | `PLANEJADA` | Cotação aprovada e Motorista + Veículo + Carreta + Carga atribuídos |
| `PLANEJADA` | `AGUARDANDO_CHECKLIST` | Viagem programada para a data/rota definida |
| `AGUARDANDO_CHECKLIST` | `LIBERADA` | Checklist de saída aprovado (ver [`007-CHECKLIST.md`](./007-CHECKLIST.md), quando escrito) |
| `LIBERADA` | `EM_DESLOCAMENTO` | Motorista inicia o deslocamento até o ponto de coleta |
| `EM_DESLOCAMENTO` | `CARREGANDO` | Motorista chega à origem e inicia o carregamento |
| `CARREGANDO` | `EM_TRANSITO` | Carga conferida (romaneio) e viagem segue para o(s) destino(s) |
| `EM_TRANSITO` | `EM_ENTREGA` | Motorista chega a um ponto de entrega |
| `EM_ENTREGA` | `EM_TRANSITO` | Entrega da parada concluída, há mais paradas pendentes (multi-drop) |
| `EM_ENTREGA` | `FINALIZADA` | Última Entrega atinge estado terminal, canhotos registrados |
| `EM_DESLOCAMENTO`/`CARREGANDO`/`EM_TRANSITO`/`EM_ENTREGA` | `INTERROMPIDA` | Pane, sinistro ou ocorrência grave |
| `INTERROMPIDA` | *(estado de onde interrompeu)* | Ocorrência resolvida, viagem retoma |
| `INTERROMPIDA` | `CANCELADA` | Perda definitiva (ex: sinistro com perda total) |
| `RASCUNHO`/`PLANEJADA`/`AGUARDANDO_CHECKLIST`/`LIBERADA` | `CANCELADA` | Cancelamento antes do início do deslocamento |

**Reconciliado (V1 Operational Hardening, Parte 2)**: `LIBERADA→EM_DESLOCAMENTO` (despacho) e
`EM_ENTREGA→FINALIZADA` (encerramento) aceitam, opcionalmente, o hodômetro do Veículo no momento —
gravado como leitura de fronteira em `leituras_hodometro` (`fleet`, D034, ver
[`003-frota.md`](../domain/003-frota.md)), nunca uma segunda fonte da verdade. Com as duas leituras,
`Trip.km_rodado = leitura_encerramento − leitura_despacho`; sem alguma delas, fica indisponível —
nunca estimado.

#### Transições inválidas (normativas)

- **Não é permitido** ir de `RASCUNHO` diretamente para `EM_TRANSITO` — a viagem precisa passar por
  `PLANEJADA`, `AGUARDANDO_CHECKLIST` e `LIBERADA`.
- **Não é permitido** finalizar uma viagem (`→ FINALIZADA`) sem encerrar o checklist obrigatório e
  sem que todas as Entregas estejam em estado terminal — **salvo** encerramento administrativo
  forçado por Gestor Operacional ou Administrador SaaS, sempre com justificativa auditada (exceção
  documentada, não silenciosa).
- **Não é permitido** ir de `LIBERADA` diretamente para `EM_ENTREGA`, pulando
  `EM_DESLOCAMENTO`/`CARREGANDO`/`EM_TRANSITO` — o caso de origem e destino coincidirem (viagem
  local) é tratado como regra de negócio própria a especificar, não como atalho genérico da máquina
  de estados.
- **Não é permitido** reabrir uma viagem `FINALIZADA` para qualquer estado anterior — qualquer
  correção pós-encerramento gera um novo registro (ocorrência retroativa/nota de ajuste), nunca
  altera o histórico já fechado (consistente com D007 — auditoria e histórico nunca são reescritos).
- **Não é permitido** mover para `CANCELADA` a partir de `EM_TRANSITO`, `EM_ENTREGA`, `CARREGANDO`
  ou `EM_DESLOCAMENTO` diretamente — obrigatoriamente passa por `INTERROMPIDA` primeiro, porque
  cancelar uma viagem com carga em curso exige tratativa (o que fazer com a carga), não é um
  cancelamento simples.
- **Não é permitido** avançar de `AGUARDANDO_CHECKLIST` para `LIBERADA` sem um registro de checklist
  aprovado associado.

### Status Fiscal

Ciclo de vida dos documentos fiscais vinculados à viagem — referência canônica em
[`009-FISCAL.md`](./009-FISCAL.md) (CT-e, MDF-e, CIOT, cancelamentos e carta de correção); aqui
apenas o suficiente para a convergência de `ENCERRADA`.

```
PENDENTE → CTE_EMITIDO → MDFE_EMITIDO → MDFE_ENCERRADO
               │
               └──(cancelamento do CT-e)──► CTE_CANCELADO ──(reemissão)──► PENDENTE
```

| De | Para | Gatilho |
|---|---|---|
| `PENDENTE` | `CTE_EMITIDO` | CT-e emitido com sucesso na SEFAZ (`ViagemDespachada` dispara a emissão) |
| `CTE_EMITIDO` | `MDFE_EMITIDO` | MDF-e emitido consolidando o(s) CT-e da viagem |
| `MDFE_EMITIDO` | `MDFE_ENCERRADO` | MDF-e encerrado na SEFAZ ao concluir a última entrega |
| `CTE_EMITIDO` | `CTE_CANCELADO` | CT-e cancelado antes da emissão do MDF-e |
| `CTE_CANCELADO` | `PENDENTE` | Reemissão de um novo CT-e |

**Não é permitido** emitir MDF-e (`→ MDFE_EMITIDO`) sem ao menos um CT-e em `CTE_EMITIDO`. **Não é
permitido** encerrar o MDF-e (`→ MDFE_ENCERRADO`) com o Status Operacional ainda anterior a
`EM_ENTREGA` na última parada.

### Status Financeiro

Ciclo de vida do faturamento e recebimento da viagem — referência canônica em
[`005-FINANCEIRO.md`](./005-FINANCEIRO.md), que também define a separação entre Receita/Custo
Previsto e Realizado desta viagem (Margem Prevista, Margem Realizada, Desvio Financeiro).

```
AGUARDANDO_FATURAMENTO → FATURADA → AGUARDANDO_RECEBIMENTO → RECEBIDA
```

| De | Para | Gatilho |
|---|---|---|
| `AGUARDANDO_FATURAMENTO` | `FATURADA` | Canhoto(s) registrado(s) e CT-e emitido — condições para faturar atendidas |
| `FATURADA` | `AGUARDANDO_RECEBIMENTO` | Cobrança enviada ao cliente (automático, na própria transição de faturamento) |
| `AGUARDANDO_RECEBIMENTO` | `RECEBIDA` | Pagamento do cliente confirmado |

**Não é permitido** faturar (`→ FATURADA`) sem ao menos um Canhoto registrado. **Não é permitido**
pular `AGUARDANDO_RECEBIMENTO` e ir direto de `FATURADA` para `RECEBIDA` — o recebimento é sempre um
evento próprio, nunca implícito no faturamento (mesmo quando o intervalo entre os dois for mínimo).

### Status Composto — `ENCERRADA` (D019)

`ENCERRADA` **nunca** é atribuída diretamente por um usuário — é derivada automaticamente quando as
três dimensões convergem para seus estados terminais:

```
Status Operacional = FINALIZADA
        +
Status Fiscal       = MDFE_ENCERRADO
        +
Status Financeiro   = RECEBIDA
        ═══════════════════════════►  ENCERRADA
```

Assim que a última das três dimensões atinge seu estado terminal, o sistema insere automaticamente
a transição para `ENCERRADA` no histórico (D018) — não existe ação de usuário "encerrar viagem".
Isso é o que permite medir o **ciclo financeiro real da viagem** (do `RASCUNHO` até o dinheiro
efetivamente recebido), não apenas o ciclo operacional.

**Não é permitido** setar `ENCERRADA` manualmente por nenhum perfil, incluindo Administrador SaaS —
correções excepcionais (ex: viagem que nunca será paga, baixa por perda) são tratadas como uma
regra de negócio própria de baixa financeira em [`005-FINANCEIRO.md`](./005-FINANCEIRO.md), nunca
como uma transição forçada desta máquina de estados.

### Histórico de Transições

Por D017/D018, nenhuma das quatro dimensões acima jamais sobrescreve um valor de status — toda
mudança insere um novo registro em `ViagemStatusHistory`:

| Campo | Descrição |
|---|---|
| `id` | Identificador do registro de histórico |
| `viagem_id` | Viagem a que pertence |
| `dimensao` | `OPERACIONAL`, `FISCAL`, `FINANCEIRO` ou `COMPOSTO` |
| `status` | O novo valor de status |
| `usuario` | Quem realizou a transição (ou `sistema`, para automáticas) |
| `origem` | Onde a transição foi disparada (`app_motorista`, `portal_gestor`, `webhook_sefaz`, etc.) |
| `data_hora` | Timestamp da transição (UTC — D003) |
| `observacao` | Obrigatória nas transições de exceção (`INTERROMPIDA`, `CANCELADA`, `CTE_CANCELADO`) |
| `latitude` / `longitude` | Posição no momento da transição, quando disponível (predominantemente nas transições de Status Operacional originadas no app do motorista) |

> A coluna `dimensao` estende o exemplo original de D018 (desenhado antes da decisão de três
> dimensões coexistentes, D020, tomada na mesma revisão) para não perder o histórico de nenhuma das
> quatro máquinas de estado da Viagem em uma única tabela coesa.

Esse histórico é a fonte de dados para: auditoria completa, BI (linha do tempo de qualquer viagem),
IA (aprendizado sobre duração real de cada etapa), SLA (cálculo de tempo em cada status) e
produtividade (tempo parado vs. em execução).

## Fluxo principal

Visão geral da cadeia completa:

```
Solicitação → Cotação → Aprovação → Programação → Motorista → Veículo → Carreta → Carga
  → Checklist → Início → GPS → Ocorrências → Abastecimentos → Pedágios
  → Entrega 1 → Entrega 2 → Entrega 3 (n paradas) → Canhotos
  → Faturamento → Recebimento → Encerramento → BI
```

Detalhado por fase, com o estado correspondente da Viagem entre colchetes:

1. **Solicitação** `[RASCUNHO]` — cliente, comercial ou gestor operacional registra a necessidade
   de transporte (origem, destino(s), tipo de carga).
2. **Cotação** `[RASCUNHO]` — valor calculado a partir da Tabela de Preço (`pricing`).
3. **Aprovação** `[RASCUNHO]` — cliente/comercial aprova a cotação; gera o Contrato de Frete.
4. **Programação** `[RASCUNHO]` — gestor operacional define data e rota.
5. **Motorista / 6. Veículo / 7. Carreta / 8. Carga** `[RASCUNHO → PLANEJADA]` — alocação dos
   recursos; a Viagem avança para `PLANEJADA` quando todos estão atribuídos.
6. **Checklist** `[PLANEJADA → AGUARDANDO_CHECKLIST → LIBERADA]` — checklist de saída executado e
   aprovado (ver [`007-CHECKLIST.md`](./007-CHECKLIST.md)).
7. **Início** `[LIBERADA → EM_DESLOCAMENTO]` — motorista inicia o deslocamento até a origem.
8. **GPS** `[contínuo, a partir de EM_DESLOCAMENTO]` — posição rastreada em tempo real (ver
   [`008-RASTREAMENTO.md`](./008-RASTREAMENTO.md)).
9. **Ocorrências** `[podem ocorrer a partir de LIBERADA]` — qualquer evento relevante registrado ao
   longo da viagem, sem necessariamente mudar o estado macro.
10. **Abastecimentos** `[predominantemente em EM_TRANSITO]` — ver
    [`006-ABASTECIMENTO.md`](./006-ABASTECIMENTO.md).
11. **Pedágios** `[predominantemente em EM_TRANSITO]` — custo automaticamente associado ao Centro de
    Custo da viagem.
12. **Entrega 1, 2, 3...** `[EM_TRANSITO ⇄ EM_ENTREGA, por parada]` — ciclo multi-drop descrito
    acima.
13. **Canhotos** `[a cada Entrega concluída → Status Fiscal pode avançar para MDFE_ENCERRADO na
    última parada]` — comprovante de entrega registrado (ver
    [`../product/GLOSSARY.md`](../product/GLOSSARY.md), "Canhoto").
14. **Faturamento** `[Status Financeiro: AGUARDANDO_FATURAMENTO → FATURADA]` — consumido por
    `financial` (ver [`005-FINANCEIRO.md`](./005-FINANCEIRO.md)).
15. **Recebimento** `[Status Financeiro: AGUARDANDO_RECEBIMENTO → RECEBIDA]` — quitação do valor
    faturado pelo cliente.
16. **Encerramento** `[Status Operacional: FINALIZADA — necessário mas não suficiente]` — viagem
    chega ao fim operacional; o encerramento **de fato** (`ENCERRADA`) só ocorre quando Fiscal e
    Financeiro também convergirem (D019, ver Status Composto acima).
17. **BI** `[consumidor terminal]` — dados da viagem, incluindo o `ViagemStatusHistory` completo,
    alimentam `analytics`, sem retroalimentar a Viagem.

## Fluxos alternativos

- **Viagem sem cotação prévia** (operação recorrente com contrato guarda-chuva já fechado): pula
  Cotação/Aprovação, começa direto em Programação.
- **Múltiplos pontos de coleta** (não apenas múltiplas entregas): o mesmo sub-ciclo de `CARREGANDO`
  pode se repetir antes de `EM_TRANSITO`, análogo ao sub-ciclo de entregas.
- **Troca de cavalo mecânico**: substituição do Veículo alocado, em qualquer estado de `PLANEJADA`
  até `EM_ENTREGA`, sem alterar o status da Viagem — gera `ViagemReatribuida` e auditoria.
- **Troca de motorista**: substituição do Motorista alocado, mesmas condições da troca de cavalo.
- **Carga recusada no destino**: tratada no nível da Entrega individual (não da Viagem) — a Entrega
  vai para `Recusada`, o que pode disparar Devolução ou Reentrega sem necessariamente interromper as
  demais entregas da mesma viagem multi-drop.

## Fluxos de exceção

- **Devolução**: cliente recusa a carga (total ou parcial) na entrega → Entrega marcada `Recusada`;
  gera uma nova Viagem vinculada do tipo devolução, ou segue para Reentrega conforme acordo
  comercial. A Viagem original só avança para `FINALIZADA` quando essa Entrega atingir um estado
  terminal (a devolução em si, não a recusa).
- **Sinistro**: acidente, roubo ou perda da carga → Viagem vai para `INTERROMPIDA`; se a perda for
  definitiva, avança para `CANCELADA` com Ocorrência crítica registrada e acionamento de seguro
  (`fleet`/fornecedor de seguro); se parcial/recuperável, pode retomar o estado anterior.
- **Pane (mecânica)**: veículo apresenta problema em rota → `INTERROMPIDA`; abre Ordem de Serviço
  emergencial (ver [`003-MANUTENCAO.md`](./003-MANUTENCAO.md)); ao ser resolvida (reparo no local ou
  troca de cavalo), retoma o estado anterior.
- **Troca de cavalo mecânico** *(como exceção, distinta do fluxo alternativo de substituição
  planejada)*: pane ou indisponibilidade obriga troca não planejada em rota — tratada dentro de
  `INTERROMPIDA`, retomando ao estado anterior após a troca.
- **Troca de motorista** *(exceção)*: mal súbito, jornada excedida ou outro impedimento em rota →
  mesma tratativa de `INTERROMPIDA` até a substituição ser efetivada.
- **Carga recusada**: ver Devolução — é o gatilho que leva à Devolução ou à Reentrega.
- **Cancelamento**: solicitado pelo cliente ou pela transportadora antes do início do deslocamento
  → `CANCELADA` direto; se a carga já estiver em curso, passa obrigatoriamente por `INTERROMPIDA`
  primeiro (ver Transições inválidas). Sempre com confirmação explícita (D010).
- **Reentrega**: Entrega falha por motivo não imputável ao destinatário recusar definitivamente
  (ausência no local, endereço incorreto) → nova tentativa agendada para a mesma Entrega, sem gerar
  nova Viagem; a Viagem permanece em `EM_ENTREGA` até a reentrega ser concluída ou definitivamente
  frustrada.
- **Avaria**: dano identificado na carga durante conferência (na coleta ou na entrega) → Ocorrência
  registrada com evidência (foto); pode levar à Devolução parcial sem necessariamente interromper a
  viagem inteira.
- **Atraso**: SLA de entrega estourado → não é um estado da Viagem, é uma condição temporal que
  gera Ocorrência e alerta (`notification_center`), sem interromper o fluxo.

## Eventos publicados

| Evento | Gerado quando |
|---|---|
| `ViagemCriada` | Viagem sai de nenhuma existência para `RASCUNHO` — já catalogado em [`../product/EVENT_MAP.md`](../product/EVENT_MAP.md) |
| `ViagemDespachada` | Transição `LIBERADA → EM_DESLOCAMENTO` — já catalogado |
| `ColetaRealizada` | Transição `EM_DESLOCAMENTO → CARREGANDO` concluída — já catalogado |
| `EntregaRealizada` | Uma Entrega individual atinge `Concluída` — já catalogado |
| `OcorrenciaRegistrada` | Qualquer Ocorrência é registrada, em qualquer estado — já catalogado |
| `ViagemReatribuida` | Troca de motorista/veículo, planejada ou por exceção — já catalogado |
| `ViagemConcluida` | Transição `EM_ENTREGA → FINALIZADA` — já catalogado |
| `ViagemInterrompida` | Transição para `INTERROMPIDA` (novo — ver [`../product/EVENT_MAP.md`](../product/EVENT_MAP.md)) |
| `ViagemCancelada` | Transição para `CANCELADA` (novo) |
| `EntregaRecusada` | Uma Entrega vai para `Recusada` (novo) |
| `ReentregaAgendada` | Nova tentativa de uma Entrega é agendada (novo) |
| `AvariaRegistrada` | Dano identificado na carga (novo) |
| `MDFeEncerrado` | Status Fiscal atinge `MDFE_ENCERRADO` (publicado por `documents` — novo) |
| `RecebimentoConfirmado` | Status Financeiro atinge `RECEBIDA` (publicado por `financial` — novo) |
| `ViagemEncerrada` | Status Composto atinge `ENCERRADA` — as três dimensões convergiram (novo) |

## Eventos consumidos

| Evento | Publicado por | Efeito na Viagem |
|---|---|---|
| `ChecklistReprovado` | `maintenance` | Bloqueia a transição `AGUARDANDO_CHECKLIST → LIBERADA` — já catalogado em `EVENT_MAP.md` |

## Permissões

| Etapa | Quem executa |
|---|---|
| Solicitação, Cotação, Aprovação | Comercial, Cliente (Portal do Cliente, fases futuras) |
| Programação, alocação de recursos, reatribuição | Gestor Operacional |
| Checklist | Motorista (execução), Mecânico/Analista de Frota (checklist de oficina, quando aplicável) |
| Início, GPS, Ocorrências, Abastecimentos, Entregas, Canhotos | Motorista (app mobile) |
| Cancelamento, encerramento administrativo forçado | Gestor Operacional; casos excepcionais, Administrador SaaS |
| Consulta somente leitura de toda a viagem | Auditor |

## Auditoria

Toda transição de estado da Viagem e de cada Entrega é registrada na trilha de auditoria (`audit`),
com ator, timestamp e — nas transições de exceção (`INTERROMPIDA`, `CANCELADA`, encerramento
forçado) — motivo obrigatório (D007).

## Notificações

- Motorista: viagem atribuída, checklist pendente, viagem liberada.
- Gestor Operacional: ocorrência registrada, viagem interrompida, checklist reprovado.
- Cliente: confirmação de coleta, confirmação de entrega, atraso identificado.
- Financeiro: viagem finalizada (gatilho para conferência de faturamento).

## Capacidades Transversais

1. **Timeline Universal** (D022): a mais rica do sistema — funde os três `ViagemStatusHistory`
   (Operacional/Fiscal/Financeiro), eventos de Checklist, Abastecimento, Ocorrência, Ordem de
   Serviço (quando gerada por pane) e Documento Fiscal, comentários e anexos, em uma única linha do
   tempo por viagem. Exemplo de leitura (ver também o exemplo original desta decisão em
   [`../product/DECISIONS.md`](../product/DECISIONS.md), D022): `08:00 Viagem criada → 08:20
   Checklist aprovado → 08:45 Início → 10:35 Abastecimento registrado → 13:10 Entrega 1 concluída →
   16:40 Canhoto anexado → 17:15 CT-e encerrado → 18:20 Faturamento emitido`.
2. **Comentários** (D023): aplicável — usados por Gestor Operacional/Suporte para registrar contexto
   de uma Ocorrência ou de uma `INTERROMPIDA`; visibilidade compartilhada com o Cliente é possível
   para comentários explicitamente marcados como tal (ex: aviso de atraso).
3. **Anexos** (D024): foto de avaria, foto de canhoto físico, XML/PDF do CT-e e MDF-e, comprovante
   de pedágio/abastecimento quando não capturado eletronicamente.
4. **Favoritos** (D025): filtros de listagem de viagens (ex: "minhas viagens em atraso", "viagens
   aguardando `ENCERRADA`") favoritáveis pelo Gestor Operacional.
5. **Pesquisa Global** (D026): número da viagem, placa do veículo, nome do motorista, nome do
   cliente, número do CT-e/MDF-e.

## Regras de negócio relacionadas

- D001 — soft delete: nenhuma Viagem/Entrega é excluída fisicamente, mesmo `CANCELADA`.
- D005/D006 — toda consulta de Viagem filtra por `tenant_id`.
- D010 — cancelamento e encerramento forçado exigem confirmação explícita.
- D022–D026 — capacidades transversais aplicadas na seção acima.
- D015/D016 — este documento é a referência canônica da máquina de estados de Viagem.
- D017/D018 — histórico de transições via `ViagemStatusHistory`, nunca sobrescrita de status.
- D019/D020 — três dimensões de status coexistentes; `ENCERRADA` como status composto derivado.

## SLA

| Etapa | Prazo |
|---|---|
| `RASCUNHO` → `PLANEJADA` (alocação de recursos) | Até 30 dias antes da data programada (varia por contrato) |
| Checklist (`AGUARDANDO_CHECKLIST` → `LIBERADA`) | Até o horário programado de início da viagem |
| Execução (`LIBERADA` → `FINALIZADA`) | Conforme programação/rota — a definir por tipo de rota |
| Canhoto registrado após a entrega | Até 24 horas |
| Faturamento após condições atendidas | A definir (política comercial por cliente) |
| Recebimento após faturamento | Conforme prazo de pagamento do contrato (Status Financeiro) |

## Indicadores Gerados

A Viagem, com o `ViagemStatusHistory` completo, gera para BI/analytics:

- Receita e Faturamento
- Km Rodado
- Tempo total e tempo por etapa (Status Operacional)
- Consumo (via Abastecimento, [`006-ABASTECIMENTO.md`](./006-ABASTECIMENTO.md))
- SLA cumprido/estourado, por etapa
- Tempo parado (`INTERROMPIDA`) vs. tempo em execução
- Margem e rentabilidade real (receita menos custo, apurada apenas após `ENCERRADA`)
- Ciclo financeiro da viagem (`RASCUNHO` até `RECEBIDA`)
- Prazo médio de recebimento
- Performance do motorista (viagens no prazo, ocorrências, avarias)

## Riscos

- Atraso (SLA de qualquer etapa estourado).
- Pane mecânica.
- Roubo/sinistro de carga.
- Perda de sinal do rastreamento durante `EM_TRANSITO` (ver
  [`008-RASTREAMENTO.md`](./008-RASTREAMENTO.md)).
- Troca de veículo/motorista não planejada.
- Devolução/recusa de carga.
- Avaria na carga.
- Viagem presa em `FINALIZADA` sem convergir para `ENCERRADA` por pendência fiscal ou financeira
  (MDF-e não encerrado, recebimento não confirmado) — risco operacional específico da fundação D019,
  a ser monitorado por um indicador dedicado assim que implementado.

## KPIs impactados

- Percentual de viagens concluídas no prazo (ver [`../product/PERSONAS.md`](../product/PERSONAS.md),
  persona 2 — Gestor Operacional).
- Taxa de ocorrências por viagem.
- Taxa de devolução/reentrega.
- Tempo médio entre `RASCUNHO` e `LIBERADA` (eficiência de programação).
- Taxa de viagens interrompidas por pane/sinistro.
- Tempo médio entre `FINALIZADA` (operacional) e `ENCERRADA` (composto) — o próprio ciclo financeiro.

## Critérios de encerramento

- **Sucesso operacional**: Status Operacional `FINALIZADA` com todas as Entregas em estado terminal
  e checklist de retorno concluído (quando aplicável) — necessário, mas não suficiente.
- **Sucesso pleno**: Status Composto `ENCERRADA` — convergência de Operacional `FINALIZADA`, Fiscal
  `MDFE_ENCERRADO` e Financeiro `RECEBIDA` (D019). Este é o critério de encerramento real da Viagem.
- **Sem sucesso**: Status Operacional `CANCELADA`, com motivo registrado e, se aplicável,
  sinistro/seguro acionado — uma viagem `CANCELADA` nunca converge para `ENCERRADA`.

## Pontos de integração

- SEFAZ (via `documents`, para CT-e/MDF-e emitidos a partir desta viagem — ver
  [`009-FISCAL.md`](./009-FISCAL.md)).
- Mapbox (roteirização e rastreamento — ver [`008-RASTREAMENTO.md`](./008-RASTREAMENTO.md)).
- App Motorista (execução de campo — ver [`010-APP_MOTORISTA.md`](./010-APP_MOTORISTA.md)).
- Bounded contexts: `freight`, `fleet`, `drivers`, `pricing`, `documents`, `financial`,
  `maintenance`, `tracking`, `notification_center`, `audit`, `analytics`.

## Requisitos futuros

- IA sugerindo alocação ótima de motorista/veículo na Programação (ver
  [`../product/VISION.md`](../product/VISION.md), capítulo 24).
- Reentrega e Devolução como fluxos próprios e detalhados, quando o volume de exceções justificar
  um documento dedicado.
- Integração com Marketplace para Solicitação de frete originada de fora do tenant.
