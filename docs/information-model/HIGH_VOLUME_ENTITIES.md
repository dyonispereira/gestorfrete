# HIGH_VOLUME_ENTITIES.md — Entidades de Alto Volume

Aplicação de D049 (classificação de volume esperado) e D050 (dados Time Series) a entidades
específicas do GestorFrete. **Atualizado após a conclusão do Modelo de Domínio completo (12
categorias, 173 entidades)** — a versão anterior deste documento (Sprint 06) antecipava várias
entidades como "ainda não modeladas"; todas já existem agora, com nome e bounded context definitivos.
Esta é a lista de referência consultada por
[`../database/DATABASE_ARCHITECTURE.md`](../database/DATABASE_ARCHITECTURE.md) (D179) para decidir
particionamento.

## Classificação de volume (D049)

| Nível | Entidade | Bounded Context | Fonte |
|---|---|---|---|
| **Muito Alto** | Posição de Veículo | `tracking` | [`../domain/008-rastreamento.md`](../domain/008-rastreamento.md) |
| **Muito Alto** | Leitura de Telemetria | `tracking` | [`../domain/008-rastreamento.md`](../domain/008-rastreamento.md) |
| **Muito Alto** | Heartbeat | `tracking` | [`../domain/008-rastreamento.md`](../domain/008-rastreamento.md) |
| **Muito Alto** | Log de Auditoria | `audit` | [`../domain/010-administracao.md`](../domain/010-administracao.md) |
| **Alto** | Evento Fiscal | `documents` | [`../domain/007-fiscal.md`](../domain/007-fiscal.md) — omitida na versão anterior deste documento; mesma natureza técnica de `Heartbeat`, uma linha por comunicação com a SEFAZ/ANTT |
| **Alto** | Medição de Pneu | `maintenance` | [`../domain/005-pneus.md`](../domain/005-pneus.md) |
| **Alto** | Evento de Rastreamento | `tracking` | [`../domain/008-rastreamento.md`](../domain/008-rastreamento.md) |
| **Alto** | Inferência de IA | `ai` | [`../domain/012-ia.md`](../domain/012-ia.md) |
| **Alto** | Ocorrência | `freight` | [`../domain/002-operacao.md`](../domain/002-operacao.md) |
| **Alto** | Leitura de Hodômetro | `fleet` | [`../domain/003-frota.md`](../domain/003-frota.md) |
| **Médio** | Viagem, Entrega | `freight` | [`../domain/002-operacao.md`](../domain/002-operacao.md) |
| **Médio** | Ordem de Serviço | `maintenance` | [`../domain/004-manutencao.md`](../domain/004-manutencao.md) |
| **Médio** | Fila de Sincronização, Registro de Sincronização | `mobile` | [`../domain/009-app_motorista.md`](../domain/009-app_motorista.md) |
| **Médio** | Indicador Consolidado | `analytics` | [`../domain/011-bi.md`](../domain/011-bi.md) |
| **Médio** | Execução de Job | `integration` | [`../domain/010-administracao.md`](../domain/010-administracao.md) |
| **Baixo** | Cliente, Fornecedor, Motorista, Veículo Tracionador, Implemento, Pneu e demais Master Data | Ver [`002-MASTER_DATA.md`](./002-MASTER_DATA.md) |

*Nota sobre eventos de barramento*: mensagens RabbitMQ em trânsito não são, em si, uma entidade
armazenada — são Muito Alto volume como fluxo, mas de vida curta (ver
[`007-DATA_RETENTION.md`](./007-DATA_RETENTION.md)). O que persiste em Muito Alto volume é o
`StatusHistory` (D017/D018) ou a entidade histórica própria gerada a partir delas (Log de Auditoria,
Posição de Veículo, etc.), nunca uma "entidade de eventos" genérica centralizada.

## Dados Time Series (D050) — status final

| Dado | Entidade | Status |
|---|---|---|
| GPS | Posição de Veículo (`tracking`) | Modelado — [`../domain/008-rastreamento.md`](../domain/008-rastreamento.md) |
| Telemetria (ignição, velocidade, bateria, tensão, odômetro, horímetro, RPM, temperatura, combustível, aceleração, frenagem) | Leitura de Telemetria (`tracking`) | Modelado — mesmo arquivo, padrão EAV extensível (D120) |
| Hodômetro histórico | Leitura de Hodômetro (`fleet`) | Modelado — [`../domain/003-frota.md`](../domain/003-frota.md) |
| Consumo | Derivado de Abastecimento (`freight`) | Modelado — [`../flows/006-ABASTECIMENTO.md`](../flows/006-ABASTECIMENTO.md) |
| Sulco/pressão/temperatura de pneu | Medição de Pneu (`maintenance`) | Modelado — [`../domain/005-pneus.md`](../domain/005-pneus.md), mesmo padrão EAV |
| Auditoria de plataforma | Log de Auditoria (`audit`) | Modelado — [`../domain/010-administracao.md`](../domain/010-administracao.md) |
| Inferências de IA | Inferência de IA (`ai`) | Modelado — [`../domain/012-ia.md`](../domain/012-ia.md) |

Todas as entidades desta tabela seguem o padrão de particionamento por `tenant_id` + data de
captura desde a primeira migration (D179) — ver
[`../database/DATABASE_ARCHITECTURE.md`](../database/DATABASE_ARCHITECTURE.md).

## Pendências

Nenhuma — o Modelo de Domínio está completo (12/12 categorias). Este documento só muda agora se uma
entidade nova nascer durante a modelagem lógica/física (D102 — nasceria primeiro em
`docs/domain/`, nunca direto aqui) ou se o volume real observado em produção divergir do estimado.
