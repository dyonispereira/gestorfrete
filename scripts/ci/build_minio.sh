#!/usr/bin/env bash
# CI-only — compila o MinIO Community Edition a partir do source oficial, pinado por tag + commit.
#
# Por quê: a partir de set/2025 a MinIO Inc. passou a exigir login para pull de `minio/minio` tanto
# no Docker Hub quanto no Quay.io (a Community Edition virou source-only para distribuição livre).
# Nenhuma imagem de terceiro é usada aqui — o binário é compilado do zero a cada execução do CI, a
# partir do repositório oficial github.com/minio/minio.
#
# Reprodutibilidade: NUNCA aponta para uma branch flutuante. A tag abaixo é verificada contra o
# commit exato antes de compilar — se a tag um dia for realocada (ataque ou erro humano), o build
# falha em vez de compilar algo inesperado silenciosamente. Atualizar a versão pinada é uma decisão
# deliberada: mudar as duas constantes abaixo juntas, nunca só uma.
set -euo pipefail

MINIO_TAG="RELEASE.2025-10-15T17-29-55Z"
MINIO_COMMIT="9e49d5e7a648f00e26f2246f4dc28e6b07f8c84a"

OUT_BIN="${1:?Uso: build_minio.sh <caminho-de-saida-do-binario>}"

log() { echo "[build_minio.sh] $*"; }

SRC_DIR="$(mktemp -d)"
trap 'rm -rf "${SRC_DIR}"' EXIT

log "clonando minio/minio @ ${MINIO_TAG}"
git clone --quiet --depth 1 --branch "${MINIO_TAG}" https://github.com/minio/minio.git "${SRC_DIR}"

cd "${SRC_DIR}"
ACTUAL_COMMIT="$(git rev-parse HEAD)"
if [ "${ACTUAL_COMMIT}" != "${MINIO_COMMIT}" ]; then
  log "ERRO: a tag ${MINIO_TAG} não aponta para o commit pinado — build abortado."
  log "  esperado: ${MINIO_COMMIT}"
  log "  obtido:   ${ACTUAL_COMMIT}"
  exit 1
fi
log "commit verificado: ${ACTUAL_COMMIT}"

log "compilando (CGO_ENABLED=0, estático, sem checks/build-debugging/ldflags do Makefile — só o"
log "binário do servidor, que é tudo que os testes de conectividade do GestorFrete precisam)"
CGO_ENABLED=0 go build -tags kqueue -trimpath -o "${OUT_BIN}" .

log "MinIO ${MINIO_TAG} (${MINIO_COMMIT}) compilado em ${OUT_BIN}"
