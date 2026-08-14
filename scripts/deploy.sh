#!/usr/bin/env bash
set -euo pipefail

cat <<'EOF'
O deploy suportado é o workflow "Deploy pilot site" após o CI de main.

Abra:
https://github.com/flavioluiz/iea_site_dev/actions/workflows/deploy.yml

Instruções e configuração do token:
docs/operations/github-pages.md
EOF
