# INDEX.md — Mapa Mestre de Business Flows

Este é o índice de todos os fluxos de negócio documentados do GestorFrete. Um "Business Flow"
descreve **como a empresa funciona** de ponta a ponta para um processo específico — não é uma tela,
não é uma tabela de banco, não é um endpoint. É o comportamento real que telas, banco e API vão
precisar sustentar quando forem construídos.

Todo fluxo novo, ao ser criado, é registrado nesta tabela — este índice nunca fica desatualizado em
relação à pasta `docs/flows/`.

## Regra de estrutura obrigatória

Todo arquivo `NNN-NOME.md` nesta pasta contém, nesta ordem: Objetivo, Pré-condições, Gatilho
inicial, Máquina de Estados (quando o fluxo girar em torno de uma entidade com status — ver
[`../product/DECISIONS.md`](../product/DECISIONS.md), D015/D016), Fluxo principal, Fluxos
alternativos, Fluxos de exceção, Eventos publicados, Eventos consumidos, Permissões, Auditoria,
Notificações, **Capacidades Transversais**, Regras de negócio relacionadas, SLA, Indicadores
Gerados, Riscos, KPIs impactados, Critérios de encerramento, Pontos de integração, Requisitos
futuros. A seção SLA sempre existe, mesmo quando o conteúdo é apenas "a definir" — nunca é omitida.

Toda Máquina de Estados desta pasta segue também D017/D018: o status nunca é sobrescrito, cada
mudança gera um registro de histórico (padrão `<Entidade>StatusHistory`), e por isso cada seção de
Máquina de Estados inclui uma subseção **Histórico de Transições** descrevendo esse registro.

### Capacidades Transversais

Toda entidade central de um fluxo é avaliada contra cinco capacidades de plataforma, registradas em
[`../product/DECISIONS.md`](../product/DECISIONS.md) (D022–D026), sempre nesta ordem:

1. **Timeline Universal** (D022) — o que aparece na linha do tempo desta entidade, além do seu
   próprio `StatusHistory` (eventos de entidades relacionadas, comentários, anexos).
2. **Comentários** (D023) — se aplicável, e a visibilidade padrão (interna vs. compartilhada).
3. **Anexos** (D024) — quais tipos de arquivo fazem sentido para esta entidade.
4. **Favoritos** (D025) — o que, relacionado a esta entidade, faz sentido favoritar (geralmente uma
   tela/relatório/filtro, não a entidade individual).
5. **Pesquisa Global** (D026) — quais campos desta entidade são indexados na busca única.

Nem toda capacidade se aplica com a mesma força a toda entidade — quando uma não se aplica, o fluxo
diz isso explicitamente (nunca omite a subseção em silêncio).

## Índice

| # | Fluxo | Entidade central | Máquina de estados | Status |
|---|---|---|---|---|
| 001 | [Onboarding](./001-ONBOARDING.md) | Tenant / Assinatura | Sim | Concluído |
| 002 | [Viagem](./002-VIAGEM.md) | Viagem | Sim | Concluído |
| 003 | [Manutenção](./003-MANUTENCAO.md) | Ordem de Serviço | Sim | Concluído |
| 004 | [Pneus](./004-PNEUS.md) | Pneu | Sim | Concluído |
| 005 | [Financeiro](./005-FINANCEIRO.md) | Faturamento / Contas a Pagar | Sim | Concluído |
| 006 | [Abastecimento](./006-ABASTECIMENTO.md) | Abastecimento | Sim | Concluído |
| 007 | [Checklist](./007-CHECKLIST.md) | Checklist | Sim | Concluído |
| 008 | [Rastreamento](./008-RASTREAMENTO.md) | Posição/Evento de rastreamento | Não (fluxo de eventos, não de status) | Concluído |
| 009 | [Fiscal](./009-FISCAL.md) | CT-e / MDF-e / CIOT | Sim | Concluído |
| 010 | [App Motorista](./010-APP_MOTORISTA.md) | Execução de Viagem (mobile) | Não (consome a máquina de estados da Viagem) | Concluído |

**Sprint 04 (Business Flows) concluído** — os 10 fluxos planejados estão documentados. Próxima
etapa: `RBAC_MATRIX.md` e `DATA_DICTIONARY_FUNCTIONAL.md` (ver
[`../product/DECISIONS.md`](../product/DECISIONS.md) e roadmap do produto), antes de qualquer
modelagem de banco de dados.

## Convenções

- Numeração sequencial de 3 dígitos, na ordem em que os fluxos foram desenhados — a ordem não
  implica prioridade de implementação (ver [`../product/MODULE_PRIORITY.md`](../product/MODULE_PRIORITY.md)
  para isso).
- Quando um fluxo referencia a máquina de estados de outro (ex: o fluxo de Abastecimento acontece
  *durante* o estado `EM_TRANSITO` da Viagem), ele **não redefine** os estados — apenas referencia
  o fluxo dono da entidade, para evitar duas fontes de verdade divergentes sobre o mesmo status.
- Nomes de estado são `MAIUSCULO_COM_UNDERSCORE`; nomes de evento seguem D013
  ([`../product/EVENT_MAP.md`](../product/EVENT_MAP.md)).
