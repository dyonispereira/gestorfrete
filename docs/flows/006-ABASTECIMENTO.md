# 006 — Abastecimento

## Objetivo

Documentar o ciclo completo de um Abastecimento — da autorização à validação de consistência
(hodômetro, litros, média de consumo) — incluindo a detecção de fraudes. Abastecimento é uma das
principais fontes de Custo Realizado de uma viagem (ver [`005-FINANCEIRO.md`](./005-FINANCEIRO.md)).

## Pré-condições

- Viagem em `EM_TRANSITO` (ou outro estado operacional ativo — ver
  [`002-VIAGEM.md`](./002-VIAGEM.md)) ou veículo em operação fora de uma viagem específica
  (abastecimento de pátio).
- Veículo com hodômetro/histórico de consumo registrado (para cálculo de média).

## Gatilho inicial

Motorista solicita autorização de abastecimento via app mobile, informando posto/local e, quando
disponível, valor estimado.

## Máquina de Estados — Abastecimento

### Estados

`SOLICITADO`, `AUTORIZADO`, `REALIZADO`, `EM_VALIDACAO`, `VALIDADO`, `SUSPEITO`, `REJEITADO`,
`NEGADO`.

```
SOLICITADO ──(autorizado)──► AUTORIZADO ──(executado no posto)──► REALIZADO ──► EM_VALIDACAO
     │                                                                                │
     └──(negado)──► NEGADO                                          ┌────────────────┤
                                                                       ▼                ▼
                                                                  VALIDADO          SUSPEITO
                                                                                        │
                                                                     (investigação)     │
                                                              ┌─────────────────────────┤
                                                              ▼                         ▼
                                                          VALIDADO                 REJEITADO
```

### Transições válidas

| De | Para | Gatilho |
|---|---|---|
| `SOLICITADO` | `AUTORIZADO` | Autorização concedida (automática dentro do limite, ou manual) |
| `SOLICITADO` | `NEGADO` | Autorização negada (limite excedido, posto não credenciado) |
| `AUTORIZADO` | `REALIZADO` | Abastecimento executado; cupom, hodômetro e litros registrados |
| `REALIZADO` | `EM_VALIDACAO` | Sistema calcula a média (km/litro) automaticamente |
| `EM_VALIDACAO` | `VALIDADO` | Média dentro do esperado para o veículo |
| `EM_VALIDACAO` | `SUSPEITO` | Média fora do esperado ou inconsistência de hodômetro/cupom |
| `SUSPEITO` | `VALIDADO` | Investigação conclui que é válido (justificativa registrada) |
| `SUSPEITO` | `REJEITADO` | Investigação conclui fraude/erro — não entra no Custo Realizado |

### Transições inválidas (normativas)

- **Não é permitido** ir de `SOLICITADO` diretamente para `REALIZADO` — todo abastecimento passa
  por autorização, mesmo quando automática.
- **Não é permitido** ir de `REALIZADO` diretamente para `VALIDADO` — a validação de média/
  consistência é sempre calculada, nunca pulada.
- **Não é permitido** um Abastecimento `REJEITADO` retornar a `VALIDADO` — um lançamento incorreto
  gera um novo registro (Abastecimento correto), não a reabertura do rejeitado.

### Histórico de Transições

Por D017/D018, toda transição gera um registro em `AbastecimentoStatusHistory`: `id`,
`abastecimento_id`, `status`, `usuario`, `origem`, `data_hora`, `observacao` (obrigatória em
`SUSPEITO`/`REJEITADO`), `latitude`/`longitude` (posição do posto no momento do registro).

## Fluxo principal

1. **Autorização** `[SOLICITADO → AUTORIZADO]` — motorista solicita, sistema/gestor autoriza.
2. **Posto** `[dentro de AUTORIZADO]` — motorista se dirige ao posto (credenciado, quando aplicável).
3. **Cupom** `[REALIZADO]` — cupom fiscal do posto registrado (foto/OCR — ver
   [`010-APP_MOTORISTA.md`](./010-APP_MOTORISTA.md)).
4. **Hodômetro** `[dentro de REALIZADO]` — leitura do hodômetro no momento do abastecimento.
5. **Litros** `[dentro de REALIZADO]` — quantidade abastecida.
6. **Média** `[EM_VALIDACAO]` — sistema calcula km/litro desde o abastecimento anterior do mesmo
   veículo e compara com a média histórica.
7. **Validação** `[VALIDADO ou SUSPEITO]` — automática, com investigação manual apenas quando
   `SUSPEITO`.

## Fluxos alternativos

- **Abastecimento sem viagem ativa** (pátio, reabastecimento preventivo): mesmo ciclo, sem vínculo
  a uma Viagem específica — custo lançado diretamente ao Centro de Custo do veículo.
- **Autorização automática**: dentro de um limite de valor/frequência configurado, `SOLICITADO →
  AUTORIZADO` acontece sem intervenção humana.

## Fluxos de exceção

- **Fraude confirmada** (cupom adulterado, litragem inflada, posto fictício): `SUSPEITO →
  REJEITADO`, com Ocorrência disciplinar registrada para o Motorista.
- **Erro de digitação de hodômetro**: `SUSPEITO` por média fora do esperado, mas investigação
  confirma erro de digitação — corrigido e `→ VALIDADO`, com a correção registrada no histórico
  (nunca sobrescrita silenciosamente).
- **Posto fora da rota**: abastecimento em local muito distante da rota planejada — gera `SUSPEITO`
  por regra de geolocalização (ver [`008-RASTREAMENTO.md`](./008-RASTREAMENTO.md)).

## Eventos publicados

| Evento | Gerado quando |
|---|---|
| `AbastecimentoSolicitado` | Transição para `SOLICITADO` (novo) |
| `AbastecimentoAutorizado` | Transição para `AUTORIZADO` (novo) |
| `AbastecimentoRegistrado` | Transição para `REALIZADO` (novo — consumido por `financial`, ver [`005-FINANCEIRO.md`](./005-FINANCEIRO.md)) |
| `AbastecimentoValidado` | Transição para `VALIDADO` (novo) |
| `AbastecimentoSuspeito` | Transição para `SUSPEITO` (novo) |
| `AbastecimentoRejeitado` | Transição para `REJEITADO` (novo) |

## Eventos consumidos

Nenhum de outro bounded context — recebe apenas o contexto da Viagem ativa (quando aplicável) por
referência direta, não por evento.

## Permissões

| Etapa | Quem executa |
|---|---|
| Solicitação, registro de cupom/hodômetro/litros | Motorista (app mobile) |
| Autorização manual (acima do limite) | Gestor Operacional |
| Investigação de `SUSPEITO` | Analista de Frota / Gestor Operacional |
| Consulta somente leitura | Auditor |

## Auditoria

Toda transição é registrada em `audit`, com ator, timestamp e motivo obrigatório em
`SUSPEITO`/`REJEITADO` (D007).

## Notificações

- Motorista: autorização concedida/negada.
- Analista de Frota/Gestor: abastecimento suspeito, pendente de investigação.

## Capacidades Transversais

1. **Timeline Universal** (D022): `AbastecimentoStatusHistory` completo, integrado à Timeline
   Universal da Viagem (ver [`002-VIAGEM.md`](./002-VIAGEM.md)).
2. **Comentários** (D023): aplicável na investigação de `SUSPEITO`; visibilidade interna.
3. **Anexos** (D024): foto do cupom fiscal, foto do hodômetro.
4. **Favoritos** (D025): filtro "abastecimentos suspeitos pendentes" favoritável pelo Analista de
   Frota.
5. **Pesquisa Global** (D026): placa do veículo, nome do motorista, posto.

## Regras de negócio relacionadas

- D001 — soft delete.
- D007 — auditoria obrigatória.
- D015/D016/D017/D018 — máquina de estados com histórico append-only.
- D022–D026 — capacidades transversais aplicadas na seção acima.

## SLA

| Etapa | Prazo |
|---|---|
| Autorização | Até 5 minutos (para não atrasar o motorista no posto) |
| Validação automática (cálculo de média) | Imediato |
| Investigação de `SUSPEITO` | Até 24 horas |

## Indicadores Gerados

- Média de consumo (km/litro) por veículo e por motorista
- Custo de combustível por km rodado
- Custo médio por litro, por posto/região
- Taxa de abastecimentos suspeitos
- Litros abastecidos por período

## Riscos

- Fraude (cupom falso, litragem inflada, conluio com posto).
- Erro de digitação de hodômetro/litros.
- Abastecimento em posto não credenciado ou fora da rota.
- Autorização automática mal configurada permitindo abuso.

## KPIs impactados

- Consumo (ver [`002-VIAGEM.md`](./002-VIAGEM.md), Indicadores Gerados).
- Custo Realizado da viagem (ver [`005-FINANCEIRO.md`](./005-FINANCEIRO.md)).

## Critérios de encerramento

- **Sucesso**: `VALIDADO` (diretamente ou após investigação de `SUSPEITO`).
- **Sem sucesso**: `NEGADO` (autorização) ou `REJEITADO` (fraude/erro confirmado).

## Pontos de integração

- `mobile` (app do motorista), `freight` (vínculo com a Viagem ativa), `financial` (Custo
  Realizado), `fleet` (histórico de consumo do veículo), `tracking` (validação de geolocalização do
  posto).
- Rede de postos credenciados (fora do escopo eletrônico desta fundação).

## Requisitos futuros

- Integração eletrônica com redes de postos (cartão frota) para autorização/registro automático.
- IA detectando padrões de fraude a partir do histórico (ver
  [`../product/VISION.md`](../product/VISION.md), capítulo 24).
- OCR automático do cupom fiscal (ver [`010-APP_MOTORISTA.md`](./010-APP_MOTORISTA.md)).
