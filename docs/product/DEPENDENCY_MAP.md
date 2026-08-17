# DEPENDENCY_MAP.md — Mapa de Dependências

Este documento define, camada por camada, o que cada entidade de negócio **precisa existir antes
dela** para fazer sentido. O objetivo é único: nenhuma dependência circular. Uma entidade de uma
camada nunca pode depender de uma entidade de camada igual ou superior à sua — só de camadas
abaixo.

## A regra

> Dependência sempre aponta para baixo. Se ao desenhar uma nova entidade ela parecer precisar de
> algo de uma camada acima da sua, o problema não é a regra — é a camada em que a entidade nova foi
> colocada, ou um sinal de que ela deveria ser dividida em duas.

Exemplo do formato usado neste documento, para a cadeia de uma Viagem até o BI:

```
Viagem
  depende de → Motorista, Veículo, Cliente, Tabela de Preço
CT-e
  depende de → Viagem
MDF-e
  depende de → CT-e
Financeiro (Faturamento)
  depende de → CT-e, Canhoto
Rastreamento
  depende de → Viagem
BI
  depende de → Viagem, CT-e, MDF-e, Financeiro, Rastreamento (e de tudo mais abaixo dele)
```

---

## Camada 0 — Cadastros-base (sem dependência de negócio)

Não dependem de nenhuma outra entidade além de `tenancy` (todo dado pertence a um tenant).

- Cliente (Embarcador)
- Motorista
- Categoria de Veículo
- Veículo (Cavalo Mecânico) — na prática depende de Categoria de Veículo (`categoria_veiculo_id
  NOT NULL`), listado aqui porque Categoria é ela própria Camada 0 (D367)
- Implemento / Carreta — mesma nota de Categoria de Veículo acima
- Fornecedor
- Centro de Custo
- Tabela de Preço
- Usuário e Permissão
- Filial

## Camada 1 — Qualificação dos cadastros-base

| Entidade | Depende de |
|---|---|
| Habilitação/CNH do Motorista | Motorista |
| Ficha Técnica do Veículo | Veículo |
| Documento do Veículo | Veículo |
| Leitura de Hodômetro | Veículo |
| Composição Veicular | Veículo, Implemento (D367) |
| Contrato de Frete | Cliente, Tabela de Preço |
| Escala de Viagem | Motorista, Veículo |
| Seguro do Veículo | Veículo, Fornecedor (seguradora) |
| Licenciamento do Veículo | Veículo (D367) |

## Camada 2 — Operação central

| Entidade | Depende de |
|---|---|
| **Viagem** | Motorista, Veículo, Cliente, Tabela de Preço, Contrato de Frete |
| Ordem de Serviço | Veículo |
| Roteirização | Viagem |
| Disponibilidade do Veículo | Veículo e, por evento (D032, nunca leitura direta), Viagem + Ordem de Serviço (D367) — projeção só existe de fato depois que ao menos um evento chega |

## Camada 3 — Execução da viagem

| Entidade | Depende de |
|---|---|
| Coleta | Viagem |
| Alocação de Recurso da Viagem | Viagem, Motorista, Veículo Tracionador, Implemento (D374) |
| Entrega | Viagem, Coleta |
| Ocorrência | Viagem |
| Romaneio | Viagem |
| Rastreamento em Tempo Real | Viagem |
| Ciclo de Pneu / Recapagem | Veículo, Ordem de Serviço |

## Camada 4 — Documentos fiscais

| Entidade | Depende de |
|---|---|
| CT-e | Viagem, Cliente, Tabela de Preço |
| Canhoto | Entrega |
| MDF-e | CT-e (um ou mais) |
| CIOT | Viagem, Motorista (quando autônomo) |

## Camada 5 — Financeiro

| Entidade | Depende de |
|---|---|
| Faturamento | CT-e, Canhoto |
| Contas a Receber | Faturamento |
| Adiantamento | Motorista, Viagem |
| Haver do Motorista | Viagem, Adiantamento |
| Plano de Contas | — (Reference Data, auto-referenciada por `categoria_pai_id`) |
| Conta Bancária | — (Reference Data) |
| Contas a Pagar | Fornecedor, Centro de Custo, Plano de Contas, Ordem de Serviço (D384) |
| Rateio de Despesa | Contas a Pagar, Centro de Custo, Viagem (D384) |
| Estorno Financeiro | Fatura, Contas a Pagar ou Contas a Receber (exatamente um, D384) |
| Fluxo de Caixa | Contas a Pagar, Contas a Receber |
| DRE | Fluxo de Caixa, Centro de Custo |

## Camada 6 — Consumidores finais (só leem, nunca são pré-requisito de nada)

Estas entidades/capacidades dependem de qualquer coisa nas camadas 0–5, mas **nada nas camadas
0–5 pode depender delas** — se isso acontecer, é uma dependência circular e deve ser corrigida
antes de implementar.

| Capacidade | Consome dados de |
|---|---|
| Notificações | Viagem, Financeiro, Manutenção (via eventos, ver [`EVENT_MAP.md`](./EVENT_MAP.md)) |
| Relatórios | Qualquer camada abaixo, conforme o relatório |
| BI / Analytics | Qualquer camada abaixo |
| Auditoria | Qualquer camada abaixo (eventos de criação/alteração) |
| Inteligência Artificial | Qualquer camada abaixo (para sugerir ações — nunca é pré-requisito de uma ação, apenas sugere) |

---

## Como usar este documento

Antes de desenhar uma nova entidade de negócio: identifique de quais entidades já mapeadas ela
depende, encontre a camada mais alta entre elas, e posicione a nova entidade uma camada acima. Se
a nova entidade parecer precisar de algo em uma camada igual ou acima da que ela ocuparia, é um
sinal de acoplamento incorreto — revisar antes de prosseguir, não implementar do jeito que "parece
funcionar".

Este documento é atualizado junto com [`PRODUCT_MAP.md`](./PRODUCT_MAP.md): toda vez que uma área
funcional nova entra no mapa de produto, sua posição neste mapa de dependências deve ser definida
antes de qualquer implementação.
