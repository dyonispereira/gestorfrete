# 003 — Manutenção

## Objetivo

Documentar a vida útil completa de uma Ordem de Serviço (OS) — preventiva, corretiva, emergencial
ou de garantia — desde a abertura até o fechamento com custos consolidados, incluindo compra de
peça, almoxarifado e fornecedor. Este fluxo sustenta o bounded context `maintenance` e é consumido
diretamente pelo fluxo [`002-VIAGEM.md`](./002-VIAGEM.md) (uma pane em rota abre uma OS emergencial;
um Checklist reprovado pode abrir uma OS corretiva).

## Pré-condições

- Veículo cadastrado em `fleet`.
- Ao menos um Mecânico e, quando aplicável, um Almoxarife com acesso ao tenant.
- Tabela de peças/insumos existente para permitir baixa de estoque (mesmo que vazia inicialmente).

## Gatilho inicial

Uma OS é aberta por um dos seguintes eventos: agendamento de manutenção preventiva (por
quilometragem/tempo — ver [`004-PNEUS.md`](./004-PNEUS.md) para o caso específico de pneus),
reporte de problema pelo Motorista ou Analista de Frota (corretiva), pane em rota (emergencial, via
`ViagemInterrompida` — ver [`002-VIAGEM.md`](./002-VIAGEM.md)), ou acionamento de garantia de peça/
serviço anterior.

## Máquina de Estados — Ordem de Serviço

### Estados

`ABERTA`, `EM_DIAGNOSTICO`, `AGUARDANDO_APROVACAO`, `AGUARDANDO_PECA`, `EM_EXECUCAO`, `CONCLUIDA`,
`FECHADA` — fluxo principal. `CANCELADA` — exceção.

O **tipo** da OS (`PREVENTIVA`, `CORRETIVA`, `EMERGENCIAL`, `GARANTIA`) é um atributo da OS,
independente do status — todas as quatro seguem a mesma máquina de estados.

```
ABERTA → EM_DIAGNOSTICO ──(custo estimado > limite de alçada)──► AGUARDANDO_APROVACAO
              │                                                        │
              │◄───────────────────(aprovado)──────────────────────────┘
              │
              ▼
        (peça disponível?)
         │              │
         │ não          │ sim
         ▼              ▼
   AGUARDANDO_PECA → EM_EXECUCAO → CONCLUIDA → FECHADA
         │
         └──(peça chega)──► EM_EXECUCAO

  (a partir de ABERTA, EM_DIAGNOSTICO, AGUARDANDO_APROVACAO ou AGUARDANDO_PECA)
       └──(cancelamento)──► CANCELADA
```

### Transições válidas

| De | Para | Gatilho |
|---|---|---|
| `ABERTA` | `EM_DIAGNOSTICO` | Mecânico inicia a avaliação do problema |
| `EM_DIAGNOSTICO` | `AGUARDANDO_APROVACAO` | Custo estimado excede a alçada do Mecânico/Analista de Frota |
| `AGUARDANDO_APROVACAO` | `EM_DIAGNOSTICO` | Gestor aprova — segue para verificar disponibilidade de peça |
| `EM_DIAGNOSTICO` | `AGUARDANDO_PECA` | Peça necessária não disponível no Almoxarifado |
| `EM_DIAGNOSTICO` | `EM_EXECUCAO` | Peça disponível (ou reparo não depende de peça) e sem necessidade de aprovação |
| `AGUARDANDO_PECA` | `EM_EXECUCAO` | Peça recebida (compra concluída ou retirada do Almoxarifado) |
| `EM_EXECUCAO` | `AGUARDANDO_PECA` | Durante o reparo, identifica-se necessidade de outra peça |
| `EM_EXECUCAO` | `CONCLUIDA` | Reparo finalizado e veículo testado |
| `CONCLUIDA` | `FECHADA` | Custos consolidados e lançados no Centro de Custo do veículo |
| `ABERTA`/`EM_DIAGNOSTICO`/`AGUARDANDO_APROVACAO`/`AGUARDANDO_PECA` | `CANCELADA` | OS cancelada antes do início da execução |

### Transições inválidas (normativas)

- **Não é permitido** ir de `ABERTA` diretamente para `EM_EXECUCAO` — todo reparo passa por
  `EM_DIAGNOSTICO`, mesmo que o diagnóstico seja rápido (ex: item já identificado pelo Motorista).
- **Não é permitido** cancelar (`→ CANCELADA`) uma OS em `EM_EXECUCAO` ou posterior — reparo já
  iniciado não é "cancelado", é concluído (mesmo que parcialmente, com Ocorrência registrada) e
  fechado normalmente.
- **Não é permitido** fechar (`→ FECHADA`) uma OS sem passar por `CONCLUIDA` — o fechamento exige o
  reparo já finalizado e testado.
- **Não é permitido** reabrir uma OS `FECHADA` — qualquer problema recorrente gera uma nova OS,
  referenciando a anterior (nunca reescrevendo o histórico já fechado).
- **Não é permitido** avançar para `EM_EXECUCAO` a partir de `AGUARDANDO_APROVACAO` sem a aprovação
  registrada — mesmo que a peça já esteja disponível.

### Histórico de Transições

Por D017/D018, toda transição de status da OS insere um novo registro em
`OrdemServicoStatusHistory`: `id`, `os_id`, `status`, `usuario`, `origem`, `data_hora`,
`observacao` (obrigatória em `CANCELADA` e em `AGUARDANDO_APROVACAO`), sem `latitude`/`longitude`
(entidade não móvel). Esse histórico alimenta o KPI de MTTR (tempo médio de reparo) e o indicador de
tempo de veículo parado.

## Fluxo principal

1. **Abertura** `[ABERTA]` — OS criada, vinculada a um Veículo e a um tipo (preventiva, corretiva,
   emergencial, garantia).
2. **Diagnóstico** `[EM_DIAGNOSTICO]` — Mecânico avalia o problema e estima peças/custo.
3. **Aprovação** `[AGUARDANDO_APROVACAO, quando aplicável]` — Gestor/Analista de Frota aprova custo
   acima da alçada.
4. **Verificação de peça / Almoxarifado** `[AGUARDANDO_PECA, quando aplicável]` — Almoxarife
   verifica disponibilidade; se ausente, aciona compra junto a um Fornecedor.
5. **Compra de peça** `[dentro de AGUARDANDO_PECA]` — pedido de compra ao Fornecedor, recebimento e
   entrada no Almoxarifado.
6. **Execução** `[EM_EXECUCAO]` — Mecânico executa o reparo, registrando peças efetivamente usadas.
7. **Conclusão** `[CONCLUIDA]` — reparo finalizado, veículo testado e liberado para `fleet`.
8. **Fechamento e custos** `[FECHADA]` — custo total (peças + mão de obra) consolidado e lançado no
   Centro de Custo do veículo (`financial`).

## Fluxos alternativos

- **OS sem necessidade de peça**: pula diretamente de `EM_DIAGNOSTICO` para `EM_EXECUCAO`.
- **OS de garantia**: peça ou serviço coberto por garantia de um Fornecedor — o custo lançado no
  Fechamento é zero ou parcial, com a diferença registrada como reembolso a receber do Fornecedor.
- **Manutenção preventiva agendada**: `ABERTA` é criada automaticamente por regra de quilometragem/
  tempo (ver [`004-PNEUS.md`](./004-PNEUS.md) para o caso de pneus), não por reporte manual.

## Fluxos de exceção

- **OS emergencial em rota**: aberta a partir de `ViagemInterrompida` (pane) — segue a mesma máquina
  de estados, com prioridade máxima de diagnóstico e execução; ao concluir, publica evento que
  permite à Viagem retomar.
- **Peça em falta sem previsão de fornecedor**: OS permanece em `AGUARDANDO_PECA` indefinidamente —
  requer acompanhamento ativo do Almoxarife/Gestor (ver Riscos).
- **Reincidência**: problema reaparece pouco depois do fechamento de uma OS anterior — nova OS
  aberta, referenciando a anterior; indicador de reincidência é calculado a partir dessa referência.
- **Cancelamento por decisão de troca do veículo** (baixa/venda): OS em qualquer estado anterior a
  `EM_EXECUCAO` é cancelada com observação obrigatória.

## Eventos publicados

| Evento | Gerado quando |
|---|---|
| `OrdemServicoAberta` | Transição para `ABERTA` — já catalogado em [`../product/EVENT_MAP.md`](../product/EVENT_MAP.md) |
| `OrdemServicoAprovacaoPendente` | Transição para `AGUARDANDO_APROVACAO` (novo) |
| `PecaSolicitada` | Transição para `AGUARDANDO_PECA` com necessidade de compra (novo) |
| `OrdemServicoConcluida` | Transição para `CONCLUIDA` — já catalogado |
| `OrdemServicoFechada` | Transição para `FECHADA` (novo) |
| `OrdemServicoCancelada` | Transição para `CANCELADA` (novo) |

## Eventos consumidos

| Evento | Publicado por | Efeito na OS |
|---|---|---|
| `ViagemInterrompida` | `freight` | Pode gerar abertura automática de OS emergencial |
| `ChecklistReprovado` | `maintenance` (checklist de oficina, ver [`007-CHECKLIST.md`](./007-CHECKLIST.md)) | Pode gerar abertura automática de OS corretiva |

## Permissões

| Etapa | Quem executa |
|---|---|
| Abertura, Diagnóstico, Execução | Mecânico |
| Aprovação de custo acima da alçada | Gestor Operacional / Analista de Frota |
| Verificação/baixa de peça, compra junto a Fornecedor | Almoxarife |
| Fechamento e lançamento de custo | Analista de Frota, com reflexo automático em `financial` |
| Consulta somente leitura | Auditor |

## Auditoria

Toda transição de status é registrada em `audit`, com ator, timestamp e motivo obrigatório nas
transições para `AGUARDANDO_APROVACAO` e `CANCELADA` (D007).

## Notificações

- Gestor Operacional/Analista de Frota: aprovação pendente.
- Almoxarife: peça a comprar.
- Analista de Frota: OS concluída, pronta para fechamento.
- Motorista: veículo liberado após conclusão.

## Capacidades Transversais

1. **Timeline Universal** (D022): `OrdemServicoStatusHistory` + solicitações de peça + comentários
   do Mecânico durante o diagnóstico + anexos (fotos do defeito, nota fiscal da peça).
2. **Comentários** (D023): aplicável — Mecânico registra observações técnicas durante o diagnóstico
   e a execução; visibilidade interna (equipe da transportadora).
3. **Anexos** (D024): foto do defeito, nota fiscal da peça, laudo técnico (garantia).
4. **Favoritos** (D025): filtros como "OSs aguardando minha aprovação" (Gestor), "OSs aguardando
   peça" (Almoxarife).
5. **Pesquisa Global** (D026): número da OS, placa do veículo, nome do Mecânico responsável.

## Regras de negócio relacionadas

- D001 — soft delete: OS `CANCELADA`/`FECHADA` nunca é excluída fisicamente.
- D007 — auditoria obrigatória em toda entidade de negócio.
- D015/D016 — máquina de estados com transições inválidas normativas.
- D022–D026 — capacidades transversais aplicadas na seção acima.
- D017/D018 — histórico via `OrdemServicoStatusHistory`, nunca sobrescrita.

## SLA

| Etapa | Prazo |
|---|---|
| Diagnóstico | A definir por tipo (emergencial tem prioridade máxima) |
| Aprovação de custo | A definir |
| Peça — prazo de fornecedor | A definir por fornecedor/contrato |
| Execução | A definir por complexidade do reparo |
| Fechamento após conclusão | Até 48 horas |

## Indicadores Gerados

- Custo por OS e por veículo/km rodado
- MTTR (tempo médio de reparo)
- Percentual de manutenção preventiva vs. corretiva/emergencial
- Tempo de veículo parado (indisponível para viagem)
- Taxa de reincidência do mesmo problema
- Custo de peças vs. mão de obra

## Riscos

- Falta de peça em estoque sem previsão de fornecedor.
- Atraso de fornecedor.
- Diagnóstico incorreto levando à reincidência.
- Custo estourando orçamento sem aprovação registrada.
- Veículo retornando à operação sem reparo efetivamente completo (falha no teste pós-reparo).

## KPIs impactados

- Disponibilidade da frota (veículos aptos vs. total — ver
  [`../product/PERSONAS.md`](../product/PERSONAS.md), persona 3 — Analista de Frota).
- Custo de manutenção por veículo/km.
- Percentual de manutenções preventivas vs. corretivas.

## Critérios de encerramento

- **Sucesso**: `FECHADA`, com custo consolidado e lançado no Centro de Custo.
- **Sem sucesso**: `CANCELADA`, com motivo registrado.

## Pontos de integração

- `fleet` (libera/bloqueia o veículo), `financial` (Centro de Custo), `drivers` (notificação ao
  Motorista), `freight` (retomada de viagem interrompida por pane).
- Fornecedores externos de peças (fora do escopo desta fundação — hoje tratado como cadastro em
  `fleet`/`maintenance`, sem integração eletrônica).

## Requisitos futuros

- IA sugerindo manutenção preventiva a partir do uso real do veículo (ver
  [`../product/VISION.md`](../product/VISION.md), capítulo 24).
- Integração eletrônica com fornecedores de peças (cotação/pedido automatizado).
- Alçada de aprovação configurável por tenant/perfil.
