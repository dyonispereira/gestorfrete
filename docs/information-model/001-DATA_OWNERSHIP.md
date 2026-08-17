# 001 — Data Ownership

Quem é o dono de cada informação relevante do GestorFrete — a aplicação prática de D034 (cada dado
tem um único dono) e D042 (uma informação tem apenas uma fonte de verdade). "Dono" é sempre um
bounded context (nome técnico real, ver [`../architecture/ddd.md`](../architecture/ddd.md)), nunca
uma tela nem um documento. "Apenas Consulta" lista quem lê ou reage por evento — nunca escreve.

## Regra de leitura da tabela

Se um bounded context aparece em "Apenas Consulta", ele nunca grava aquele dado — nem em cópia
local editável, nem por acesso direto ao dado do dono. Ele lê por referência (ID) ou reage a um
Domain Event publicado pelo dono (D008). Quando isso não for óbvio, a coluna Observação explica
como a leitura acontece.

## Dados operacionais centrais

| Informação | Dono | Apenas Consulta | Observação |
|---|---|---|---|
| Hodômetro (Leitura de Hodômetro) | `fleet` | `maintenance`, `freight` | `freight`/`maintenance` publicam o dado bruto via evento (`AbastecimentoRegistrado`, `ChecklistConcluido`); só `fleet` grava a Leitura de Hodômetro oficial — ver [`../domain/003-frota.md`](../domain/003-frota.md) |
| Status Operacional da Viagem | `freight` | `tracking`, `analytics`, `mobile`, `notification_center` | Ver [`../flows/002-VIAGEM.md`](../flows/002-VIAGEM.md) |
| Status Fiscal da Viagem (CT-e/MDF-e/CIOT) | `documents` | `freight`, `financial` | `freight` só lê para saber se pode despachar; ver [`../flows/009-FISCAL.md`](../flows/009-FISCAL.md) |
| Status Financeiro da Viagem (Faturamento) | `financial` | `freight`, `analytics` | Ver [`../flows/005-FINANCEIRO.md`](../flows/005-FINANCEIRO.md) |
| Status Composto `ENCERRADA` | `freight` | `financial`, `documents`, `analytics` | Derivado automaticamente da convergência dos três acima (D019/D020) — nenhum dos três dimensões-dono o escreve diretamente |
| Marca de Fogo do Pneu | `maintenance` | `fleet` | Ver [`../domain/005-pneus.md`](../domain/005-pneus.md) |
| Placa do Veículo Tracionador/Implemento | `fleet` | `freight`, `documents`, `maintenance` | Todos os demais referenciam por ID e exibem a placa via consulta, nunca a duplicam em campo próprio editável |
| Disponibilidade do Veículo (derivada) | `fleet` | `freight`, `analytics` | Read model — ver [`../domain/003-frota.md`](../domain/003-frota.md) |
| Posição de Veículo (rastreamento) | `tracking` | `freight`, `mobile`, `analytics` | Ver [`../flows/008-RASTREAMENTO.md`](../flows/008-RASTREAMENTO.md) |
| Checklist (status/resultado) | `maintenance` | `freight` | Ver [`../flows/007-CHECKLIST.md`](../flows/007-CHECKLIST.md) |
| Ordem de Serviço (status/custo) | `maintenance` | `financial`, `fleet` | `financial` só lê o custo total já fechado (`OrdemServicoFechada`) |
| Abastecimento (registro/validação) | `freight` | `financial`, `fleet` | Ver [`../flows/006-ABASTECIMENTO.md`](../flows/006-ABASTECIMENTO.md) |

## Dados financeiros

| Informação | Dono | Apenas Consulta | Observação |
|---|---|---|---|
| Receita Prevista / Receita Realizada da Viagem | `financial` | `analytics`, `freight` | Ver [`../flows/005-FINANCEIRO.md`](../flows/005-FINANCEIRO.md) — o valor recebido de uma viagem é mantido só aqui; BI e Dashboard apenas leem (D042, exemplo oficial desta decisão) |
| Custo Previsto / Custo Realizado da Viagem | `financial` | `analytics` | Idem |
| Margem Prevista / Margem Realizada / Desvio Financeiro | `financial` | `analytics` | **Dado derivado (D041)** — nunca editável, sempre calculado |
| Centro de Custo (saldo/lançamentos) | `financial` | `fleet`, `maintenance`, `freight` | Os demais só publicam eventos de custo; nunca escrevem diretamente no saldo |
| Adiantamento / Haver do Motorista | `financial` | `drivers`, `mobile` | `mobile` exibe ao motorista via consulta, nunca edita |
| Plano/Assinatura do Tenant | `subscription` | `billing`, `tenancy`, `analytics` | |
| Cobrança Recorrente | `billing` | `subscription`, `analytics` | |

## Dados de cadastro

| Informação | Dono | Apenas Consulta | Observação |
|---|---|---|---|
| Dados cadastrais do Cliente | `crm` | `freight`, `financial` | Ver [`../domain/001-cadastros.md`](../domain/001-cadastros.md) |
| Dados cadastrais do Motorista | `drivers` | `freight`, `mobile`, `financial` | |
| Dados cadastrais do Fornecedor | `maintenance` | `financial` | |
| Tabela de Preço vigente | `pricing` | `freight`, `financial` | |
| Estado do Tenant (`ATIVO`/`SUSPENSO`/etc.) | `tenancy` | `identity_access`, `billing` | Ver [`../flows/001-ONBOARDING.md`](../flows/001-ONBOARDING.md) |
| Permissões/Papel do Usuário | `identity_access` | Todos os módulos (verificação de acesso) | Nenhum módulo duplica a lógica de permissão — apenas consulta `identity_access` |

## Dados transversais (D022–D026)

| Informação | Dono | Apenas Consulta | Observação |
|---|---|---|---|
| Comentários de uma entidade (D023) | O bounded context dono da entidade comentada | Quem visualiza a entidade | Comentário não é uma entidade independente — vive dentro do dono da entidade a que se refere |
| Anexos (D024) | `storage` (candidato — dono técnico ainda em aberto, ver D024) | Todos os módulos que anexam | |
| Trilha de auditoria (D007) | `audit` | Todos (consumidor terminal, D014) | `audit` nunca é fonte de um dado de negócio — apenas registra o que os donos publicam |
| Notificações enviadas | `notification_center` | — | Consumidor terminal de eventos, não republica (mesmo padrão de `audit`/`analytics`, D014) |
| Indicadores/KPIs consolidados | `analytics` | — | Sempre derivado (D041) — `analytics` nunca é a fonte de verdade de um valor operacional, só agrega o que os donos publicam |

## Como usar este documento

Antes de desenhar uma nova entidade ou campo (em [`../domain/`](../domain/) ou, futuramente, em uma
tabela física), verifique se a informação já tem dono aqui. Se tiver, a nova entidade **referencia**
o dono (por ID ou por evento) — nunca duplica o campo como editável. Se não tiver, a decisão de
ownership é tomada e registrada aqui antes de a entidade ser detalhada (D040 — nenhum dado nasce
sem dono).

Este documento cresce junto com [`../domain/`](../domain/): cada novo arquivo `NNN-categoria.md`
que revelar uma informação cross-module deve resultar em uma linha nova aqui.
