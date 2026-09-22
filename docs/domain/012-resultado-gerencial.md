# 012 — Resultado Gerencial

Lote 4. **Nenhuma entidade nova.** Resultado Gerencial é uma camada de leitura/agregação
(`modules.analytics`) sobre fatos que `freight`/`financial`/`maintenance`/`fleet`/`drivers`/`crm` já
são donos de calcular — nunca uma cópia. Mesma direção D090/D149 do Lote 11 (BI): `analytics` lê os
módulos operacionais diretamente (cross-module, sancionado pelo import-linter); nenhum módulo
operacional lê de volta.

## Objetivo

Responder, por período: **Viagem** deu dinheiro? **Veículo** realmente gera resultado? **Cliente**
fatura muito e deixa pouca margem? **Motorista** — qual o resultado das operações que ele executou?
Sempre derivado, nunca digitado.

## KPIs fundamentais (as 4 dimensões, quando o dado existir)

Receita Prevista, Receita Realizada, Custo Previsto, Custo Realizado, Margem R$, Margem %, Viagens,
KM rodado, Receita/km, Custo/km, Margem/km.

## Fórmula base (comum às 4 dimensões)

Toda dimensão parte da mesma soma sobre `viagens` (nunca recalculada, só agregada):

- `Viagens` = COUNT
- `Receita Prevista` = Σ `receita_prevista_snapshot`
- `Receita Realizada` = Σ `receita_realizada`
- `Custo Previsto`/`Custo Realizado` (base) = Σ `custo_previsto`/`custo_realizado`
- `Margem R$` = Receita Realizada − Custo Realizado; `Margem %` = Margem R$ / Receita Realizada
- Viagens `CANCELADA` são **sempre excluídas** — não representam operação real. Filtro de período
  usa `viagens.data_programada`; Viagem sem `data_programada` fica fora de qualquer período filtrado
  (mas conta quando nenhum período é informado).

Cada dimensão só muda o `GROUP BY` (`cliente_id`/`veiculo_tracionador_id`/`motorista_id`) e, quando
aplicável, soma um bucket de custo adicional — nunca o mesmo real contado duas vezes entre buckets
(ver "Nunca cria dinheiro" abaixo).

## Dimensão Veículo — Resultado Operacional de Viagens vs. Resultado Total

Pedido central do usuário: um caminhão pode parecer ótimo nas Viagens e consumir tudo fora delas.

- **Resultado Operacional de Viagens** = Receita Realizada − Custo Realizado (só o que as Viagens do
  Veículo geraram).
- **Manutenção Realizada** = Σ `contas_pagar.valor` com `origem=ORDEM_SERVICO`, unida a
  `ordens_servico` por `ordem_servico_id`, filtrada por `ordens_servico.veiculo_tracionador_id`
  (nunca por `contas_pagar.veiculo_tracionador_id`, que é opcional/manual — a FK real e sempre
  presente é a da Ordem de Serviço). Exclui `status=REJEITADA` e Ordens de Serviço `CANCELADA`.
- **Manutenção Prevista** = Σ `ordens_servico.custo_previsto` do Veículo (Ordens não canceladas).
- **Outros Custos Realizados** = Σ `contas_pagar.valor` com `origem` fora de `VIAGEM`/`ORDEM_SERVICO`
  e `veiculo_tracionador_id` preenchido diretamente na Conta a Pagar — depende de o lançamento ter
  sido explicitamente tagueado ao Veículo no cadastro (não é inferido de `viagem_id`).
- **Custo Total** = Custo Realizado (Viagens) + Manutenção Realizada + Outros Custos Realizados.
- **Resultado Total do Veículo** = Receita Realizada − Custo Total.

## Dimensão Cliente — escopo deliberado

`Custo` do Cliente é só o custo operacional de Viagem atribuível a ele (Σ `custo_realizado` das
Viagens do Cliente) — **nunca rateia Manutenção/frota por Cliente**. Isso exigiria uma regra de
alocação (por km, por peso, por número de viagens...) que não existe nos contratos atuais; inventá-la
seria uma aproximação silenciosa. Gap registrado, não implementado.

## Dimensão Motorista — regra explícita do usuário

**Nunca herda automaticamente todo custo do Veículo.** Resultado do Motorista = custo das Viagens que
ele executou (mesmo `custo_realizado` de Viagem, filtrado por `motorista_id`) **+** Contas a Pagar
**explicitamente vinculadas a ele** (`motorista_id` preenchido, qualquer `origem` exceto `VIAGEM` —
essa já está contada via a Viagem, contá-la de novo aqui duplicaria). Uma Ordem de Serviço de R$30 mil
sem `motorista_id` setado em nenhuma Conta a Pagar **nunca** aparece no resultado do Motorista — fica
só no Veículo.

## Visão Geral (topo do painel)

Custo Realizado da empresa = Custo Realizado (Viagens, todas) + Manutenção Realizada (toda a frota) +
"Outros Custos" **somados uma única vez, sem agrupamento por dimensão**. Isto é deliberado: a mesma
Conta a Pagar pode estar tagueada simultaneamente a um Veículo e a um Motorista (ex.: uma multa),
e nesse caso ela aparece tanto em "Outros Custos" do Veículo quanto em "custo vinculado" do
Motorista — cada visão está correta isoladamente. Somar as duas visões agrupadas na Visão Geral
contaria esse real duas vezes; por isso a Visão Geral usa uma soma própria, não-agrupada, sobre as
mesmas Contas a Pagar (contadas exatamente uma vez cada).

## Invariante: agregar nunca cria dinheiro

Σ receita realizada por Viagem = Σ por Cliente = Σ por Motorista = Σ por Veículo = Receita Realizada
da Visão Geral (sempre, para o mesmo período) — toda Viagem tem exatamente um Cliente e, uma vez
alocada, exatamente um Motorista/Veículo "atuais" (`viagens.motorista_id`/`veiculo_tracionador_id`,
os mesmos ponteiros denormalizados já usados no resto do sistema — nunca uma junção com o histórico
de `alocacoes_recurso_viagem`). Quando uma Viagem ainda não tem Veículo/Motorista alocado, ela soma
na Visão Geral mas fica fora do agrupamento por Veículo/Motorista até ser alocada — isso é esperado,
não um bug: a soma por dimensão pode ser **menor ou igual** à Visão Geral, nunca maior, e nunca conta
o mesmo real duas vezes dentro da mesma dimensão. Custo é onde a disciplina importa mais: cada Conta
a Pagar cai em exatamente um bucket por dimensão (Viagem via `custo_realizado` já calculado por
`financial`; Manutenção só por `origem=ORDEM_SERVICO`; Outros Custos só pelas demais origens) —
nunca dois buckets da mesma dimensão somam a mesma linha. Provado com Decimal exato em
`tests/integration/test_management_result_flow.py` e no e2e (`resultado-gerencial.spec.ts`).

## Gaps registrados — não aproximados

1. **KM rodado por Viagem não é derivável hoje.** `viagens.km_rodado` existe na coluna mas nunca é
   preenchido por nenhum fluxo (nem despacho, nem finalização). `leituras_hodometro` tem um
   `viagem_id` opcional, mas é lançamento manual, sem convenção de par início/fim — não há como
   calcular `km` de uma Viagem com segurança a partir dos contratos atuais. Consequência: `KM`,
   `Receita/km`, `Custo/km`, `Margem/km` retornam `null` (nunca `0` ou uma aproximação) sempre que a
   base não tiver `km_rodado`, em qualquer dimensão. Fechar este gap exige decidir uma convenção real
   de captura de KM por Viagem — fora do escopo desta Parte.
2. **Manutenção não tem "Outros Custos" previsto.** `contas_pagar` não distingue previsto/realizado
   (é lançamento único, sem orçamento prévio) — só Viagem (`custo_previsto`) e Ordem de Serviço
   (`custo_previsto`, calculado de `itens_ordem_servico`) têm um previsto de verdade. "Custo
   Previsto" do Veículo soma os dois; "Outros Custos" só existe do lado realizado.
3. **Conta a Pagar `REJEITADA` que já tinha sido lançada continua contando em
   `viagens.custo_realizado`** (D390, comportamento anterior a esta Parte — `create_accounts_
   payable.py` recalcula o realizado na criação, e rejeitar não dispara um novo recálculo). Não
   alterado aqui, fora de escopo. Os buckets novos desta Parte (Manutenção, Outros Custos, custo
   vinculado ao Motorista) excluem `REJEITADA` explicitamente — divergência deliberada, documentada
   para não parecer inconsistência não-intencional.
4. **Custo do Cliente não inclui frota/manutenção** (ver "Dimensão Cliente" acima) — exigiria uma
   regra de rateio inexistente.
