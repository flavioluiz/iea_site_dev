#!/usr/bin/env bash
set -euo pipefail

HUGO_VERSION="0.152.2"
HUGO_ARCHIVE="hugo_extended_${HUGO_VERSION}_linux-amd64.tar.gz"
HUGO_SHA256="416bcfbdf5f68469ec9644dbe507da50fc21b94b69a125b059d64ed2cb4d8c27"
INSTALL_DIR="${RUNNER_TEMP:?RUNNER_TEMP is required}/iea-hugo/bin"
ARCHIVE_PATH="${RUNNER_TEMP}/hugo.tar.gz"

mkdir -p "${INSTALL_DIR}"
curl --fail --location --silent --show-error \
  "https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/${HUGO_ARCHIVE}" \
  --output "${ARCHIVE_PATH}"
printf '%s  %s\n' "${HUGO_SHA256}" "${ARCHIVE_PATH}" | sha256sum --check --strict
tar --extract --gzip --file "${ARCHIVE_PATH}" --directory "${INSTALL_DIR}" hugo
printf '%s\n' "${INSTALL_DIR}" >> "${GITHUB_PATH:?GITHUB_PATH is required}"
