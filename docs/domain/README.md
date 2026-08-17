# docs/domain — Índice do Modelo de Domínio

Este é o índice principal do Sprint 05 (Modelo de Domínio) do GestorFrete — o "negócio antes do
banco" (ver [`../product/DECISIONS.md`](../product/DECISIONS.md)). Substitui o plano original de um
único `DOMAIN_MODEL.md`: o modelo completo é grande demais (300+ páginas esperadas) para um
documento só, então esta pasta é organizada em várias frentes, todas indexadas aqui.

## Estrutura

```
docs/domain/
├── README.md                    (este arquivo — índice principal)
├── UBIQUITOUS_LANGUAGE.md        (dicionário oficial de nomenclatura — D028)
├── ENTITY_CATALOG.md             (índice raso de todas as entidades, por categoria)
├── OFFLINE_STRATEGY.md           (estratégia de Offline First seletivo — D039, ainda vazio)
├── NNN-categoria.md              (detalhamento completo das entidades de cada categoria)
└── shared/                       (documentos transversais a todas as entidades)
    ├── AGGREGATES.md              (a ser escrito — Aggregate Roots e o que contêm)
    ├── VALUE_OBJECTS.md           (a ser escrito — CPF, CNPJ, Placa, Dinheiro, etc.)
    ├── DOMAIN_EVENTS.md           (a ser escrito — EVENT_MAP.md formalizado por evento)
    └── INVARIANTS.md              (a ser escrito — regras de negócio do domínio)
```

Os documentos em `shared/` ficam separados dos arquivos `NNN-categoria.md` porque não pertencem a
uma única categoria de entidades — um Value Object como Dinheiro, ou uma regra de invariante, é
usado por dezenas de entidades ao mesmo tempo.

## Entidades por categoria

| # | Arquivo | Entidades catalogadas | Status |
|---|---|---|---|
| 001 | [Cadastros](./001-cadastros.md) | 18 (16 + Endereço/Documento do Motorista, D182/D183) | Concluído |
| 002 | [Operação](./002-operacao.md) | 14 | Concluído |
| 003 | [Frota](./003-frota.md) | 10 | Concluído |
| 004 | [Manutenção](./004-manutencao.md) | 8 | Concluído |
| 005 | [Pneus](./005-pneus.md) | 5 | Concluído |
| 006 | [Financeiro](./006-financeiro.md) | 11 (+ Centro de Custo, já em `001-cadastros.md`) | Concluído |
| 007 | [Fiscal](./007-fiscal.md) | 7 | Concluído |
| 008 | [Rastreamento](./008-rastreamento.md) | 9 (reconciliado de 8 — ver nota em `008-rastreamento.md`) | Concluído |
| 009 | [App (Motorista)](./009-app_motorista.md) | 5 (reconciliado de 6 — ver nota em `009-app_motorista.md`) | Concluído |
| 010 | [Administração (Plataforma)](./010-administracao.md) | 20 (reconciliado de 9 — ver nota em `010-administracao.md`) | Concluído |
| 011 | [BI](./011-bi.md) | 9 (reconciliado de 5 — ver nota em `011-bi.md`) | Concluído |
| 012 | [IA](./012-ia.md) | 8 (reconciliado de 4 — ver nota em `012-ia.md`) | Concluído |

Ver [`ENTITY_CATALOG.md`](./ENTITY_CATALOG.md) para os nomes de cada entidade antes de seu arquivo
de detalhe existir.

**Modelo de Domínio completo** — as 12 categorias planejadas estão com `Status: Concluído`. A partir
daqui, o par Domain → Data Dictionary segue por categoria (D101) até o Data Dictionary também estar
completo, e então o projeto avança para Modelo Lógico → Modelo Físico → OpenAPI (ver
[`../product/DECISIONS.md`](../product/DECISIONS.md), D101).

## O template oficial de entidade

Toda entidade documentada em um arquivo `NNN-categoria.md` segue este template, nesta ordem. Os
primeiros 18 campos valem desde `001-cadastros.md`; os 4 últimos (**Dependências obrigatórias**,
**Dependências proibidas**, **Dono da Timeline**, **Capacidade Offline**) foram adicionados a partir
do lote de `003-frota.md` em diante — arquivos anteriores ainda não os têm (ver nota de
inconsistência pendente abaixo).

1. Objetivo
2. Responsabilidades
3. O que não faz
4. Aggregate Root (ou indica de qual agregado é parte)
5. Bounded Context proprietário
6. Principais relacionamentos
7. Eventos que publica
8. Eventos que consome
9. Invariantes
10. Regras de negócio associadas
11. Estados (quando houver)
12. Auditoria
13. Linha do tempo (Timeline Universal)
14. Anexos suportados
15. Comentários suportados
16. KPIs relacionados
17. Documentos canônicos relacionados
18. Evoluções futuras previstas
19. **Dependências obrigatórias** — de quais outras entidades esta depende para existir/fazer sentido
20. **Dependências proibidas** — quais entidades esta **nunca** pode depender (mantém os bounded
    contexts limpos — ver [`../architecture/ddd.md`](../architecture/ddd.md))
21. **Dono da Timeline** — qual Aggregate Root controla a Timeline Universal (D022) desta entidade
22. **Capacidade Offline** — `Sim` / `Não` / `Consulta Offline` (D039)

> **Nota de inconsistência pendente**: `001-cadastros.md` e `002-operacao.md` (30 entidades) foram
> escritos antes dos campos 19–22 existirem. Ainda não foram retrofitados — fica para confirmação
> explícita antes de fazer, seguindo a disciplina de não gerar trabalho fora do lote combinado.

## Classificações conceituais (não são campos do template)

Duas decisões desta etapa classificam entidades sem exigir um campo próprio no template (ainda):

- **Referência × Operacional** (D036) — cadastros que mudam pouco vs. entidades transacionais.
- **Mestre × Histórica** (D037) — um registro ativo por identidade vs. tabelas append-only
  (`<Entidade>StatusHistory`, já em uso desde D017/D018/D021).
- **Snapshot Histórico** (D038) — algumas entidades (a começar pela Viagem, ver
  [`002-operacao.md`](./002-operacao.md)) guardam uma fotografia de dados relacionados no momento do
  uso, para nunca depender retroativamente de um cadastro que mudou depois.

## Ver também

- [`../product/DECISIONS.md`](../product/DECISIONS.md) — todas as decisões arquiteturais e de
  produto, incluindo as D027–D039 desta etapa.
- [`../flows/INDEX.md`](../flows/INDEX.md) — os Business Flows que motivam boa parte deste modelo.
