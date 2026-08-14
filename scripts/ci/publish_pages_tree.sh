#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="${1:?source directory is required}"
DESTINATION_SUBDIR="${2:?destination subdirectory is required}"
COMMIT_MESSAGE="${3:?commit message is required}"
TARGET_REPOSITORY="${PAGES_TARGET_REPOSITORY:-flavioluiz/iea_site}"
TOKEN="${PAGES_DEPLOY_TOKEN:?PAGES_DEPLOY_TOKEN is required}"

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

AUTH_VALUE="$(printf 'x-access-token:%s' "${TOKEN}" | base64 --wrap=0)"
printf '::add-mask::%s\n' "${AUTH_VALUE}"
WORK_DIR="$(mktemp -d)"
TARGET_DIR="${WORK_DIR}/site"
REMOTE_URL="https://github.com/${TARGET_REPOSITORY}.git"

git -c "http.extraheader=AUTHORIZATION: basic ${AUTH_VALUE}" clone --depth 1 "${REMOTE_URL}" "${TARGET_DIR}"

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
git -C "${TARGET_DIR}" -c "http.extraheader=AUTHORIZATION: basic ${AUTH_VALUE}" push origin HEAD:main
