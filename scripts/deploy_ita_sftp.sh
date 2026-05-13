#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${PROJECT_DIR}/.deploy_ita"
ITA_CONFIG="${PROJECT_DIR}/config/production/config-ita-domain.yaml"
DEPLOY_ENV_FILE="${PROJECT_DIR}/config/production/deploy_ita_sftp.env"

SFTP_HOST="${SFTP_HOST:-dominios02.ita.br}"
SFTP_PORT="${SFTP_PORT:-2222}"
SFTP_USER="${SFTP_USER:-wmpgeam}"
SFTP_REMOTE_DIR="${SFTP_REMOTE_DIR:-.}"
SITE_URL="${SITE_URL:-https://www.pgeam.ita.br}"
DEFAULT_LANG_PATH="${DEFAULT_LANG_PATH:-pt}"

DELETE_REMOTE=true
BUILD_ONLY=false
AUTO_DETECT_REMOTE=true
SKIP_CONFIRM=false
USER_SET_REMOTE_DIR=false
CHANGED_ONLY=false
PROTECTION_ENABLED=true
PROTECTION_NOINDEX=true
PROTECTION_USER="preview"
PROTECTION_AUTH_REALM="PG-EAM em revisao interna"
PROTECTION_AUTH_USER_FILE=".htpasswd"

if [[ -f "${DEPLOY_ENV_FILE}" ]]; then
  # shellcheck disable=SC1090
  source "${DEPLOY_ENV_FILE}"
fi

usage() {
  cat <<EOF
Uso: $(basename "$0") [opcoes]

Opcoes:
  --remote-dir DIR   Diretorio remoto (default: .)
  --no-delete        Nao remove arquivos remotos ausentes localmente
  --no-auto-detect   Nao tenta autodetectar diretorio remoto
  --changed-only     Envia apenas arquivos alterados (comparacao por hash)
  --no-protection    Nao gera protecao por senha/noindex
  --yes              Nao pede confirmacao antes do upload
  --build-only       Apenas build local, sem upload SFTP
  -h, --help         Exibe ajuda

Variaveis de ambiente suportadas:
  SFTP_HOST, SFTP_PORT, SFTP_USER, SFTP_REMOTE_DIR, SITE_URL, SFTP_PASSWORD
  DEFAULT_LANG_PATH, PROTECTION_ENABLED, PROTECTION_NOINDEX, PROTECTION_USER
  PROTECTION_AUTH_REALM, PROTECTION_AUTH_USER_FILE

Exemplos:
  $(basename "$0")
  $(basename "$0") --remote-dir public_html
  SFTP_PASSWORD='***' $(basename "$0") --remote-dir public_html
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --remote-dir)
      if [[ $# -lt 2 ]]; then
        echo "Erro: --remote-dir exige um valor." >&2
        exit 1
      fi
      SFTP_REMOTE_DIR="$2"
      USER_SET_REMOTE_DIR=true
      shift 2
      ;;
    --no-delete)
      DELETE_REMOTE=false
      shift
      ;;
    --no-auto-detect)
      AUTO_DETECT_REMOTE=false
      shift
      ;;
    --changed-only)
      CHANGED_ONLY=true
      shift
      ;;
    --no-protection)
      PROTECTION_ENABLED=false
      shift
      ;;
    --yes)
      SKIP_CONFIRM=true
      shift
      ;;
    --build-only)
      BUILD_ONLY=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Erro: opcao desconhecida: $1" >&2
      usage
      exit 1
      ;;
  esac
done

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Erro: comando obrigatorio nao encontrado: $1" >&2
    exit 1
  fi
}

require_cmd hugo

if [[ ! -f "$ITA_CONFIG" ]]; then
  echo "Erro: configuracao ITA nao encontrada: $ITA_CONFIG" >&2
  exit 1
fi

echo "==> Build Hugo para ambiente ITA"
echo "    baseURL: ${SITE_URL}"
rm -rf "$BUILD_DIR"
hugo \
  --gc \
  --minify \
  --buildFuture \
  --environment production \
  --baseURL "${SITE_URL}" \
  --config "${PROJECT_DIR}/config/_default/config.yaml,${ITA_CONFIG}" \
  --destination "$BUILD_DIR"

# Remove arquivos de metadados locais indesejados no deploy.
find "$BUILD_DIR" -name ".DS_Store" -type f -delete

# Em dominio proprio, a raiz "/" precisa ter index.html para evitar 404.
if [[ ! -f "${BUILD_DIR}/index.html" ]]; then
  cat > "${BUILD_DIR}/index.html" <<EOF
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="0; url=/${DEFAULT_LANG_PATH}/">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Redirecionando...</title>
  <link rel="canonical" href="${SITE_URL%/}/${DEFAULT_LANG_PATH}/">
</head>
<body>
  <p>Redirecionando para <a href="/${DEFAULT_LANG_PATH}/">/${DEFAULT_LANG_PATH}/</a>...</p>
</body>
</html>
EOF
fi

if command -v rg >/dev/null 2>&1; then
  FOUND_OLD_DOMAIN=0
  if rg -n --max-count 1 "flavioluiz.github.io/pgeam" "$BUILD_DIR" >/dev/null 2>&1; then
    FOUND_OLD_DOMAIN=1
  fi
else
  FOUND_OLD_DOMAIN=0
  if grep -R -n -m 1 "flavioluiz.github.io/pgeam" "$BUILD_DIR" >/dev/null 2>&1; then
    FOUND_OLD_DOMAIN=1
  fi
fi

if [[ "$FOUND_OLD_DOMAIN" -eq 1 ]]; then
  echo "Erro: build contem referencias ao dominio antigo (GitHub Pages)." >&2
  echo "Revise o conteudo e a configuracao antes do deploy." >&2
  exit 1
fi

echo "==> Build concluido em: $BUILD_DIR"

if [[ "$BUILD_ONLY" == true ]]; then
  echo "==> Modo --build-only: upload SFTP ignorado."
  exit 0
fi

require_cmd lftp

if [[ -z "${SFTP_PASSWORD:-}" ]]; then
  read -r -s -p "Senha SFTP para ${SFTP_USER}@${SFTP_HOST}:${SFTP_PORT}: " SFTP_PASSWORD
  echo
fi

if [[ -z "${SFTP_PASSWORD}" ]]; then
  echo "Erro: senha SFTP vazia." >&2
  exit 1
fi

lftp_run() {
  local cmd="$1"
  lftp \
    -p "${SFTP_PORT}" \
    "sftp://${SFTP_HOST}" \
    -e "set cmd:fail-exit true; set sftp:auto-confirm yes; set net:max-retries 2; set net:reconnect-interval-base 3; set net:timeout 20; user \"${SFTP_USER}\" \"${SFTP_PASSWORD}\"; ${cmd}; bye"
}

lftp_run_file() {
  local cmd_file="$1"
  lftp \
    -p "${SFTP_PORT}" \
    "sftp://${SFTP_HOST}" \
    -e "set cmd:fail-exit true; set sftp:auto-confirm yes; set net:max-retries 2; set net:reconnect-interval-base 3; set net:timeout 20; user \"${SFTP_USER}\" \"${SFTP_PASSWORD}\"; source \"${cmd_file}\"; bye"
}

remote_pwd() {
  local dir="$1"
  local out raw path_part

  out="$(lftp_run "cd \"${dir}\"; pwd" 2>/dev/null || true)"
  raw="$(printf "%s\n" "${out}" | tr -d '\r' | awk 'NF { last=$0 } END { print last }')"
  raw="${raw#* is }"
  raw="${raw#\"}"
  raw="${raw%\"}"

  if [[ "${raw}" == *"://"* ]]; then
    path_part="$(printf "%s" "${raw}" | sed -E 's#^[a-zA-Z]+://[^/]+##')"
    if [[ -z "${path_part}" ]]; then
      path_part="/"
    fi
    raw="${path_part}"
  fi

  printf "%s" "${raw}"
}

remote_test() {
  local cmd="$1"
  if lftp_run "$cmd" >/dev/null 2>&1; then
    return 0
  fi
  return 1
}

if ! remote_test "pwd"; then
  echo "Erro: falha ao autenticar/conectar via SFTP em ${SFTP_HOST}:${SFTP_PORT}." >&2
  echo "Verifique usuario/senha (senhas com caracteres especiais agora sao suportadas)." >&2
  exit 1
fi

build_manifest() {
  local output_file="$1"
  echo "    Calculando hashes de ${BUILD_DIR}..." >&2
  (
    cd "${BUILD_DIR}"
    set +o pipefail
    find . -type f -print0 | sort -z | xargs -0 shasum -a 256 2>/dev/null \
      | awk '{hash=substr($0,1,64); file=substr($0,67); sub(/^\.\//,"",file); print file "|" hash}'
  ) > "${output_file}"
  local count
  count="$(wc -l < "${output_file}" | tr -d ' ')"
  echo "    ${count} arquivos no manifesto" >&2
}

compute_diff_lists() {
  local old_manifest="$1"
  local new_manifest="$2"
  local changed_list="$3"
  local deleted_list="$4"

  : > "${changed_list}"
  : > "${deleted_list}"

  if [[ ! -f "${old_manifest}" ]]; then
    cut -d'|' -f1 "${new_manifest}" > "${changed_list}"
    return
  fi

  awk -F'|' \
    -v changed_out="${changed_list}" \
    -v deleted_out="${deleted_list}" \
    '
    NR==FNR { old[$1]=$2; next }
    {
      seen[$1]=1
      if (!(($1 in old) && old[$1] == $2)) {
        print $1 >> changed_out
      }
    }
    END {
      for (path in old) {
        if (!(path in seen)) {
          print path >> deleted_out
        }
      }
    }
    ' "${old_manifest}" "${new_manifest}"
}

detect_remote_dir() {
  local candidates=("$@")

  echo "==> Autodeteccao de diretorio remoto (sem upload)" >&2
  for candidate in "${candidates[@]}"; do
    echo "    testando: ${candidate}" >&2
    if remote_test "cd \"${candidate}\""; then
      echo "    acessivel: ${candidate}" >&2
      echo "$candidate"
      return 0
    fi
    echo "    indisponivel: ${candidate}" >&2
  done

  return 1
}

if [[ "$AUTO_DETECT_REMOTE" == true ]]; then
  if [[ "$USER_SET_REMOTE_DIR" == true ]]; then
    CANDIDATES=("$SFTP_REMOTE_DIR")
  else
    # Em hospedagens de dominio, "." costuma ser o document root.
    # Testamos "." primeiro e so tentamos subpastas conhecidas se falhar.
    CANDIDATES=("." "public_html" "web" "www" "htdocs")
  fi

  if DETECTED_DIR="$(detect_remote_dir "${CANDIDATES[@]}")"; then
    SFTP_REMOTE_DIR="$DETECTED_DIR"
  fi
fi

if ! remote_test "cd \"${SFTP_REMOTE_DIR}\""; then
  echo "Erro: diretorio remoto nao acessivel: ${SFTP_REMOTE_DIR}" >&2
  echo "Use --remote-dir para informar o caminho correto." >&2
  exit 1
fi

echo "==> Diretorio remoto selecionado: ${SFTP_REMOTE_DIR}"
if [[ "$SKIP_CONFIRM" == false ]]; then
  read -r -p "Confirmar upload para ${SFTP_USER}@${SFTP_HOST}:${SFTP_PORT}/${SFTP_REMOTE_DIR}? Digite SIM para continuar: " CONFIRM
  if [[ "$CONFIRM" != "SIM" ]]; then
    echo "Upload cancelado pelo usuario."
    exit 0
  fi
fi

if [[ "${PROTECTION_ENABLED}" == "true" ]]; then
  if ! command -v openssl >/dev/null 2>&1; then
    echo "Erro: 'openssl' nao encontrado. Necessario para gerar senha de acesso HTTP." >&2
    exit 1
  fi

  echo "==> Protecao ativa: senha + noindex"
  if [[ -z "${PROTECTION_HTTP_PASSWORD:-}" ]]; then
    read -r -s -p "Senha para acesso HTTP (Basic Auth) [usuario: ${PROTECTION_USER}]: " PROTECTION_HTTP_PASSWORD
    echo
  fi

  if [[ -z "${PROTECTION_HTTP_PASSWORD}" ]]; then
    echo "Erro: senha HTTP vazia." >&2
    exit 1
  fi

  PASSWORD_HASH="$(openssl passwd -apr1 "${PROTECTION_HTTP_PASSWORD}")"

  AUTH_USER_FILE_RESOLVED="${PROTECTION_AUTH_USER_FILE}"
  if [[ "${AUTH_USER_FILE_RESOLVED}" != /* ]]; then
    REMOTE_ABS_DIR="$(remote_pwd "${SFTP_REMOTE_DIR}")"
    if [[ "${REMOTE_ABS_DIR}" == /* && "${REMOTE_ABS_DIR}" != "." && "${REMOTE_ABS_DIR}" != "./" ]]; then
      AUTH_USER_FILE_RESOLVED="${REMOTE_ABS_DIR}/${PROTECTION_AUTH_USER_FILE}"
      AUTH_USER_FILE_RESOLVED="$(printf "%s" "${AUTH_USER_FILE_RESOLVED}" | sed 's://*:/:g')"
    fi
  fi

  if [[ "${AUTH_USER_FILE_RESOLVED}" != /* ]]; then
    FALLBACK_AUTH_USER_FILE="/home/${SFTP_USER}/$(basename "${PROTECTION_AUTH_USER_FILE}")"
    if [[ "${SKIP_CONFIRM}" == "false" ]]; then
      echo "Aviso: nao foi possivel detectar automaticamente o caminho absoluto para AuthUserFile."
      read -r -p "Informe caminho absoluto de .htpasswd [${FALLBACK_AUTH_USER_FILE}]: " INPUT_AUTH_USER_FILE
      AUTH_USER_FILE_RESOLVED="${INPUT_AUTH_USER_FILE:-${FALLBACK_AUTH_USER_FILE}}"
    else
      AUTH_USER_FILE_RESOLVED="${FALLBACK_AUTH_USER_FILE}"
      echo "Aviso: usando fallback para AuthUserFile: ${AUTH_USER_FILE_RESOLVED}"
    fi
  fi

  if [[ "${AUTH_USER_FILE_RESOLVED}" != /* ]]; then
    echo "Erro: AuthUserFile precisa ser absoluto. Recebido: ${AUTH_USER_FILE_RESOLVED}" >&2
    exit 1
  fi

  echo "    AuthUserFile: ${AUTH_USER_FILE_RESOLVED}"

  SAFE_REALM="${PROTECTION_AUTH_REALM//\"/}"
  cat > "${BUILD_DIR}/.htaccess" <<EOF
# Gerado automaticamente por deploy_ita_sftp.sh
AuthType Basic
AuthName "${SAFE_REALM}"
AuthUserFile ${AUTH_USER_FILE_RESOLVED}
Require valid-user

<Files ".htpasswd">
  Require all denied
</Files>
EOF

  cat > "${BUILD_DIR}/.htpasswd" <<EOF
${PROTECTION_USER}:${PASSWORD_HASH}
EOF

  if [[ "${PROTECTION_NOINDEX}" == "true" ]]; then
    cat > "${BUILD_DIR}/robots.txt" <<EOF
User-agent: *
Disallow: /
EOF
  fi
else
  rm -f "${BUILD_DIR}/.htaccess" "${BUILD_DIR}/.htpasswd"
fi

MIRROR_FLAGS=(--reverse --verbose --parallel=4)
if [[ "$DELETE_REMOTE" == true ]]; then
  MIRROR_FLAGS+=(--delete)
fi

echo "==> Iniciando upload SFTP"
echo "    host: ${SFTP_HOST}:${SFTP_PORT}"
echo "    usuario: ${SFTP_USER}"
echo "    diretorio remoto: ${SFTP_REMOTE_DIR}"
if [[ "${CHANGED_ONLY}" == "true" ]]; then
  echo "    modo: changed-only (arquivos alterados)"
else
  echo "    modo: mirror completo"
fi

if [[ "${CHANGED_ONLY}" == "true" ]]; then
  MANIFEST_FILE="${PROJECT_DIR}/.deploy_ita_manifest.sha256"
  NEW_MANIFEST="$(mktemp)"
  CHANGED_LIST="$(mktemp)"
  DELETED_LIST="$(mktemp)"
  LFTP_CMD_FILE="$(mktemp)"
  trap 'rm -f "${NEW_MANIFEST}" "${CHANGED_LIST}" "${DELETED_LIST}" "${LFTP_CMD_FILE}"' EXIT

  build_manifest "${NEW_MANIFEST}"
  compute_diff_lists "${MANIFEST_FILE}" "${NEW_MANIFEST}" "${CHANGED_LIST}" "${DELETED_LIST}"

  if [[ "${DELETE_REMOTE}" != "true" ]]; then
    : > "${DELETED_LIST}"
  fi

  CHANGED_COUNT="$(wc -l < "${CHANGED_LIST}" | tr -d ' ')"
  DELETED_COUNT="$(wc -l < "${DELETED_LIST}" | tr -d ' ')"

  if [[ "${CHANGED_COUNT}" == "0" && "${DELETED_COUNT}" == "0" ]]; then
    echo "==> Nenhum arquivo alterado para envio."
    cp "${NEW_MANIFEST}" "${MANIFEST_FILE}"
  else
    {
      echo "set cmd:fail-exit true"
      echo "set sftp:auto-confirm yes"
      echo "set net:max-retries 1"
      echo "set net:reconnect-interval-base 3"
      echo "set net:timeout 12"
      echo "cd \"${SFTP_REMOTE_DIR}\""
      echo "lcd \"${BUILD_DIR}\""

      if [[ "${CHANGED_COUNT}" != "0" ]]; then
        awk -F'/' '
          {
            if (NF <= 1) {
              print "."
            } else {
              dir = $1
              for (i = 2; i < NF; i++) dir = dir "/" $i
              print dir
            }
          }
        ' "${CHANGED_LIST}" | sort -u | grep -v '^\.$' | while IFS= read -r dir; do
          echo "set cmd:fail-exit false; mkdir -p \"${dir}\"; set cmd:fail-exit true"
        done

        while IFS= read -r file; do
          file_dir="$(dirname "${file}")"
          echo "put -O \"${file_dir}\" \"${file}\""
        done < "${CHANGED_LIST}"
      fi

      if [[ "${DELETED_COUNT}" != "0" ]]; then
        while IFS= read -r file; do
          echo "rm -f \"${file}\""
        done < "${DELETED_LIST}"
      fi

      echo "bye"
    } > "${LFTP_CMD_FILE}"

    echo "==> Changed-only: ${CHANGED_COUNT} upload(s), ${DELETED_COUNT} remocao(oes)"
    lftp_run_file "${LFTP_CMD_FILE}"
    echo "==> Atualizando manifesto local"
    cp "${NEW_MANIFEST}" "${MANIFEST_FILE}"
  fi
else
  lftp_run "cd \"${SFTP_REMOTE_DIR}\"; lcd \"${BUILD_DIR}\"; mirror ${MIRROR_FLAGS[*]} . ."
  echo "==> Salvando manifesto para futuros deploys changed-only"
  MANIFEST_FILE="${PROJECT_DIR}/.deploy_ita_manifest.sha256"
  NEW_MANIFEST="$(mktemp)"
  build_manifest "${NEW_MANIFEST}"
  cp "${NEW_MANIFEST}" "${MANIFEST_FILE}"
  rm -f "${NEW_MANIFEST}"
fi

echo "==> Deploy concluido"
echo "    URL: ${SITE_URL}"
echo
echo "Observacao de dominio:"
echo "- O site foi gerado para ${SITE_URL}."
echo "- Se o servidor publicar em subpasta, rode com --remote-dir e ajuste baseURL no arquivo config/production/config-ita-domain.yaml."
