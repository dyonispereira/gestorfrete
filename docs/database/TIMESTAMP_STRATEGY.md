# TIMESTAMP_STRATEGY.md — Estratégia de Data/Hora

Implementação física de D074 (todo atributo temporal informa sua granularidade) e D003 (UTC,
decisão de fundação do projeto), mais a exibição por fuso do tenant já modelada em
`Configuração Regional do Tenant` ([`dictionary/010-administracao.md`](./dictionary/010-administracao.md)).

## Armazenamento: sempre UTC, sempre `TIMESTAMPTZ`

```sql
data_hora TIMESTAMPTZ NOT NULL DEFAULT now()
```

Nunca `TIMESTAMP` sem timezone. O PostgreSQL guarda `TIMESTAMPTZ` internamente em UTC e converte na
leitura — a aplicação nunca faz essa conversão manualmente nem guarda o fuso junto do valor.

## Exibição: conforme o fuso do Tenant

A conversão de UTC para o fuso local acontece **apenas na apresentação** (frontend/API de leitura),
consultando `Configuração Regional do Tenant.FUSO_HORARIO` — nunca alterando o valor armazenado.
Dois tenants em fusos diferentes leem a mesma linha de `logs_auditoria`, por exemplo, cada um vendo o
horário local correto, sem duplicar dado nenhum.

## Granularidade por Tipo Conceitual (D074)

Já definida no Data Dictionary Funcional — este documento só confirma o tipo SQL físico
correspondente:

| Tipo Conceitual | Granularidade | Tipo SQL |
|---|---|---|
| `Data` | Dia | `DATE` |
| `Data/Hora` (padrão) | Segundo | `TIMESTAMPTZ` |
| `Data/Hora` (GPS/telemetria, quando o Provedor oferece) | Milissegundo | `TIMESTAMPTZ` (PostgreSQL já suporta microssegundo de precisão nativamente — milissegundo é só a granularidade *significativa* dos dados, não uma limitação do tipo) |

Não existe um tipo SQL "milissegundo" separado — a granularidade documentada no dicionário
(D074) é sobre o que a origem do dado garante, não sobre uma limitação do PostgreSQL.

## Colunas universais e seus tipos

| Coluna universal | Tipo SQL | Granularidade |
|---|---|---|
| `criado_em` / `atualizado_em` | `TIMESTAMPTZ` | Segundo (D074) |
| `excluido_em` | `TIMESTAMPTZ` | Segundo |
| `data_hora` (Posição de Veículo, Leitura de Telemetria, Log de Auditoria, Inferência de IA) | `TIMESTAMPTZ` | Milissegundo quando a origem oferece (D074) |

## Três momentos distintos, quando aplicável (D124/D125)

Para dados importados de fonte externa (rastreadores, integrações), até três colunas de tempo
coexistem na mesma linha — nunca colapsadas em uma só (já modelado em
[`dictionary/008-rastreamento.md`](./dictionary/008-rastreamento.md)):

```sql
data_hora_captura       TIMESTAMPTZ NOT NULL,  -- no dispositivo/fonte externa
data_hora_recebimento   TIMESTAMPTZ NOT NULL,  -- quando o GestorFrete recebeu
data_hora_processamento TIMESTAMPTZ NOT NULL   -- quando foi persistido/interpretado
```

Tabelas que **não** vêm de fonte externa (a maioria dos cadastros/transações internas) têm apenas
`criado_em`/`atualizado_em` — as três colunas acima só existem onde o Data Dictionary Funcional já as
definiu explicitamente (rastreamento, telemetria, sincronização mobile, inferências de IA).

## Como este documento cresce

Regra estável. Novas fontes externas que exijam os três momentos distintos seguem o mesmo padrão já
estabelecido, sem necessidade de nova decisão arquitetural — D124/D125 já cobrem o caso geral.
