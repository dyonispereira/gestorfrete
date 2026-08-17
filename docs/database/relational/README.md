# docs/database/relational — Modelo Relacional (Lote 2+)

Um arquivo `NNN-categoria.md` por vez, mesma ordem do Modelo de Domínio (D101-style, agora aplicado
à camada relacional). Cada arquivo assume as 8 regras do Lote 1 (ver [`../README.md`](../README.md))
como já resolvidas — nunca repete `tenant_id`/auditoria/soft delete/UUID por tabela.

**Modelo Relacional planejado completo** — `001-core.md` a `012-ia.md`, `Status: Concluído` em
todos. Próxima etapa do roadmap: `DER.md` (diagrama lógico consolidado), seguido de `TABLES.md`,
`FOREIGN_KEYS.md`, `INDEXES.md`, `CONSTRAINTS.md`, `PARTITIONING.md`, `MIGRATION_ORDER.md` e
`SEED_DATA.md` (ver [`../../product/DECISIONS.md`](../../product/DECISIONS.md) para a sequência
completa acordada).

| # | Arquivo | Categoria | Status |
|---|---|---|---|
| 001 | [`001-core.md`](./001-core.md) | Core (SaaS, Identidade, Configuração) | Concluído |
| 002 | [`002-cadastros.md`](./002-cadastros.md) | Cadastros | Concluído |
| 003 | [`003-operacao.md`](./003-operacao.md) | Operação (Viagem e correlatas) | Concluído |
| 004 | [`004-frota.md`](./004-frota.md) | Frota | Concluído |
| 005 | [`005-manutencao.md`](./005-manutencao.md) | Manutenção | Concluído |
| 006 | [`006-financeiro.md`](./006-financeiro.md) | Financeiro | Concluído |
| 007 | [`007-fiscal.md`](./007-fiscal.md) | Fiscal | Concluído |
| 008 | [`008-rastreamento.md`](./008-rastreamento.md) | Rastreamento | Concluído |
| 009 | [`009-app_motorista.md`](./009-app_motorista.md) | App Motorista | Concluído |
| 010 | [`010-administracao.md`](./010-administracao.md) | Administração (Segurança/Configurações/Plataforma restantes) | Concluído |
| 011 | [`011-bi.md`](./011-bi.md) | BI | Concluído |
| 012 | [`012-ia.md`](./012-ia.md) | IA | Concluído |
| 013 | `013-pneus.md` | Pneus | Planejado — sequência renumerada para seguir a ordem real pedida (Financeiro logo após Manutenção); Pneus fica como complemento |

> Renumerado a partir do Lote 7: a sequência original deste índice (escrita antes do Lote 6)
> previa Pneus em 006, mas o pedido real seguiu direto para Financeiro — corrigido aqui para
> refletir a ordem verdadeira, em vez de deixar o índice desatualizado (mesmo cuidado já tomado com
> `HIGH_VOLUME_ENTITIES.md`).

## Mapeamento Tipo Conceitual → Tipo SQL

Referência única, não repetida em cada arquivo (mesmo princípio de D069/D180 aplicado a tipos):

| Tipo Conceitual (Data Dictionary, [`../dictionary/README.md`](../dictionary/README.md)) | Tipo SQL (PostgreSQL) |
|---|---|
| Texto Curto | `TEXT` |
| Texto Longo | `TEXT` |
| Inteiro | `INTEGER` (ou `BIGINT` em contadores de altíssimo volume) |
| Decimal | `NUMERIC(p,s)` — precisão/escala definida por coluna |
| Percentual | `NUMERIC(5,2)` |
| Monetário | `NUMERIC(14,2)` + moeda implícita BRL (D075) — coluna de moeda só quando a entidade já prevê multi-moeda |
| Data | `DATE` |
| Data/Hora | `TIMESTAMPTZ` (ver [`../TIMESTAMP_STRATEGY.md`](../TIMESTAMP_STRATEGY.md)) |
| Booleano | `BOOLEAN` |
| Enum | `ENUM` físico nomeado `<tabela>_<coluna>_enum` (ver [`../NAMING_CONVENTION.md`](../NAMING_CONVENTION.md)) |
| UUID (conceitual) | `UUID` |
| Referência | `UUID` (FK, `<entidade>_id`) |
| Arquivo / Imagem | `UUID` (`<nome>_arquivo_id`) — referência lógica ao Storage (MinIO/S3, D107); sem FK de banco, o Storage não é uma tabela do PostgreSQL |
| Localização | `GEOGRAPHY(Point, 4326)` (PostGIS, D173) |
| Time Series | Não é um tipo de coluna — é uma classificação de tabela inteira (partição por `tenant_id` + data, D179) |
| JSON Estruturado | `JSONB` |

## Como este documento cresce

Um arquivo por vez, aprovação explícita antes do próximo — mesmo ritmo do Modelo de Domínio e do
Data Dictionary Funcional.
