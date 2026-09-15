#!/usr/bin/env bash
set -euo pipefail

INSTALL_ROOT="/opt/okf-wiki"
VAULT_DIR="${INSTALL_ROOT}/okf-wiki-vault"

echo "==> Creating OKF Wiki local structure"

if [[ "$(uname -s)" != "Linux" ]]; then
    echo "ERROR: This installer currently supports Linux only."
    exit 1
fi

sudo mkdir -p \
    "${INSTALL_ROOT}" \
    "${VAULT_DIR}/raw" \
    "${VAULT_DIR}/curated"

if [[ ! -e "${VAULT_DIR}/index.md" ]]; then
    sudo touch "${VAULT_DIR}/index.md"
fi

if [[ ! -e "${VAULT_DIR}/log.md" ]]; then
    sudo touch "${VAULT_DIR}/log.md"
fi

echo
echo "OKF Wiki structure ready:"
echo
echo "${VAULT_DIR}/"
echo "├── index.md"
echo "├── log.md"
echo "├── raw/"
echo "└── curated/"
