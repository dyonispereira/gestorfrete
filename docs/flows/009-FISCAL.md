# 009 — Fiscal

## Objetivo

Documentar o ciclo de vida dos documentos fiscais de uma viagem — CT-e, MDF-e e CIOT — incluindo
cancelamentos, carta de correção e encerramento. Este documento é a referência canônica do Status
Fiscal introduzido em [`002-VIAGEM.md`](./002-VIAGEM.md) (D020); `002-VIAGEM.md` resume, este
detalha.

## Pré-condições

- Viagem com dados completos de origem/destino, cliente e carga (necessários para o CT-e).
- Certificado digital do tenant configurado para comunicação com a SEFAZ.

## Gatilho inicial

A Viagem transita de `LIBERADA` para `EM_DESLOCAMENTO` (`ViagemDespachada`, ver
[`002-VIAGEM.md`](./002-VIAGEM.md)), disparando a emissão do CT-e.

## Máquina de Estados — CT-e

Por D106, o CT-e tem sua própria máquina de estados completa — mais granular que o resumo de
`STATUS_FISCAL` que a Viagem mantém (D081, projeção; ver [`002-VIAGEM.md`](./002-VIAGEM.md)). Um
observador externo lendo só a Viagem enxerga apenas `PENDENTE`/`AUTORIZADO`/`CANCELADO`/`DENEGADO`;
o CT-e, internamente, percorre mais estados intermediários.

### Estados

`RASCUNHO`, `VALIDADO`, `ASSINADO`, `TRANSMITIDO`, `AUTORIZADO`, `CANCELADO`, `DENEGADO`,
`INUTILIZADO`.

```
RASCUNHO → VALIDADO → ASSINADO → TRANSMITIDO ──(SEFAZ autoriza)──► AUTORIZADO
                                       │                                │
                                       └──(SEFAZ rejeita)──► DENEGADO   └──(cancelamento, dentro do prazo legal)──► CANCELADO

  (a partir de RASCUNHO/VALIDADO, número reservado mas nunca transmitido)
       └──(faixa de numeração inutilizada)──► INUTILIZADO
```

`INUTILIZADO` é distinto de `CANCELADO`: um número de CT-e é **inutilizado** quando foi reservado
(pela Configuração Fiscal do Tenant, D110) mas nunca chegou a ser transmitido/autorizado (ex: falha
de sistema entre a reserva do número e a transmissão) — a numeração não pode ter buracos silenciosos
perante a SEFAZ. **Cancelamento**, por outro lado, reverte um CT-e que já foi `AUTORIZADO`.

### Transições válidas

| De | Para | Gatilho |
|---|---|---|
| `RASCUNHO` | `VALIDADO` | Dados obrigatórios conferidos (schema XML válido) |
| `VALIDADO` | `ASSINADO` | Assinatura digital aplicada (certificado da Configuração Fiscal do Tenant) |
| `ASSINADO` | `TRANSMITIDO` | Envio à SEFAZ |
| `TRANSMITIDO` | `AUTORIZADO` | SEFAZ autoriza a emissão |
| `TRANSMITIDO` | `DENEGADO` | SEFAZ rejeita (CNPJ irregular, dados inconsistentes) |
| `AUTORIZADO` | `CANCELADO` | Cancelamento solicitado dentro do prazo legal |
| `RASCUNHO`/`VALIDADO` | `INUTILIZADO` | Número reservado nunca chega a ser transmitido (falha de sistema, mudança de plano) |

### Transições inválidas (normativas)

- **Não é permitido** cancelar um CT-e (`→ CANCELADO`) fora do prazo legal de cancelamento — após
  esse prazo, a correção só é possível via Carta de Correção (para erros formais) ou por
  procedimento fiscal específico fora do escopo deste sistema.
- **Não é permitido** reemitir um CT-e `DENEGADO` como o mesmo registro — gera um novo CT-e, após
  correção do motivo da denegação.
- **Não é permitido** um CT-e `CANCELADO` ou `INUTILIZADO` retornar a qualquer estado anterior.
- **Não é permitido** pular `ASSINADO`/`TRANSMITIDO` direto de `VALIDADO` para `AUTORIZADO` — a
  assinatura e a transmissão são sempre passos próprios, auditáveis independentemente do resultado
  da SEFAZ.
- **Idempotência (D108)**: receber a mesma resposta de autorização/denegação da SEFAZ mais de uma
  vez (reentrega, timeout seguido de retry) nunca gera uma segunda transição — a segunda resposta
  idêntica é descartada após conferência do protocolo já registrado.

## Máquina de Estados — MDF-e

### Estados

`PENDENTE`, `AUTORIZADO`, `ENCERRADO`, `CANCELADO`.

```
PENDENTE ──(SEFAZ autoriza)──► AUTORIZADO ──(última entrega concluída)──► ENCERRADO
    │                               │
    └───────────(cancelamento, antes de ENCERRADO)──► CANCELADO
```

### Transições válidas

| De | Para | Gatilho |
|---|---|---|
| `PENDENTE` | `AUTORIZADO` | MDF-e emitido, consolidando um ou mais CT-e `AUTORIZADO` |
| `AUTORIZADO` | `ENCERRADO` | Última Entrega da Viagem concluída (`MDFeEncerrado`, ver [`002-VIAGEM.md`](./002-VIAGEM.md)) |
| `PENDENTE`/`AUTORIZADO` | `CANCELADO` | Cancelamento antes do encerramento |

### Transições inválidas (normativas)

- **Não é permitido** emitir MDF-e sem ao menos um CT-e `AUTORIZADO` vinculado.
- **Não é permitido** encerrar (`→ ENCERRADO`) um MDF-e antes da conclusão operacional da última
  Entrega da Viagem — esta é exatamente a condição que trava `ENCERRADA` em D019.
- **Não é permitido** cancelar um MDF-e já `ENCERRADO`.

## Máquina de Estados — CIOT

### Estados

`PENDENTE`, `REGISTRADO`, `CANCELADO`.

Aplicável apenas quando a Viagem envolve motorista autônomo (TAC). Ciclo simples:
`PENDENTE → REGISTRADO`, com `CANCELADO` como exceção antes do início da viagem.

## Carta de Correção (CC-e)

Não é uma transição de status — é um registro adicional anexado a um CT-e já `AUTORIZADO`,
corrigindo erros formais que não alteram valores fiscais nem partes envolvidas (ex: erro de
digitação em observações). O CT-e permanece `AUTORIZADO`; a CC-e aparece na Timeline Universal do
documento como um evento próprio.

## Histórico de Transições

Por D017/D018, cada uma das três máquinas gera seu próprio histórico append-only:
`CTeStatusHistory`, `MDFeStatusHistory`, `CIOTStatusHistory` — mesmos campos padrão (`id`,
`documento_id`, `status`, `usuario`, `origem`, `data_hora`, `observacao`, obrigatória em
`CANCELADO`/`DENEGADO`).

## Fluxo principal

1. **CT-e** `[PENDENTE → AUTORIZADO]` — emitido ao despachar a Viagem.
2. **MDF-e** `[PENDENTE → AUTORIZADO]` — emitido consolidando o(s) CT-e da viagem.
3. **CIOT** `[PENDENTE → REGISTRADO, quando aplicável]` — registrado para motorista autônomo.
4. **NF-e** *(referenciada, não emitida pela transportadora)* — o CT-e referencia a(s) NF-e do
   cliente/embarcador que acompanham a carga; o GestorFrete não emite NF-e.
5. **Cancelamentos** `[→ CANCELADO, quando aplicável]` — dentro do prazo legal de cada documento.
6. **Carta de Correção** — quando aplicável, anexada a um CT-e `AUTORIZADO`.
7. **Encerramento** `[MDF-e: AUTORIZADO → ENCERRADO]` — ao concluir a última Entrega.

## Fluxos alternativos

- **Viagem com múltiplos CT-e** (multi-cliente ou multi-carga): um MDF-e consolida vários CT-e
  `AUTORIZADO`; o encerramento do MDF-e depende de todas as entregas associadas, não de um único
  CT-e.

## Fluxos de exceção

- **SEFAZ indisponível (contingência)**: emissão em modo de contingência conforme regulamentação
  vigente — fora do escopo detalhado desta fundação, tratado como requisito futuro.
- **CNPJ do cliente irregular**: CT-e `DENEGADO` — Viagem não pode avançar em `ViagemDespachada`
  até a pendência ser resolvida (ver [`002-VIAGEM.md`](./002-VIAGEM.md)).
- **MDF-e não encerrado a tempo**: risco direto ao D019 — a Viagem permanece com Status Operacional
  `FINALIZADA` mas nunca atinge `ENCERRADA` enquanto o MDF-e não for `ENCERRADO` (ver Riscos).

## Eventos publicados

| Evento | Gerado quando |
|---|---|
| `CTeEmitido` | Transição para `AUTORIZADO` — já catalogado em [`../product/EVENT_MAP.md`](../product/EVENT_MAP.md) |
| `CTeCancelado` | Transição para `CANCELADO` — já catalogado |
| `CTeDenegado` | Transição para `DENEGADO` (novo) |
| `CTeCorrigido` | Carta de Correção anexada (novo) |
| `MDFeEmitido` | Transição para `AUTORIZADO` — já catalogado |
| `MDFeEncerrado` | Transição para `ENCERRADO` — já catalogado |
| `MDFeCancelado` | Transição para `CANCELADO` (novo) |
| `CIOTRegistrado` | Transição para `REGISTRADO` (novo) |
| `CIOTCancelado` | Transição para `CANCELADO` (novo) |

## Eventos consumidos

| Evento | Publicado por | Efeito |
|---|---|---|
| `ViagemDespachada` | `freight` | Dispara emissão de CT-e |
| `EntregaRealizada` (última da viagem) | `freight` | Dispara encerramento do MDF-e |

## Permissões

| Etapa | Quem executa |
|---|---|
| Emissão, cancelamento, carta de correção | Faturista |
| Registro de CIOT | Faturista, com dados do motorista autônomo |
| Consulta somente leitura | Auditor |

## Auditoria

Toda transição é registrada em `audit`, com motivo obrigatório em `CANCELADO`/`DENEGADO` (D007).

## Notificações

- Faturista: documento denegado, prazo de cancelamento se esgotando.
- Gestor Operacional: MDF-e pendente de encerramento após entrega concluída.

## Capacidades Transversais

1. **Timeline Universal** (D022): `CTeStatusHistory` + `MDFeStatusHistory` + `CIOTStatusHistory` +
   Cartas de Correção, integrados à Timeline Universal da Viagem.
2. **Comentários** (D023): aplicável em denegações e cancelamentos, para registrar a tratativa;
   visibilidade interna.
3. **Anexos** (D024): XML e PDF (DANFE/DACTE/DAMDFE) de cada documento, obrigatórios por
   compliance. Por D107, o XML autorizado é evidência armazenada (`storage`), referenciada por
   ID/URL a partir do CT-e/MDF-e/CIOT — nunca um campo de texto/blob dentro da própria entidade de
   domínio.
4. **Favoritos** (D025): filtro "MDF-e pendentes de encerramento" favoritável pelo Faturista.
5. **Pesquisa Global** (D026): número/chave de acesso do CT-e/MDF-e, número do CIOT.

## Regras de negócio relacionadas

- D007 — auditoria obrigatória.
- D015/D016/D017/D018 — três máquinas de estado com histórico append-only.
- D019/D020 — Fiscal é uma das três dimensões que convergem para `ENCERRADA`.
- D022–D026 — capacidades transversais aplicadas na seção acima.
- D105 — eventos técnicos (webhook SEFAZ/ANTT) nunca alteram o domínio diretamente, sempre
  interpretados pelas regras de `documents` antes de virar transição de status.
- D106 — CT-e tem máquina de estados própria, mais granular que o `STATUS_FISCAL` resumido da
  Viagem (ver Máquina de Estados — CT-e, acima).
- D108 — toda comunicação com SEFAZ/ANTT é tratada de forma idempotente.
- D109 — nenhum documento fiscal é excluído fisicamente, mesmo `CANCELADO`/`INUTILIZADO`.
- D110 — a numeração/série de CT-e/MDF-e é política exclusiva da Configuração Fiscal do Tenant; os
  documentos apenas consomem o próximo número dali.

## SLA

| Etapa | Prazo |
|---|---|
| Emissão de CT-e após despacho | Near real-time (segundos, sujeito à SEFAZ) |
| Emissão de MDF-e | Near real-time, após CT-e autorizado |
| Cancelamento | Dentro do prazo legal vigente (a confirmar com legislação atualizada) |
| Encerramento do MDF-e após última entrega | Até 24 horas (prazo legal de referência, a confirmar) |
| Carta de Correção | Dentro do prazo legal vigente |

## Indicadores Gerados

- Tempo médio de emissão de CT-e/MDF-e
- Percentual de documentos denegados/rejeitados
- Tempo entre última entrega e encerramento do MDF-e
- Quantidade de Cartas de Correção emitidas (indicador de qualidade de cadastro)

## Riscos

- SEFAZ indisponível no momento da emissão.
- CNPJ irregular do cliente gerando denegação recorrente.
- Prazo de cancelamento perdido por atraso operacional.
- MDF-e não encerrado a tempo, bloqueando a convergência de `ENCERRADA` (D019) mesmo com a
  operação fisicamente concluída.

## KPIs impactados

- Compliance fiscal (percentual de documentos emitidos sem erro).
- Ciclo financeiro da viagem (ver [`005-FINANCEIRO.md`](./005-FINANCEIRO.md)) — depende do MDF-e
  `ENCERRADO`.

## Critérios de encerramento

- **Sucesso**: CT-e `AUTORIZADO` e MDF-e `ENCERRADO`.
- **Sem sucesso**: CT-e `DENEGADO` sem correção, ou documentos `CANCELADO` sem reemissão.

## Pontos de integração

- SEFAZ (emissão, cancelamento, consulta de status).
- ANTT (registro de CIOT).
- `freight` (gatilhos de emissão/encerramento), `financial` (CT-e/Canhoto como pré-requisito de
  faturamento — ver [`005-FINANCEIRO.md`](./005-FINANCEIRO.md)).

## Requisitos futuros

- Emissão em modo de contingência quando a SEFAZ estiver indisponível.
- Alertas automáticos de prazo de cancelamento/encerramento próximo do limite.
- Integração com GestorContábil consumindo os documentos fiscais emitidos (ver
  [`../product/VISION.md`](../product/VISION.md), capítulo 20).
