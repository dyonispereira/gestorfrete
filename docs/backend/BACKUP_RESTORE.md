# BACKUP_RESTORE.md — Backup e Restore do Postgres

V1 Operational Hardening — item de INFRA pedido explicitamente pelo usuário. Escopo mínimo: o
Postgres é o único armazenamento com estado de negócio que não pode ser reconstruído (`viagens`,
`contas_pagar`/`contas_receber`, `ctes`/`mdfes`, `logs_auditoria`, tudo). Redis (idempotência,
`IDEMPOTENCY.md`) e RabbitMQ são caches/filas efêmeras por natureza — perdê-los não perde dado de
negócio, não fazem parte deste documento. MinIO (uploads/documentos) tem sua própria estratégia de
replicação de bucket, fora de escopo aqui (fica registrado como gap, não resolvido nesta rodada).

Não existia nenhuma estratégia de backup documentada ou automatizada antes deste documento — P0
registrado no Go-Live Audit. **Pilot Hardening Final, Parte 1**: fechado — o script abaixo existe
de verdade (`scripts/backup.sh`), não é mais só um bloco de bash dentro deste `.md`.

## `pg_dump` automatizado

Script real: [`scripts/backup.sh`](../../scripts/backup.sh). Formato `custom` (`-Fc`) — comprime,
permite restore seletivo (schema/tabela específica) e restore paralelo, ao contrário de um dump
`.sql` texto puro. Falha explicitamente (`exit 1`, sem fallback silencioso) se `DATABASE_URL_SYNC`
não estiver definida; nunca hardcoda credencial. `GESTORFRETE_BACKUP_RETENTION_DAYS` (novo,
default `35`) controla a poda ao final de cada execução — ver seção Retenção abaixo.

Agendamento: `cron`/systemd timer diário fora do horário de pico de tráfego (a definir por
ambiente de produção real — não existe ainda um ambiente de produção real para calibrar isso).
Local: `docker-compose.yml`/`infra/` não tem nenhum serviço de agendamento hoje — este script roda
fora dos containers, num host com `pg_dump` da mesma major version do Postgres do
`docker-compose.yml` (`postgis/postgis:16-3.4-alpine`, ou seja `pg_dump` 16.x) e acesso de rede ao
`postgres` (porta `5432`, já exposta no compose).

## Retenção

Ponto de partida documentado (mesmo espírito de `IDEMPOTENCY.md`'s 24h — valor inicial, ajustável
com necessidade real, não uma lei imutável):

| Idade do backup | Retenção |
|---|---|
| Últimos 7 dias | Todos os dumps diários |
| 8–35 dias | 1 dump semanal |
| 36+ dias | 1 dump mensal, por 12 meses |

Poda simples por idade de arquivo (não a tiering diário/semanal/mensal completa — mesma
simplificação já documentada), executada automaticamente ao final de `scripts/backup.sh`, com o
número de dias controlável via `GESTORFRETE_BACKUP_RETENTION_DAYS`.

## Localização/configuração por ambiente

| Variável | Local (`docker-compose.yml`) | Produção (futura) |
|---|---|---|
| `GESTORFRETE_BACKUP_DIR` | `./backups` (bind mount, fora do volume `postgres_data`) | Bucket S3-compatible separado do banco — nunca no mesmo host físico do Postgres (backup que mora no mesmo disco que falha não é backup) |
| `DATABASE_URL_SYNC` | `postgresql://gestorfrete:gestorfrete@localhost:5432/gestorfrete` | Lido de secret manager, nunca hardcoded — mesmo princípio já aplicado a `Settings.jwt_secret_key`/`database_url` (`core/config/settings.py`), que hoje só têm defaults fracos, sem guard de produção (gap relacionado, registrado no Go-Live Audit, não fechado por este documento) |

## Procedimento de restore

Script real: [`scripts/restore.sh`](../../scripts/restore.sh) `<caminho-do-dump>`. Nunca toca no
banco vivo — cria (`createdb -T template0`, evita um problema de metadado de collation observado
no `postgis/postgis:16-3.4-alpine` local) um banco descartável `<dbname>_restore_test`, restaura
(`pg_restore --clean --if-exists --no-owner`), valida (`alembic_version` + contagem de linhas em
`viagens`/`contas_pagar`/`contas_receber`/`logs_auditoria`) e imprime tudo. Promover para o banco
vivo (troca de `DATABASE_URL` + restart, nunca um `DROP DATABASE` automático) continua sendo uma
decisão manual, deliberadamente fora do script.

## Teste real de restore — executado nesta rodada, não só documentado

Backup nunca testado é backup que não existe de fato — a falha só aparece quando já é tarde demais.
[`scripts/verify_backup_restore.sh`](../../scripts/verify_backup_restore.sh) automatiza a prova
completa (cria um banco descartável → insere linhas conhecidas → `backup.sh` → corrompe/apaga as
linhas originais → `restore.sh` → confirma que os valores ORIGINAIS, não os corrompidos, voltaram)
e foi executado de ponta a ponta nesta rodada, duas vezes:

1. **Prova de mecanismo** (schema mínimo, dados sintéticos): 3 linhas conhecidas inseridas, 1
   corrompida (`UPDATE`) e 1 apagada (`DELETE`) depois do backup — o restore trouxe as 3 linhas
   originais de volta, exatamente como gravadas antes da corrupção. Saída real:
   ```
   PROVA OK — dados originais recuperados integralmente:
     1,viagem-conhecida-1,1234.56
     2,viagem-conhecida-2,7890.12
     3,viagem-conhecida-3,555.55
   ```
2. **Prova contra o schema real** (`backup.sh`/`restore.sh` direto, sem o wrapper de corrupção
   sintética, contra o banco de desenvolvimento local): dump de 7.8MB; restore produziu
   `alembic_version = 61bb63affb03` e as mesmas contagens do banco de origem (`viagens: 210`,
   `contas_pagar: 176`, `contas_receber: 9`, `logs_auditoria: 73865`) — restore fiel ao schema real
   da aplicação, não só a uma tabela de teste isolada.

Executado neste ambiente via `docker exec` no container `postgres` (o host de desenvolvimento não
tem `pg_dump`/`pg_restore`/`createdb` instalados — os scripts em si não assumem Docker, só exigem
esses binários no PATH e `DATABASE_URL_SYNC` alcançável, conforme já documentado acima).

**Disciplina operacional exigida a partir daqui**: rodar `verify_backup_restore.sh` (ou o
procedimento manual equivalente) pelo menos uma vez por ciclo de retenção (mensal) contra o
ambiente real do piloto, como rotina operacional recorrente — não como um evento único desta
rodada. Sem essa disciplina, a prova acima vale para o dia em que foi rodada, não para sempre.

## Fora de escopo desta rodada (não esquecido)

- Backup do bucket MinIO (uploads/documentos) — precisa de replicação/versionamento de objeto,
  mecanismo diferente de `pg_dump`.
- Point-in-time recovery (WAL archiving/`pgbackrest`) — o `pg_dump` diário acima cobre o caso de
  recuperação de desastre completo, não "recuperar para as 14h32 de terça"; PITR fica para quando
  o volume real de transações em produção justificar o investimento operacional adicional.
- Automação real do agendamento (cron/systemd/job de CI) — o script acima é o contrato, não ainda
  amarrado a um executor automático nesta rodada.
