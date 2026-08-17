# 007 — Checklist

## Objetivo

Documentar o ciclo de vida de um Checklist — o mecanismo de verificação estruturada que outros
fluxos (Viagem, Manutenção) usam como portão de qualidade antes de avançar. Um mesmo modelo de
máquina de estados serve a cinco tipos: Motorista (saída/retorno), Oficina, Administrativo,
Carregamento e Descarga — o que muda entre eles é o conjunto de itens verificados, não o
comportamento do ciclo de vida.

## Pré-condições

- Um modelo de checklist (lista de itens a verificar) cadastrado para o tipo/contexto aplicável.
- Uma entidade de referência existente à qual o checklist se associa (Viagem, OS, Veículo).

## Gatilho inicial

Um Checklist é criado automaticamente quando o fluxo de referência atinge o ponto que o exige (ex:
Viagem entra em `AGUARDANDO_CHECKLIST` — ver [`002-VIAGEM.md`](./002-VIAGEM.md); OS chega a
`EM_EXECUCAO`/`CONCLUIDA` — ver [`003-MANUTENCAO.md`](./003-MANUTENCAO.md)), ou manualmente para o
tipo Administrativo (verificação periódica não ligada a um evento operacional).

## Máquina de Estados — Checklist

### Estados

`PENDENTE`, `EM_PREENCHIMENTO`, `CONCLUIDO`, `APROVADO`, `REPROVADO`.

O **tipo** (`MOTORISTA_SAIDA`, `MOTORISTA_RETORNO`, `OFICINA`, `ADMINISTRATIVO`, `CARREGAMENTO`,
`DESCARGA`) é um atributo do Checklist, independente do status — todos seguem a mesma máquina.

```
PENDENTE → EM_PREENCHIMENTO → CONCLUIDO ──► APROVADO
                                    │
                                    └───────► REPROVADO ──(gera nova instância)──► PENDENTE (novo registro)
```

### Transições válidas

| De | Para | Gatilho |
|---|---|---|
| `PENDENTE` | `EM_PREENCHIMENTO` | Responsável inicia o preenchimento |
| `EM_PREENCHIMENTO` | `CONCLUIDO` | Todos os itens do checklist foram respondidos |
| `CONCLUIDO` | `APROVADO` | Nenhum item crítico reprovado |
| `CONCLUIDO` | `REPROVADO` | Ao menos um item crítico reprovado |

### Transições inválidas (normativas)

- **Não é permitido** ir de `EM_PREENCHIMENTO` diretamente para `APROVADO`/`REPROVADO` — o checklist
  precisa estar `CONCLUIDO` (todos os itens respondidos) antes de qualquer avaliação.
- **Não é permitido** reabrir um Checklist `APROVADO` ou `REPROVADO` — uma correção após reprovação
  gera um **novo registro** de Checklist (novo `id`), referenciando o anterior; o histórico do
  registro reprovado nunca é alterado (mesmo princípio de imutabilidade pós-terminal usado em
  [`002-VIAGEM.md`](./002-VIAGEM.md) e [`003-MANUTENCAO.md`](./003-MANUTENCAO.md)).
- **Não é permitido** a uma Viagem avançar de `AGUARDANDO_CHECKLIST` para `LIBERADA`
  (ver [`002-VIAGEM.md`](./002-VIAGEM.md)) referenciando um Checklist que não esteja `APROVADO`.

### Histórico de Transições

Por D017/D018, toda transição é registrada em `ChecklistStatusHistory`: `id`, `checklist_id`,
`status`, `usuario`, `origem`, `data_hora`, `observacao` (obrigatória em `REPROVADO`, detalhando o
item que reprovou), `latitude`/`longitude` (quando preenchido via app mobile em campo — Checklist
Motorista). Esse histórico alimenta o indicador de tempo médio de preenchimento e a taxa de
reprovação por tipo/item.

## Fluxo principal

1. **Criação** `[PENDENTE]` — Checklist instanciado a partir do modelo do tipo aplicável, vinculado
   à entidade de referência (Viagem, OS, Veículo).
2. **Preenchimento** `[EM_PREENCHIMENTO]` — responsável percorre os itens (ex: nível de óleo,
   pneus, documentação do veículo, EPIs, condição da carga).
3. **Conclusão** `[CONCLUIDO]` — todos os itens respondidos.
4. **Avaliação** `[APROVADO ou REPROVADO]` — automática, a partir das respostas dos itens críticos.
5. **Liberação do fluxo de referência** — Viagem avança para `LIBERADA`, OS avança para
   `CONCLUIDA`, ou Entrega é confirmada, conforme o tipo de checklist e seu resultado `APROVADO`.

## Fluxos alternativos

- **Checklist Administrativo periódico**: não bloqueia nenhum outro fluxo diretamente — gera apenas
  alerta e registro de auditoria quando `REPROVADO` (ex: documentação de veículo vencida).
- **Checklist com itens não-críticos reprovados**: pode chegar a `APROVADO` mesmo com pendências
  menores registradas como observação, desde que nenhum item marcado como crítico tenha reprovado —
  a distinção crítico/não-crítico é uma configuração do modelo de checklist, não desta máquina de
  estados.

## Fluxos de exceção

- **Checklist de saída (Motorista) reprovado**: publica `ChecklistReprovado`; a Viagem correspondente
  permanece em `AGUARDANDO_CHECKLIST` (nunca avança) e uma OS corretiva pode ser aberta
  automaticamente (ver [`003-MANUTENCAO.md`](./003-MANUTENCAO.md)); o motorista/mecânico gera um
  novo Checklist após a correção.
- **Checklist de Oficina reprovado**: a OS correspondente não avança para `CONCLUIDA` — reparo é
  considerado incompleto, mesmo que o Mecânico tenha registrado o serviço como feito.
- **Checklist de Carregamento/Descarga reprovado**: gera Ocorrência de Avaria na Viagem (ver
  [`002-VIAGEM.md`](./002-VIAGEM.md), fluxo de exceção Avaria) sem necessariamente interromper a
  viagem inteira.

## Eventos publicados

| Evento | Gerado quando |
|---|---|
| `ChecklistIniciado` | Transição para `EM_PREENCHIMENTO` (novo) |
| `ChecklistConcluido` | Transição para `CONCLUIDO` (novo) |
| `ChecklistAprovado` | Transição para `APROVADO` (novo) |
| `ChecklistReprovado` | Transição para `REPROVADO` — já catalogado em [`../product/EVENT_MAP.md`](../product/EVENT_MAP.md) (publicado por `maintenance`) |

## Eventos consumidos

Nenhum — Checklist é acionado pelo estado de outras entidades (Viagem, OS), não por eventos de
outros bounded contexts.

## Permissões

| Etapa | Quem executa |
|---|---|
| Checklist Motorista | Motorista (app mobile) |
| Checklist Oficina | Mecânico |
| Checklist Administrativo | Analista de Frota |
| Checklist Carregamento/Descarga | Motorista, com conferência do Gestor Operacional quando aplicável |
| Consulta somente leitura | Auditor |

## Auditoria

Toda transição é registrada em `audit`, com ator, timestamp e o item específico que causou
`REPROVADO` (D007).

## Notificações

- Gestor Operacional/Analista de Frota: checklist reprovado, com o item específico.
- Motorista: checklist pendente antes de iniciar viagem.

## Capacidades Transversais

1. **Timeline Universal** (D022): `ChecklistStatusHistory` + fotos anexadas por item reprovado —
   consumido pela Timeline Universal da Viagem/OS de referência (ver
   [`002-VIAGEM.md`](./002-VIAGEM.md), [`003-MANUTENCAO.md`](./003-MANUTENCAO.md)), não apenas pela
   própria.
2. **Comentários** (D023): aplicável em itens reprovados — visibilidade interna.
3. **Anexos** (D024): foto obrigatória em itens críticos reprovados (ex: avaria visível).
4. **Favoritos** (D025): não se aplica diretamente — o checklist é sempre acessado a partir da
   entidade de referência (Viagem/OS), nunca listado isoladamente para favoritar.
5. **Pesquisa Global** (D026): não indexado diretamente — encontrado via busca pela Viagem/OS de
   referência.

## Regras de negócio relacionadas

- D007 — auditoria obrigatória.
- D010 — reprovação de item crítico bloqueia o fluxo de referência até correção (é, em si, uma
  forma de "confirmação" negativa que impede avanço sem tratativa).
- D022–D026 — capacidades transversais aplicadas na seção acima (com duas exceções explícitas:
  Favoritos e Pesquisa Global não se aplicam diretamente a este fluxo).
- D015/D016 — transições inválidas normativas, incluindo a imutabilidade pós-avaliação.
- D017/D018 — histórico via `ChecklistStatusHistory`, nunca sobrescrita.

## SLA

| Etapa | Prazo |
|---|---|
| Preenchimento do Checklist Motorista (saída) | Até o horário programado de início da viagem |
| Preenchimento do Checklist Oficina | Antes do fechamento da OS |
| Checklist Administrativo | Periodicidade configurável (a definir) |
| Nova instância após reprovação | Sem prazo fixo — depende da correção do item reprovado |

## Indicadores Gerados

- Taxa de reprovação por tipo de checklist
- Item com maior taxa de reprovação (indicador de manutenção preventiva a priorizar)
- Tempo médio de preenchimento
- Percentual de viagens liberadas sem retrabalho de checklist (aprovado na primeira instância)

## Riscos

- Item crítico marcado como aprovado incorretamente (falha humana de preenchimento).
- Checklist Administrativo negligenciado por não bloquear operação diretamente.
- Sobrecarga de checklists obrigatórios reduzindo a adesão real do motorista (risco de produto,
  ligado ao princípio de simplicidade — ver [`../product/PRODUCT_PRINCIPLES.md`](../product/PRODUCT_PRINCIPLES.md)).

## KPIs impactados

- Percentual de viagens liberadas no prazo (depende de checklist aprovado a tempo).
- Taxa de ocorrências evitáveis (checklist bem executado reduz avarias/panes).

## Critérios de encerramento

- **Sucesso**: `APROVADO`.
- **Sem sucesso**: `REPROVADO`, sempre com nova instância gerada após a correção do item.

## Pontos de integração

- `freight` (gate de `AGUARDANDO_CHECKLIST → LIBERADA`), `maintenance` (gate de conclusão de OS),
  `mobile` (preenchimento em campo pelo Motorista).

## Requisitos futuros

- Fotos obrigatórias em itens específicos do checklist (ex: avaria de carga), integrando com o
  fluxo do App Motorista (ver [`010-APP_MOTORISTA.md`](./010-APP_MOTORISTA.md)).
- Modelos de checklist configuráveis por tenant, com itens críticos/não-críticos definidos pelo
  próprio cliente.
