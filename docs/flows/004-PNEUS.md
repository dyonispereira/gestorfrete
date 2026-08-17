# 004 — Pneus

## Objetivo

Documentar a vida útil completa de um pneu individual — da compra à baixa definitiva — incluindo o
ciclo de recapagem, que pode se repetir múltiplas vezes antes da sucata. Pneu é rastreado como
unidade individual (não como item de estoque genérico) porque seu histórico de uso é o que permite
apurar custo real por km rodado e decidir entre recapar ou sucatear.

## Pré-condições

- Veículo cadastrado em `fleet`, com posições de pneu definidas (eixo/posição).
- Fornecedor de pneus/recapagem cadastrado.

## Gatilho inicial

Uma Ordem de Compra de pneu é registrada — por reposição de pneu sucateado, ampliação de frota, ou
estoque de segurança.

## Máquina de Estados — Pneu

### Estados

`COMPRADO`, `EM_ESTOQUE`, `INSTALADO`, `AGUARDANDO_RECAPAGEM`, `EM_RECAPAGEM`, `SUCATA`, `BAIXADO`.

```
COMPRADO → EM_ESTOQUE ──(instalação)──► INSTALADO
                ▲                            │
                │                            │ (desgaste no limite de sulco)
                │                            ▼
                │                     AGUARDANDO_RECAPAGEM
                │                            │
                │                            ▼
                └──(recapagem concluída)── EM_RECAPAGEM
                                             │
                                             └──(recapadora reprova)──► SUCATA → BAIXADO

  (a partir de INSTALADO, por dano irreparável em uso)
       └──────────────────────────────────────────────────► SUCATA
```

O ciclo `EM_ESTOQUE → INSTALADO → AGUARDANDO_RECAPAGEM → EM_RECAPAGEM → EM_ESTOQUE` se repete a
cada nova recapagem, até o limite de recapagens configurado para o tipo de pneu ser atingido ou a
recapadora reprovar a carcaça — o que ocorrer primeiro.

### Transições válidas

| De | Para | Gatilho |
|---|---|---|
| `COMPRADO` | `EM_ESTOQUE` | Pneu recebido; Marca de Fogo (número de identificação) aplicada |
| `EM_ESTOQUE` | `INSTALADO` | Pneu montado em um veículo/posição |
| `INSTALADO` | `AGUARDANDO_RECAPAGEM` | Desgaste atinge o limite de sulco; pneu removido do veículo |
| `INSTALADO` | `SUCATA` | Dano irreparável em uso (furo grave, estouro) |
| `AGUARDANDO_RECAPAGEM` | `EM_RECAPAGEM` | Pneu enviado à recapadora |
| `EM_RECAPAGEM` | `EM_ESTOQUE` | Recapagem concluída com sucesso — pronto para reinstalar |
| `EM_RECAPAGEM` | `SUCATA` | Recapadora reprova a carcaça |
| `SUCATA` | `BAIXADO` | Baixa contábil do ativo |

### Transições inválidas (normativas)

- **Não é permitido** ir de `COMPRADO` diretamente para `INSTALADO` — todo pneu passa por
  `EM_ESTOQUE`, onde recebe a Marca de Fogo. Sem esse registro, o pneu não é rastreável
  individualmente.
- **Não é permitido** recapear (`→ EM_RECAPAGEM`) um pneu que não passou por
  `AGUARDANDO_RECAPAGEM` — a remoção do veículo é sempre um passo próprio.
- **Não é permitido** reinstalar (`→ INSTALADO`) um pneu em `SUCATA` ou `BAIXADO`.
- **Não é permitido** dar baixa (`→ BAIXADO`) sem passar por `SUCATA` — a baixa contábil é sempre
  precedida da marcação de sucata, preservando o motivo para auditoria.
- **Não é permitido** enviar para recapagem (`→ EM_RECAPAGEM`) um pneu que já atingiu o número
  máximo de recapagens configurado para seu tipo — a regra de negócio força `SUCATA` diretamente a
  partir de `AGUARDANDO_RECAPAGEM` nesse caso.

### Histórico de Transições

Por D017/D018, toda transição é registrada em `PneuStatusHistory`: `id`, `pneu_id` (referenciado
pela Marca de Fogo), `status`, `usuario`, `origem`, `data_hora`, `observacao` (obrigatória em
`SUCATA`), `veiculo_id` e `posicao` (quando aplicável — `INSTALADO`), sem `latitude`/`longitude`
(a posição geográfica é a do veículo, já rastreada em [`008-RASTREAMENTO.md`](./008-RASTREAMENTO.md),
não do pneu isoladamente). Este histórico é o que permite calcular quilometragem rodada por pneu
entre eventos, contando as recapagens.

## Fluxo principal

1. **Compra** `[COMPRADO]` — pedido registrado junto a um Fornecedor.
2. **Entrada** `[EM_ESTOQUE]` — pneu recebido e conferido no Almoxarifado.
3. **Marca de Fogo** `[dentro de EM_ESTOQUE]` — número de identificação único aplicado ao pneu,
   usado como referência em todo o histórico daqui em diante.
4. **Instalação** `[INSTALADO]` — pneu montado em um Veículo, em uma posição (eixo/lado).
5. **Rodízio** `[permanece INSTALADO]` — troca de posição entre pneus do mesmo veículo ou entre
   veículos; não é uma transição de status, é um evento registrado (ver Fluxos alternativos).
6. **Recapagem** `[AGUARDANDO_RECAPAGEM → EM_RECAPAGEM]` — pneu desgastado é removido e enviado à
   recapadora.
7. **Nova recapagem** `[EM_ESTOQUE → INSTALADO → AGUARDANDO_RECAPAGEM → EM_RECAPAGEM, repetido]` —
   o ciclo se repete até o limite configurado.
8. **Sucata** `[SUCATA]` — pneu chega ao fim da vida útil (limite de recapagens ou dano
   irreparável).
9. **Baixa** `[BAIXADO]` — baixa contábil do ativo.

## Fluxos alternativos

- **Rodízio sem mudança de status**: o pneu permanece `INSTALADO`; apenas os campos `veiculo_id`/
  `posicao` do registro de histórico mudam, gerando uma entrada nova (D018) sem transição de
  status.
- **Pneu novo direto para veículo recém-cadastrado**: primeira instalação de um pneu comprado
  especificamente para um veículo novo na frota — segue o fluxo normal, sem atalho.
- **Transferência entre veículos**: pneu removido de um veículo (`INSTALADO → EM_ESTOQUE`, exceção
  ao padrão de rodízio simples) e instalado em outro — tratado como duas transições, não como
  rodízio.

## Fluxos de exceção

- **Estouro/furo grave em rota**: `INSTALADO → SUCATA` diretamente; gera Ocorrência na Viagem em
  curso (ver [`002-VIAGEM.md`](./002-VIAGEM.md)) e pode acionar troca de pneu emergencial via OS
  (ver [`003-MANUTENCAO.md`](./003-MANUTENCAO.md)).
- **Marca de Fogo ilegível/perdida**: perda de rastreabilidade do pneu individual — tratado como
  risco operacional (ver Riscos), exigindo re-identificação manual auditada antes de qualquer nova
  transição.
- **Recapadora reprova antes do limite esperado**: `EM_RECAPAGEM → SUCATA` antes do número máximo
  de recapagens configurado — gera indicador de sucata prematura para investigação de causa (uso
  inadequado, calibragem incorreta).

## Eventos publicados

| Evento | Gerado quando |
|---|---|
| `PneuCadastrado` | Transição para `EM_ESTOQUE` com Marca de Fogo aplicada (novo) |
| `PneuInstalado` | Transição para `INSTALADO` (novo) |
| `PneuEnviadoParaRecapagem` | Transição para `EM_RECAPAGEM` (novo) |
| `PneuSucateado` | Transição para `SUCATA` (novo) |
| `PneuBaixado` | Transição para `BAIXADO` (novo) |

## Eventos consumidos

Nenhum de outro bounded context — este fluxo é predominantemente interno a `maintenance`/`fleet`;
recebe gatilhos manuais (Fluxos de exceção) registrados como Ocorrência dentro da própria Viagem,
não como evento consumido formalmente nesta etapa de fundação.

## Permissões

| Etapa | Quem executa |
|---|---|
| Compra, Entrada, Marca de Fogo | Almoxarife |
| Instalação, Rodízio | Mecânico |
| Envio para recapagem, acompanhamento de fornecedor | Almoxarife |
| Sucata, Baixa | Analista de Frota (com reflexo em `financial`) |
| Consulta somente leitura | Auditor |

## Auditoria

Toda transição é registrada em `audit`, com ator, timestamp e motivo obrigatório em `SUCATA`
(D007).

## Notificações

- Almoxarife: pneu no limite de sulco, pronto para `AGUARDANDO_RECAPAGEM`.
- Analista de Frota: pneu sucateado, pendente de baixa contábil.
- Mecânico: pneu recapado disponível em estoque, pronto para reinstalação.

## Capacidades Transversais

1. **Timeline Universal** (D022): `PneuStatusHistory` completo — todas as instalações, rodízios,
   recapagens e o veículo/posição de cada passagem, do primeiro uso à baixa.
2. **Comentários** (D023): aplicável — Almoxarife/Mecânico podem anotar causa provável de desgaste
   prematuro ou dano; visibilidade interna.
3. **Anexos** (D024): foto do pneu na entrada (Marca de Fogo legível), laudo da recapadora.
4. **Favoritos** (D025): filtro "pneus no limite de sulco" favoritável pelo Almoxarife.
5. **Pesquisa Global** (D026): número da Marca de Fogo, placa do veículo atual.

## Regras de negócio relacionadas

- D001 — soft delete: pneu `BAIXADO` nunca é excluído fisicamente do registro.
- D007 — auditoria obrigatória.
- D022–D026 — capacidades transversais aplicadas na seção acima.
- D015/D016 — transições inválidas normativas, incluindo o limite de recapagens.
- D017/D018 — histórico via `PneuStatusHistory`, nunca sobrescrita.

## SLA

| Etapa | Prazo |
|---|---|
| Entrada após recebimento | Até 24 horas |
| Instalação após entrada (quando já há demanda) | Conforme necessidade operacional |
| Recapagem — prazo de fornecedor | A definir por fornecedor/contrato |
| Baixa contábil após sucata | Até o fechamento do mês corrente |

## Indicadores Gerados

- Custo por pneu / km rodado (considerando todas as recapagens)
- Número médio de recapagens por pneu, por marca/modelo
- Vida útil média em km, por marca/modelo
- Custo médio de recapagem vs. pneu novo
- Taxa de sucata prematura (antes do limite de recapagens esperado)

## Riscos

- Furo/estouro em rota.
- Marca de fogo ilegível ou perdida (perda de rastreabilidade individual).
- Recapadora reprovando pneus além do esperado (indício de problema de uso/calibragem).
- Rodízio não registrado, desalinhando o histórico de posição/quilometragem.
- Pneu excedendo o número seguro de recapagens sem ser identificado a tempo.

## KPIs impactados

- Custo de manutenção por veículo/km (ver [`003-MANUTENCAO.md`](./003-MANUTENCAO.md)).
- Disponibilidade da frota.

## Critérios de encerramento

- **Sucesso** (fim natural do ciclo de vida): `BAIXADO`, após `SUCATA` com motivo registrado.
- Não há "sem sucesso" para este fluxo — todo pneu eventualmente atinge `BAIXADO`; o que varia é o
  número de ciclos de recapagem percorridos.

## Pontos de integração

- `fleet` (posição do pneu no veículo), `maintenance` (Ordens de Serviço relacionadas a troca de
  pneu), `financial` (custo de compra/recapagem no Centro de Custo).
- Fornecedores de pneus e recapadoras (fora do escopo eletrônico desta fundação).

## Requisitos futuros

- Leitura automatizada da Marca de Fogo via código/QR na entrada e no rodízio, reduzindo erro
  manual de identificação.
- IA prevendo o momento ideal de recapagem a partir do padrão de desgaste (ver
  [`../product/VISION.md`](../product/VISION.md), capítulo 24).
