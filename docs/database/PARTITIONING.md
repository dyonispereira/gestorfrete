# PARTITIONING.md — Política Operacional de Particionamento

Não é um catálogo de "quais tabelas têm `PARTITION BY`" (isso já está em [`INDEXES.md`](./INDEXES.md)
categoria 6) — é a política operacional completa: por que uma tabela é particionada, como novas
partições nascem, quanto tempo cada dado fica quente, como ele esfria, e o que acontece quando algo
dá errado. Primeira aplicação de D200 (auditar a DDL literal antes de fechar o documento) já rendeu
resultado antes da primeira linha deste catálogo ser escrita — ver "Achados" abaixo.

## Achados ao preparar este documento (D201)

Comparando a redação original de `DATABASE_ARCHITECTURE.md`/D179 ("particiona por `tenant_id`
(hash) + data, seção 4") contra os `PARTITION BY RANGE` reais dos 12 arquivos `relational/`:

1. **Nenhuma tabela usa `HASH (tenant_id)`** — todas particionam só por data. Mantido assim
   (correto, não um gap): `UUID` não tem ordem útil para hash orientado a retenção, e isolamento
   por tenant já vem do índice líder `tenant_id` em toda consulta (`INDEXES.md` categoria 4).
   `DATABASE_ARCHITECTURE.md` foi corrigido para descrever o que foi de fato implementado.
2. **`Ocorrência` é "Alto" volume em `HIGH_VOLUME_ENTITIES.md`, mas `ocorrencias` não é
   particionada** — mantido assim: é registrada por ação humana (poucas linhas por Viagem), não um
   fluxo técnico automático. Critério refinado na seção 1 abaixo.
3. **`inferencias_ia`, estruturalmente idêntica a `eventos_fiscais` (log técnico de execução com
   `duracao_ms` gerado), estava sem particionamento por descuido** — corrigida agora
   (`relational/012-ia.md`), particionada por `data_hora_inicio`. Nota técnica pendente: é a única
   tabela particionada referenciada por FK `NOT NULL` de outras 5 tabelas (`sugestoes_ia`,
   `predicoes_ia`, `classificacoes_ia`, `anomalias_detectadas`, `leituras_visao_computacional`) — em
   PostgreSQL real, o PK precisaria incluir a coluna de partição para isso ser 100% válido; mesma
   simplificação já aceita nas outras 9 tabelas particionadas (nenhuma delas é referenciada por FK),
   mas ali é inofensiva porque nada aponta para elas. Registrado como pendência técnica explícita
   para `MIGRATION_ORDER.md`/implementação real — não resolvida silenciosamente, não ignorada.

---

## 1. Critério de escolha

**"Alto"/"Muito Alto" volume (D049, [`HIGH_VOLUME_ENTITIES.md`](../information-model/HIGH_VOLUME_ENTITIES.md))
é necessário, mas não suficiente.** O critério real, com os quatro fatores que importam:

| Fator | Pergunta | Exemplo que qualifica | Exemplo que não qualifica |
|---|---|---|---|
| Volume sustentado | Cresce continuamente, sem teto natural por tenant? | `posicoes_veiculo` (um ping a cada N segundos, para sempre) | `ocorrencias` (poucas por Viagem, a Viagem tem fim) |
| Natureza técnica/automática | É gerado por máquina/integração, não por decisão humana pontual? | `heartbeats`, `eventos_fiscais` | `ocorrencias` (reportada por motorista/despachante) |
| Padrão de consulta sempre limitado no tempo | A aplicação sempre lê "últimos N dias/últimas M leituras", nunca "todo o histórico de uma vez"? | `leituras_telemetria` | Tabelas mestre (nunca são "últimos N dias") |
| Retenção diferenciada do dado bruto | O dado bruto pode ser descartado/arquivado bem antes do restante do sistema? | GPS bruto (90 dias, depois só agregado — [`007-DATA_RETENTION.md`](../information-model/007-DATA_RETENTION.md)) | Dados mestre (retenção indefinida por natureza) |

Uma tabela só é particionada quando **pelo menos três dos quatro fatores** se aplicam. `Ocorrência`
e `Medição de Pneu` (ainda não modelada — Pneus adiada para `013-pneus.md`, ver
[`relational/README.md`](./relational/README.md)) são "Alto" volume mas falham em natureza
técnica/automática e em padrão de consulta — por isso não entram na lista abaixo, mesmo citadas em
`HIGH_VOLUME_ENTITIES.md`. Se o volume real observado em produção divergir do estimado, a tabela
entra nesta lista depois — nunca é particionada "por garantia".

## 2. Tabelas particionadas atualmente

10 tabelas, confirmadas por `PARTITION BY RANGE` literal nos arquivos `relational/` (D200):

| Tabela | Coluna de partição | Motivo | Arquivo |
|---|---|---|---|
| `viagem_status_history` | `data_hora` | Histórico de status de Viagem — uma linha por transição, cresce com todo o volume operacional | `relational/003-operacao.md` |
| `leituras_hodometro` | `data_hora` | Leitura periódica de hodômetro por veículo | `relational/004-frota.md` |
| `eventos_fiscais` | `data_hora_inicio` | Log técnico de toda comunicação com SEFAZ/ANTT (D105) | `relational/007-fiscal.md` |
| `posicoes_veiculo` | `capturado_em` | GPS bruto — a maior tabela do sistema em volume (D191) | `relational/008-rastreamento.md` |
| `leituras_telemetria` | `capturado_em` | Sensor EAV (D120) — uma linha por sensor por instante (D191) | `relational/008-rastreamento.md` |
| `heartbeats` | `recebido_em` | Sinal técnico de conectividade — **exceção documentada a D191**: particiona por `recebido_em`, não `capturado_em`, porque o equipamento pode não informar captura confiável | `relational/008-rastreamento.md` |
| `eventos_rastreamento` | `data_hora` | Evento derivado (excesso de velocidade, entrada/saída de cerca) — "Alto" volume, detectado pelo sistema | `relational/008-rastreamento.md` |
| `execucoes_job` | `data_hora_inicio` | Log de execução de job assíncrono — técnico, append-only | `relational/010-administracao.md` |
| `logs_auditoria` | `data_hora` | Trilha de auditoria completa da plataforma (D007/D176) | `relational/010-administracao.md` |
| `inferencias_ia` | `data_hora_inicio` | Log técnico de execução de inferência de IA (D201) | `relational/012-ia.md` |

## 3. Estratégia temporal

**Mensal é o padrão** para as 10 tabelas — nenhuma usa granularidade semanal ou diária. Motivo:
mensal equilibra o número de partições (12/ano por tabela, não 52/365) com o tamanho de cada
partição (grande o bastante para `VACUUM`/`ANALYZE` valerem a pena rodar uma vez, pequena o
bastante para uma consulta de "últimos 30 dias" tocar no máximo 2 partições).

**Exceção — `heartbeats` particiona por `recebido_em`, não `capturado_em`** (documentada
explicitamente em `relational/008-rastreamento.md` e formalizada em D191): o equipamento de
rastreamento pode enviar um heartbeat sem informar o instante exato de captura de forma confiável
— `recebido_em` (quando o servidor recebeu) é sempre populado, `capturado_em` não. Particionar pela
coluna que é sempre confiável evita linhas "perdidas" numa partição errada por falta de dado.

## 4. Criação automática de partições

**Decisão**: um job assíncrono próprio, rastreado como qualquer outro em `execucoes_job` (o
sistema audita a própria manutenção com a mesma infraestrutura que audita jobs de negócio) —
não uma migration manual, não uma rotina administrativa ad-hoc.

- **Quem executa**: um processo agendado (`tipo_job = 'CRIACAO_PARTICAO'` em `execucoes_job`),
  rodando mensalmente, um mês antes da virada — não a aplicação em tempo de escrita (uma inserção
  nunca deve ser o gatilho de criar a partição que ela mesma precisa).
- **O que faz**: para cada uma das 10 tabelas da seção 2, verifica se a partição do mês-alvo
  (ver seção 5, look-ahead) já existe; se não, executa o `CREATE TABLE ... PARTITION OF ...` e
  registra sucesso/falha em `execucoes_job` — a mesma tabela que este job ajuda a particionar
  audita a própria execução.
- **Onde vive no código**: `infrastructure/` do bounded context `platform`/`integration` (a
  confirmar exatamente no Backend, não decidido aqui) — não é lógica de domínio, é infraestrutura
  pura.
- **Idempotência**: `CREATE TABLE IF NOT EXISTS`-style (ou verificação prévia via catálogo do
  PostgreSQL, `pg_partitions`/`information_schema`) — rodar o job duas vezes no mesmo mês nunca
  deve falhar nem duplicar.

## 5. Partição futura (look-ahead)

**Política: mês atual + 2 meses futuros sempre existentes** — ou seja, a qualquer momento, a
partição do mês corrente e das duas próximas já estão criadas antes que a primeira escrita daquele
mês aconteça. Número escolhido como ponto de partida razoável (folga suficiente para absorver uma
falha do job de um mês sem interromper escritas — seção 12), não uma lei imutável: **ajustável em
produção conforme o comportamento real do job de criação** (ex.: se o job de criação já se mostrar
100% confiável, 1 mês de folga basta; se a infraestrutura tiver janelas de manutenção maiores,
pode-se preferir 3).

## 6. Retenção

Vem de [`007-DATA_RETENTION.md`](../information-model/007-DATA_RETENTION.md) — não reinventada
aqui, só aplicada às 10 tabelas particionadas. Quatro categorias, nunca misturadas:

| Categoria | O que inclui | Retenção ativa | Depois de expirar | Status |
|---|---|---|---|---|
| **Operacional** | `posicoes_veiculo`, `leituras_telemetria`, `heartbeats`, `leituras_hodometro` | 90 dias em granularidade bruta (dado agregado — velocidade média, km/dia — mantido permanentemente à parte, fora deste particionamento) | Arquivamento/descarte da partição bruta após agregação confirmada | Proposto |
| **Técnica** | `execucoes_job`, `eventos_rastreamento` | Não é dado de negócio nem fiscal — 90 dias de logs técnicos como referência inicial (mesmo critério de "logs de sistema/aplicação" em `007-DATA_RETENTION.md`) | Descartável | Proposto |
| **Fiscal** | `eventos_fiscais` | Acompanha o documento fiscal que audita (CT-e/MDF-e/CIOT) — referência comum de 5 anos | Arquivamento a frio, nunca exclusão | **A validar juridicamente** |
| **Auditoria** | `logs_auditoria`, `viagem_status_history` | Mínimo igual à retenção do dado auditado — na prática, permanente para a maioria; proposta operacional de 2 anos ativo + arquivado | Arquivamento a frio | Proposto, prazo mínimo **a validar** conforme compliance |
| — | `inferencias_ia` | Acompanha a política de retenção de IA (retraining/auditoria de modelo, D192) — ainda não fixada em `007-DATA_RETENTION.md` | — | **A validar** — adicionar a `007-DATA_RETENTION.md` quando a estratégia de retraining for decidida |

Nenhum prazo aqui é menor que a exigência legal aplicável (princípio já fixado em
`007-DATA_RETENTION.md`) — quando um prazo estiver marcado "a validar", a partição correspondente
**não é elegível para arquivamento/descarte automático** até a confirmação jurídica acontecer.

## 7. Arquivamento (Hot / Warm / Archive)

| Camada | O que contém | Onde vive | Consultada por |
|---|---|---|---|
| **Hot** | Partição do mês corrente + os últimos 1–2 meses completos | PostgreSQL operacional, mesmo storage de produção | Aplicação em tempo real (painel operacional, app motorista) |
| **Warm** | Partições dentro do período de retenção ativa (seção 6) mas fora da janela Hot | PostgreSQL operacional, possivelmente tablespace mais barato (a definir em infraestrutura) | Consultas ocasionais, relatórios, BI (`analytics`) |
| **Archive** | Partições além da retenção ativa, ainda dentro do prazo legal/de compliance | Fora da camada operacional — export para armazenamento frio (MinIO/S3, D107, mesmo padrão já usado para arquivos) via `DETACH PARTITION` + `pg_dump`/export columnar, depois `DROP` da partição detached | Só sob demanda excepcional (auditoria, disputa fiscal, ordem judicial) |

`DETACH PARTITION` (não `DROP` direto) é o mecanismo: destacar a partição do particionamento ativo
é instantâneo (não bloqueia a tabela-mãe), o export/cópia acontece com a partição já isolada, e só
depois de export confirmado ela é descartada da camada operacional.

## 8. Compressão

**Avaliada, não presumida** — nem toda tabela particionada ganha compressão automaticamente:

| Tabela | Compressão? | Abordagem |
|---|---|---|
| `posicoes_veiculo`, `leituras_telemetria` | **Sim, forte candidata** | Maior volume do sistema, dado numérico repetitivo (ótimo para compressão colunar). Caminho recomendado: `TimescaleDB` (o projeto já é "TimescaleDB-ready via particionamento nativo", D173) — sua compressão nativa por chunk é o encaixe mais direto, sem reescrever a estratégia de particionamento já feita aqui |
| `heartbeats` | Sim, mesmo caminho | Payload pequeno mas volume altíssimo — mesmo raciocínio |
| `eventos_rastreamento`, `eventos_fiscais`, `execucoes_job`, `logs_auditoria`, `inferencias_ia` | Avaliar depois de medir volume real | Volume "Alto", não "Muito Alto" — compressão traz benefício menor; decisão adiada para quando houver dado de produção real, não estimado |
| `viagem_status_history`, `leituras_hodometro` | Não prioritário | Volume "Médio"/"Alto" mas historicamente o de crescimento mais previsível — reavaliar só se a estimativa de volume mudar |

Nenhuma extensão de compressão é ativada nesta etapa (é decisão de infraestrutura de produção, não
de modelagem) — a tabela acima é o critério de priorização para quando essa etapa acontecer.

## 9. Índices locais

Já documentado com detalhe em [`INDEXES.md`](./INDEXES.md) categoria 6 — resumo aqui, não repetido
linha a linha (D069-style): toda partição herda automaticamente 100% dos índices declarados na
tabela-mãe (comportamento nativo do `PARTITION BY RANGE` do PostgreSQL) — nenhum índice "local"
precisa ser criado manualmente por partição, incluindo o índice composto `(entidade_id, timestamp)`
do padrão D191 e o `GiST` de `posicoes_veiculo.localizacao` (D197). O job de criação de partição
(seção 4) não precisa saber nada sobre índices — só precisa criar a partição, o PostgreSQL cuida do
resto.

## 10. VACUUM / ANALYZE

Política qualitativa (valores exatos de configuração ficam para a infraestrutura de produção, não
fixados aqui):

- **Partição do mês corrente (Hot, ainda recebendo escrita)**: `autovacuum` padrão do PostgreSQL é
  suficiente — a partição é pequena o bastante no início do mês para não ser um problema.
- **Partição de mês fechado (Warm, só leitura a partir de agora)**: uma vez que o mês vira e a
  partição para de receber `INSERT`, ela se torna candidata a um `VACUUM (ANALYZE)` manual único
  (não repetido) para consolidar estatísticas — não precisa de `autovacuum` contínuo depois disso,
  porque não há mais `UPDATE`/`DELETE` gerando linhas mortas (todas as 10 tabelas desta lista são
  append-only, D001/D109).
- **Partição prestes a ser destacada (seção 7)**: um `ANALYZE` final antes do `DETACH PARTITION`
  garante que a cópia/export tenha estatísticas corretas, mas a partição detached não participa
  mais do `autovacuum` da tabela-mãe.
- Nenhum valor de `autovacuum_vacuum_scale_factor`/`autovacuum_analyze_scale_factor` específico é
  fixado aqui — depende de medição real em produção, registrado como pendência de infraestrutura,
  não de modelagem.

## 11. Monitoramento

Indicadores que qualquer painel operacional de banco (ou dashboard interno do próprio `analytics`,
se optarem por dogfood) precisa expor:

| Indicador | Por quê |
|---|---|
| Tamanho por partição (bytes) | Detecta crescimento anômalo por mês antes que vire problema |
| Crescimento diário (linhas/dia por tabela particionada) | Valida se a estimativa de volume (`HIGH_VOLUME_ENTITIES.md`) continua correta |
| Linhas por partição | Mesma finalidade, granularidade mensal |
| Partições futuras existentes (contagem de meses à frente já criados) | Confirma que o look-ahead (seção 5) está sendo mantido pelo job |
| Partições ausentes (gap na sequência mensal) | Sinal direto de falha do job de criação (seção 12) |
| Consultas lentas contra tabela particionada | Detecta consulta que não está aproveitando partition pruning (ex.: filtro sem a coluna de partição) |
| Retenção pendente (partições além do prazo de retenção ativa ainda não arquivadas) | Sinal de que o processo de arquivamento (seção 7) está atrasado |

## 12. Falha operacional

| Cenário | O que acontece | Mitigação |
|---|---|---|
| Partição futura não existe no momento da escrita | PostgreSQL rejeita o `INSERT` com erro (`no partition of relation found for row`) — falha dura, não silenciosa | Look-ahead de 2 meses (seção 5) existe exatamente para isso nunca acontecer em operação normal; ver também a rede de segurança abaixo |
| Job de criação de partição falha (ex.: erro de infraestrutura, falta de permissão) | Sem intervenção, o look-ahead encolhe mês a mês até esgotar e cair no cenário acima | `execucoes_job` já registra toda execução/falha (D007-style auditoria) — alerta automático quando `tipo_job = 'CRIACAO_PARTICAO'` falha ou não roda no mês esperado (ver monitoramento, seção 11) |
| Armazenamento fica cheio | Partições Warm/Archive não migradas a tempo consomem disco operacional | Processo de arquivamento (seção 7) precisa rodar antes do limite, não depois — monitorar tamanho por partição é o sinal antecedente |
| Retenção não executa (job de arquivamento atrasado) | Dado permanece na camada operacional além do previsto — não é uma falha de integridade, é uma falha de custo/performance | Indicador "retenção pendente" (seção 11) existe para isso ser visível antes de virar incidente |
| Uma partição fica muito maior que o esperado (ex.: bug gerando volume 10x) | Degradação de performance de toda consulta contra aquele mês | Indicador "crescimento diário" (seção 11) detecta a anomalia; resposta é investigação de aplicação, não uma ação de particionamento |
| **Rede de segurança recomendada**: uma partição `DEFAULT` (`PARTITION ... DEFAULT`) em cada uma das 10 tabelas, capturando qualquer linha fora do intervalo das partições nomeadas — nunca deveria receber dados em operação normal (o look-ahead cobre isso), mas transforma uma falha catastrófica (`INSERT` rejeitado, sistema fora do ar) numa anomalia observável (linha foi para o "lugar errado" mas não se perdeu). **Não implementada nos `relational/*.md` ainda** — recomendação para `MIGRATION_ORDER.md`/implementação real, mesmo espírito de D200 (decisão explícita, não assumida). | | |

---

## Tabela final consolidada

| Tabela | Estratégia | Coluna | Frequência | Motivo | Retenção | Compressão | Estado |
|---|---|---|---|---|---|---|---|
| `viagem_status_history` | RANGE | `data_hora` | Mensal | Histórico de status de Viagem | Auditoria — proposto 2 anos ativo + arquivado, prazo mínimo a validar | Não prioritário | Implementado no modelo |
| `leituras_hodometro` | RANGE | `data_hora` | Mensal | Leitura periódica de hodômetro | Operacional — 90 dias bruto + agregado permanente | Não prioritário | Implementado no modelo |
| `eventos_fiscais` | RANGE | `data_hora_inicio` | Mensal | Log técnico SEFAZ/ANTT | Fiscal — ~5 anos, a validar juridicamente | Avaliar com volume real | Implementado no modelo |
| `posicoes_veiculo` | RANGE | `capturado_em` | Mensal | GPS bruto, maior volume do sistema | Operacional — 90 dias bruto + agregado permanente | Forte candidata (TimescaleDB) | Implementado no modelo |
| `leituras_telemetria` | RANGE | `capturado_em` | Mensal | Sensor EAV, alta frequência | Operacional — 90 dias bruto + agregado permanente | Forte candidata (TimescaleDB) | Implementado no modelo |
| `heartbeats` | RANGE | `recebido_em` (exceção D191) | Mensal | Sinal técnico de conectividade | Técnica — 90 dias | Forte candidata (TimescaleDB) | Implementado no modelo |
| `eventos_rastreamento` | RANGE | `data_hora` | Mensal | Evento derivado (velocidade, geofence) | Técnica — 90 dias | Avaliar com volume real | Implementado no modelo |
| `execucoes_job` | RANGE | `data_hora_inicio` | Mensal | Log de execução de job assíncrono | Técnica — 90 dias | Avaliar com volume real | Implementado no modelo |
| `logs_auditoria` | RANGE | `data_hora` | Mensal | Trilha de auditoria da plataforma | Auditoria — proposto 2 anos ativo + arquivado, prazo mínimo a validar | Avaliar com volume real | Implementado no modelo |
| `inferencias_ia` | RANGE | `data_hora_inicio` | Mensal | Log técnico de execução de IA | A validar — política de retenção de IA ainda não fixada | Avaliar com volume real | Implementado no modelo (D201) |
| Partição `DEFAULT` (rede de segurança, todas as 10 tabelas) | — | — | — | Falha operacional (seção 12) | — | — | **Planejado** — não implementado nos `relational/*.md` ainda |
| Job de criação automática de partição | — | — | Mensal, com 2 meses de look-ahead | Seção 4/5 | — | — | **Planejado** — decisão tomada aqui, implementação no Backend |
| `Medição de Pneu` particionada | — | — | — | Ainda sem tabela física (Pneus adiado, `013-pneus.md`) | — | — | **Futuro** |
| `HASH (tenant_id)` como camada adicional de particionamento | — | — | — | Avaliado e descartado (D201) — isolamento por tenant já resolvido por índice | — | — | **Descartado**, não Futuro |

## Como este documento cresce

Estável enquanto o Modelo Relacional não muda. Toda tabela nova classificada "Alto"/"Muito Alto"
volume passa pelo critério da seção 1 antes de decidir particionar — nunca automaticamente só pela
classificação de volume. Próximo documento da sequência: [`MIGRATION_ORDER.md`](./MIGRATION_ORDER.md)
(ondas de migration por dependência de módulo) — primeira aplicação real de D200 num documento onde
o erro tem consequência direta (ordem errada quebra a criação do schema, não só a documentação).
