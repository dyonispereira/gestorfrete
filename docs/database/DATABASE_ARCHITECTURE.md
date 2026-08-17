# DATABASE_ARCHITECTURE.md — Arquitetura Física do Banco

A "constituição" do banco do GestorFrete: a decisão de motor, a arquitetura em camadas e como os
173 entidades do Modelo de Domínio se distribuem fisicamente. As regras de nomenclatura, tenancy,
auditoria, soft delete, UUID e timestamp têm cada uma seu próprio documento (ver
[`README.md`](./README.md)) — este arquivo as referencia, não as repete.

## 1. Motor de banco: PostgreSQL 16+ (D173)

| Necessidade do GestorFrete | Recurso do PostgreSQL |
|---|---|
| Atributos "JSON Estruturado" do dicionário (D068) — Endereço, Layout de Dashboard, Payload de Evento Fiscal, etc. | `JSONB` nativo, indexável (`GIN`) |
| Atributos "Localização" (D068) — Posição de Veículo, Cerca Eletrônica, Praça de Pedágio | `PostGIS` — tipos geográficos, índices espaciais (`GIST`), consultas de distância/contenção nativas |
| Time Series de altíssimo volume (Posição de Veículo, Telemetria, Log de Auditoria — ver [`../information-model/HIGH_VOLUME_ENTITIES.md`](../information-model/HIGH_VOLUME_ENTITIES.md)) | Particionamento nativo (`PARTITION BY RANGE`) hoje; `TimescaleDB` como extensão futura, sem mudar o modelo lógico — só a camada de armazenamento por baixo |
| Multi-tenancy lógico (D005/D006) | `Row-Level Security` disponível como camada de defesa adicional além do filtro por `tenant_id` na aplicação (avaliar na modelagem física de cada tabela, não decidido globalmente ainda) |
| Operação SaaS 24/7, milhões de registros, 1000+ tenants | Maturidade, replicação, extensões de confiabilidade (WAL, backup incremental) já consolidadas no ecossistema |

Não é uma escolha de tecnologia por modismo — cada recurso do PostgreSQL listado acima resolve um
tipo de dado que o Data Dictionary Funcional já exigia (D068, D049/D050) antes mesmo desta decisão
existir.

## 2. Arquitetura em camadas

```
                         GestorFrete SaaS
                               │
                               │
                        Application Layer
                    (FastAPI — Clean Architecture,
                     ver ../architecture/)
                               │
                               │
                      PostgreSQL 16+ Cluster
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
      Core                Time Series              Storage
        │                      │                      │
  Dados Mestres e         GPS, Telemetria,      Referências a arquivos
  Transacionais           Medição de Pneu,      (MinIO/S3) — nunca
  (Cadastros, Viagem,     Log de Auditoria      binário nas tabelas
  Financeiro, Fiscal,     (particionados por    (D107) — as tabelas
  Administração, BI,      tenant_id + data,     acima só guardam
  IA — tabelas comuns,    D179)                 arquivo_id/URL
  índices B-tree padrão)
```

A camada "Storage" na prática não é um banco separado — é MinIO/S3 (já decidido na fundação de
infraestrutura do projeto); aparece aqui porque toda tabela com um atributo `Arquivo`/`Imagem`
(D068) guarda apenas a referência, nunca o binário (D107), então arquitetonicamente é tratada como
uma camada própria de armazenamento, fora do PostgreSQL.

## 3. Separação de dados em três grupos (D178)

Aplicação física direta de D036 (Referência × Operacional) e D037 (Mestre × Histórica), já usados em
todo o Data Dictionary Funcional:

| Grupo | O que é | Exemplos | Estratégia física |
|---|---|---|---|
| **Dados Mestres** | Cadastros que mudam pouco | `motoristas`, `veiculos_tracionadores`, `clientes`, `fornecedores` | Tabela comum, índice B-tree em `id`/`codigo`/`tenant_id`, sem particionamento |
| **Dados Transacionais** | Movimento operacional do dia a dia | `viagens`, `ordens_servico`, `faturas`, `contas_pagar` | Tabela comum, índices em `tenant_id` + chaves de busca frequente (status, datas); volume moderado, não particionada de início — reavaliar por tenant conforme cresce |
| **Dados Históricos / Time Series** | Alto/altíssimo volume, quase sempre append-only | `posicoes_veiculo`, `leituras_telemetria`, `medicoes_pneu`, `logs_auditoria` | **Particionada desde a primeira migration** (D179, seção 4) — nunca tratada como tabela comum |

Esta separação já existia conceitualmente no Data Dictionary (Master Data/Transactional
Data/Histórica, D036/D037) — aqui ela vira decisão de schema físico, não um conceito novo.

## 4. Particionamento (D179)

Toda tabela classificada como "Muito Alto"/"Alto" volume e efetivamente de natureza técnica/Time
Series em [`../information-model/HIGH_VOLUME_ENTITIES.md`](../information-model/HIGH_VOLUME_ENTITIES.md)
é particionada por data (range), desde o dia da criação da tabela — nunca como tabela monolítica
"por enquanto, otimiza depois":

```
posicoes_veiculo
├── posicoes_veiculo_2026_01   (partição de janeiro/2026)
├── posicoes_veiculo_2026_02   (partição de fevereiro/2026)
└── ...
```

Motivo de particionar desde o início: para uma entidade de altíssimo volume (Posição de Veículo,
milhões de registros por mês em 1000+ tenants), reparticionar uma tabela já populada em produção é
uma migração cara e arriscada — o custo de decidir isso agora é muito menor do que corrigir depois.

**Correção (D201)**: a redação original desta seção descrevia particionamento por `tenant_id`
(hash) **+** data de captura (range) — um esquema de duas camadas nunca de fato implementado. Ao
escrever o Modelo Relacional (12 arquivos `relational/`), toda tabela particionada usou `PARTITION
BY RANGE` só na coluna de tempo, nunca uma camada adicional de `HASH (tenant_id)`. Isso é
correto, não um gap: `tenant_id` é `UUID` sem ordem natural (particionar por hash dele não ajuda
retenção/arquivamento, que é o motivo real de particionar aqui), e todo índice de consulta já leva
`tenant_id` como primeira coluna (categoria 4 de [`INDEXES.md`](./INDEXES.md)) — o isolamento por
tenant já é resolvido por índice, não precisa ser resolvido por partição também. Esta seção foi
corrigida para refletir o que foi de fato implementado, em vez de manter uma descrição de fundação
nunca revisitada. Detalhe completo de critério/retenção/arquivamento em
[`PARTITIONING.md`](./PARTITIONING.md).

## 5. Referência às demais regras físicas

| Regra | Documento |
|---|---|
| Nomenclatura de tabelas/colunas | [`NAMING_CONVENTION.md`](./NAMING_CONVENTION.md) |
| `tenant_id` obrigatório | [`TENANCY_MODEL.md`](./TENANCY_MODEL.md) |
| Chave técnica × código funcional | [`UUID_STRATEGY.md`](./UUID_STRATEGY.md) |
| Colunas de auditoria + `logs_auditoria` | [`AUDIT_MODEL.md`](./AUDIT_MODEL.md) |
| Soft delete | [`SOFT_DELETE_MODEL.md`](./SOFT_DELETE_MODEL.md) |
| Timestamps e fuso horário | [`TIMESTAMP_STRATEGY.md`](./TIMESTAMP_STRATEGY.md) |

## Como este documento cresce

Este arquivo é a constituição — muda raramente, só quando uma decisão física de escopo amplo for
necessária (ex: adoção efetiva de TimescaleDB, decisão de Row-Level Security). O detalhamento
tabela-a-tabela vive em `relational/NNN-categoria.md` (Lote 2 em diante), nunca aqui.
