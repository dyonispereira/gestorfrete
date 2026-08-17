# docs/database — Modelagem Lógica e Física do Banco (Sprint 09)

A "Constituição do Banco" do GestorFrete — as regras que as 173 entidades do
[`../domain/`](../domain/) e os atributos do [`dictionary/`](./dictionary/) seguem ao virar tabelas
reais em PostgreSQL. Sequência oficial (D101, estendida): **Domain → Dictionary → Modelo Relacional
→ DER → SQL Migration**. Nada aqui contradiz o Data Dictionary Funcional — esta pasta traduz o que
já foi decidido para a linguagem física (nomes de tabela/coluna, tipos SQL concretos, índices,
particionamento), nunca redefine regra de negócio.

## Lote 1 — Fundação (este lote)

| Arquivo | Define |
|---|---|
| [`DATABASE_ARCHITECTURE.md`](./DATABASE_ARCHITECTURE.md) | Motor (PostgreSQL 16+), arquitetura em camadas, separação Mestre/Transacional/Histórico, particionamento |
| [`NAMING_CONVENTION.md`](./NAMING_CONVENTION.md) | snake_case, singular/plural, FKs, prefixos |
| [`TENANCY_MODEL.md`](./TENANCY_MODEL.md) | `tenant_id` obrigatório, exceção de Platform Reference Data |
| [`AUDIT_MODEL.md`](./AUDIT_MODEL.md) | Colunas de auditoria padrão + tabela `logs_auditoria` |
| [`SOFT_DELETE_MODEL.md`](./SOFT_DELETE_MODEL.md) | `excluido_em`/`excluido_por`, nunca `DELETE` físico |
| [`UUID_STRATEGY.md`](./UUID_STRATEGY.md) | `id` técnico × `codigo` funcional |
| [`TIMESTAMP_STRATEGY.md`](./TIMESTAMP_STRATEGY.md) | UTC, granularidade, exibição por fuso do tenant |

Todo arquivo `NNN-categoria.md` do Modelo Relacional (Lote 2 em diante) assume estas oito regras
como já resolvidas — nenhuma delas é repetida por tabela (mesmo princípio de D069 aplicado à camada
física).

## Estrutura completa planejada

```
docs/database/
├── README.md                    (este arquivo)
├── DATABASE_ARCHITECTURE.md      (Lote 1)
├── NAMING_CONVENTION.md          (Lote 1)
├── TENANCY_MODEL.md              (Lote 1)
├── AUDIT_MODEL.md                (Lote 1)
├── SOFT_DELETE_MODEL.md          (Lote 1)
├── UUID_STRATEGY.md              (Lote 1)
├── TIMESTAMP_STRATEGY.md         (Lote 1)
├── relational/                   (Lotes 2-10 — a partir daqui, um NNN-categoria.md por vez,
│   ├── 001-core.md                mesma ordem do Modelo de Domínio: Core/Cadastros/Operação/
│   ├── 002-cadastros.md           Frota/Manutenção/Financeiro/Fiscal/Tracking/BI-IA)
│   └── ...
├── DER.md                        (visão consolidada, populado ao final de cada lote relacional)
├── TABLES.md                     (índice de todas as tabelas físicas)
├── ENUMS.md                      (todos os tipos Enum físicos, com valores)
├── INDEXES.md                    (estratégia de índices por tabela)
└── MIGRATIONS.md                 (ordem e convenção das migrations Alembic-equivalentes)
```

`DER.md`, `TABLES.md`, `ENUMS.md`, `INDEXES.md` e `MIGRATIONS.md` já existiam como placeholders
vazios desde a fundação inicial do projeto (antes da metodologia sprint-a-sprint existir) — mantidos
vazios até serem alimentados pelos Lotes 2+, quando as tabelas reais começarem a existir.

## Progresso

- **Lote 1 (Fundação)**: Concluído.
- **Lote 2 (Modelo Relacional)**: em andamento — ver [`relational/README.md`](./relational/README.md)
  para o índice categoria a categoria (`001-core.md` concluído).

## Como este documento cresce

Um arquivo por vez, mesmo princípio de todo o projeto.
