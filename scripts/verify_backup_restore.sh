#!/usr/bin/env bash
# Pilot Hardening Final, Parte 1 — prova reproduzível de BACKUP → RESTORE → VALIDAÇÃO.
# Cria um banco descartável, insere dados conhecidos, faz backup, corrompe/apaga os dados
# originais, restaura o dump num segundo banco descartável e confirma que os valores originais
# (não os corrompidos) voltaram. Requer pg_dump/pg_restore/createdb/dropdb/psql no PATH e
# DATABASE_URL_SYNC apontando para um servidor Postgres alcançável (nunca cria/apaga nada no banco
# de aplicação em si — só bancos com sufixo "_verify_proof").
set -euo pipefail

: "${DATABASE_URL_SYNC:?DATABASE_URL_SYNC não definido — ex.: postgresql://user:pass@host:5432/gestorfrete.}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

without_scheme="${DATABASE_URL_SYNC#postgresql://}"
userpass="${without_scheme%%@*}"
hostportdb="${without_scheme#*@}"
export PGUSER="${userpass%%:*}"
export PGPASSWORD="${userpass#*:}"
hostport="${hostportdb%%/*}"
export PGHOST="${hostport%%:*}"
export PGPORT="${hostport#*:}"

PROOF_DB="gestorfrete_verify_proof"
PROOF_URL="postgresql://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/${PROOF_DB}"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "${WORK_DIR}"' EXIT

log() { echo "[verify_backup_restore.sh] $(date -u +%Y-%m-%dT%H:%M:%SZ) $*"; }

log "1/6 — criando banco descartável de prova: ${PROOF_DB}"
dropdb --if-exists "${PROOF_DB}"
createdb -T template0 "${PROOF_DB}"

log "2/6 — inserindo dados conhecidos"
psql -d "${PROOF_DB}" -v ON_ERROR_STOP=1 -c "
CREATE TABLE prova_backup (id serial primary key, nome text not null, valor numeric not null);
INSERT INTO prova_backup (nome, valor) VALUES
  ('viagem-conhecida-1', 1234.56),
  ('viagem-conhecida-2', 7890.12),
  ('viagem-conhecida-3', 555.55);
"

log "3/6 — executando backup.sh"
DATABASE_URL_SYNC="${PROOF_URL}" GESTORFRETE_BACKUP_DIR="${WORK_DIR}" "${SCRIPT_DIR}/backup.sh"
DUMP_FILE="$(ls -1 "${WORK_DIR}"/gestorfrete_*.dump | tail -1)"

log "4/6 — corrompendo e apagando dados no banco de origem"
psql -d "${PROOF_DB}" -v ON_ERROR_STOP=1 -c "
UPDATE prova_backup SET nome = 'CORROMPIDO', valor = 0 WHERE id = 1;
DELETE FROM prova_backup WHERE id = 2;
"

log "5/6 — executando restore.sh contra o dump"
DATABASE_URL_SYNC="${PROOF_URL}" "${SCRIPT_DIR}/restore.sh" "${DUMP_FILE}"

log "6/6 — validando que os dados ORIGINAIS (não os corrompidos) voltaram"
RESTORED="$(psql -d "${PROOF_DB}_restore_test" -tA -F',' -c "SELECT id, nome, valor FROM prova_backup ORDER BY id;")"
EXPECTED="1,viagem-conhecida-1,1234.56
2,viagem-conhecida-2,7890.12
3,viagem-conhecida-3,555.55"

if [ "${RESTORED}" = "${EXPECTED}" ]; then
  log "PROVA OK — dados originais recuperados integralmente:"
  echo "${RESTORED}" | sed 's/^/  /'
else
  log "PROVA FALHOU — dados restaurados não batem com os originais:"
  echo "--- esperado ---"; echo "${EXPECTED}"
  echo "--- restaurado ---"; echo "${RESTORED}"
  dropdb --if-exists "${PROOF_DB}"
  dropdb --if-exists "${PROOF_DB}_restore_test"
  exit 1
fi

log "limpando bancos descartáveis de prova"
dropdb --if-exists "${PROOF_DB}"
dropdb --if-exists "${PROOF_DB}_restore_test"

log "concluído — BACKUP → RESTORE → VALIDAÇÃO provado de ponta a ponta"
exit 0
