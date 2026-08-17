# 084 — Reports (Relatórios)

## D326 — reconciliado com o Lote 11, nenhum recurso novo criado

O kickoff deste lote pediu "Relatórios salvos e consultas configuráveis... Separar: Relatório /
Configuração / Execução / Resultado" como um recurso transversal novo. Auditoria (D200, aplicada
antes de escrever qualquer endpoint) encontrou que **esse recurso já existe, construído no Lote 11
(BI)**: `068-saved-reports.md`, bounded context `reporting`, tabela física `relatorios_salvos`
(`relational/011-bi.md`) — a única tabela física para o conceito "relatório" em todo o Modelo
Relacional. Não há uma segunda tabela "relatório transversal" distinta esperando ser exposta.

A separação Relatório/Configuração/Execução/Resultado pedida no kickoff já existe, com nomes
próprios estabelecidos no Lote 11:

| Conceito pedido no kickoff | Recurso já existente |
|---|---|
| Relatório (definição) | `SavedReport` — `068-saved-reports.md` |
| Configuração | `SavedReport.metric_ids`/`.filters`/`.output_format` |
| Execução | `POST /reporting/exports` — `069-exports.md` |
| Resultado | `Export` — `069-exports.md` |

## D076 aplicado — por que não duplicar

Criar `084-reports.md` como um segundo endpoint `/reports` com o mesmo formato de
`SavedReport`/`Export` produziria duas superfícies concorrentes para o mesmo dado físico — exatamente
o cenário que D076 (reconciliar antes de criar) existe para prevenir. Nenhum endpoint novo nasce
deste documento.

## Nunca uma query SQL exposta pelo frontend

O pedido explícito do kickoff ("Não transformar cada relatório em uma query SQL exposta pelo
frontend") já era, e continua sendo, a garantia de `068-saved-reports.md`: `SavedReport` guarda
`metric_ids`/`filters`/`output_format` — o que compor e como exportar — nunca uma string de query.

## Como este documento cresce

Se o produto precisar de um conceito de "relatório" genuinamente distinto de `SavedReport` (ex.:
relatórios não baseados em Métrica de BI, mas em consultas ad-hoc de qualquer módulo), isso é uma
decisão de Domain primeiro (D101/D076) — uma tabela física nova, não uma reinterpretação deste
arquivo.
