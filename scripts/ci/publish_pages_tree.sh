#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="${1:?source directory is required}"
DESTINATION_SUBDIR="${2:?destination subdirectory is required}"
COMMIT_MESSAGE="${3:?commit message is required}"
TARGET_REPOSITORY="${PAGES_TARGET_REPOSITORY:-flavioluiz/iea_site}"
DEPLOY_KEY="${PAGES_DEPLOY_KEY:-}"
TOKEN="${PAGES_DEPLOY_TOKEN:-}"

if [[ -z "${DEPLOY_KEY}" && -z "${TOKEN}" ]]; then
  printf 'PAGES_DEPLOY_KEY or PAGES_DEPLOY_TOKEN is required.\n' >&2
  exit 1
fi

if [[ ! -d "${SOURCE_DIR}" ]]; then
  printf 'Source directory does not exist: %s\n' "${SOURCE_DIR}" >&2
  exit 1
fi
if find "${SOURCE_DIR}" -type l -print -quit | grep -q .; then
  printf 'Refusing to publish an artifact containing symbolic links.\n' >&2
  exit 1
fi
if [[ "${DESTINATION_SUBDIR}" != "." ]]; then
  printf 'Only the production root may be published by this helper.\n' >&2
  exit 1
fi

WORK_DIR="$(mktemp -d)"
TARGET_DIR="${WORK_DIR}/site"
cleanup() {
  rm -rf -- "${WORK_DIR}"
}
trap cleanup EXIT

if [[ -n "${DEPLOY_KEY}" ]]; then
  KEY_FILE="${WORK_DIR}/deploy-key"
  KNOWN_HOSTS_FILE="${WORK_DIR}/known_hosts"
  umask 077
  printf '%s\n' "${DEPLOY_KEY}" > "${KEY_FILE}"
  printf '%s\n' \
    'github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl' \
    > "${KNOWN_HOSTS_FILE}"
  export GIT_SSH_COMMAND="ssh -i ${KEY_FILE} -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=${KNOWN_HOSTS_FILE}"
  REMOTE_URL="git@github.com:${TARGET_REPOSITORY}.git"
  git clone --depth 1 "${REMOTE_URL}" "${TARGET_DIR}"
else
  AUTH_VALUE="$(printf 'x-access-token:%s' "${TOKEN}" | base64 --wrap=0)"
  printf '::add-mask::%s\n' "${AUTH_VALUE}"
  REMOTE_URL="https://github.com/${TARGET_REPOSITORY}.git"
  git -c "http.extraheader=AUTHORIZATION: basic ${AUTH_VALUE}" clone --depth 1 "${REMOTE_URL}" "${TARGET_DIR}"
fi

rsync --archive --delete \
  --exclude '.git/' \
  --exclude 'CNAME' \
  "${SOURCE_DIR}/" "${TARGET_DIR}/"

git -C "${TARGET_DIR}" config user.name "iea-site-bot"
git -C "${TARGET_DIR}" config user.email "iea-site-bot@users.noreply.github.com"
git -C "${TARGET_DIR}" add --all
if git -C "${TARGET_DIR}" diff --cached --quiet; then
  printf 'No Pages changes to publish.\n'
  exit 0
fi
git -C "${TARGET_DIR}" commit -m "${COMMIT_MESSAGE}"
if [[ -n "${DEPLOY_KEY}" ]]; then
  git -C "${TARGET_DIR}" push origin HEAD:main
else
  git -C "${TARGET_DIR}" -c "http.extraheader=AUTHORIZATION: basic ${AUTH_VALUE}" push origin HEAD:main
fi
