#!/usr/bin/env bash
#
# Ensure the master node hostname entry exists in /etc/hosts.
# Usage (requires sudo privileges):
#   sudo ./apply_master_alias.sh
#
# Set MASTER_IP to override detection (defaults to first non-loopback IPv4).

set -euo pipefail

MASTER_HOST="${MASTER_HOST:-master-node}"
MASTER_ALIAS="${MASTER_ALIAS:-octavius}"
MASTER_IP="${MASTER_IP:-}"
HOSTS_FILE="/etc/hosts"

if [[ -z "$MASTER_IP" ]]; then
    MASTER_IP=$(ip -4 addr show scope global | awk '/inet / {sub(/\/.*/, "", $2); print $2; exit}')
fi

if [[ -z "$MASTER_IP" ]]; then
    echo "ERROR: Could not auto-detect master IPv4 address. Set MASTER_IP explicitly." >&2
    exit 1
fi

echo "Ensuring ${MASTER_IP} ${MASTER_HOST} ${MASTER_ALIAS} present in ${HOSTS_FILE}"

tmp_file="$(mktemp)"
trap 'rm -f "$tmp_file"' EXIT

if [[ -f "$HOSTS_FILE" ]]; then
    cp "$HOSTS_FILE" "$tmp_file"
fi

grep -vE "\\b(${MASTER_HOST}|${MASTER_ALIAS})\\b" "$tmp_file" > "${tmp_file}.clean" || true
mv "${tmp_file}.clean" "$tmp_file"

printf "%s %s %s\n" "$MASTER_IP" "$MASTER_HOST" "$MASTER_ALIAS" >> "$tmp_file"

cp "$tmp_file" "$HOSTS_FILE"
echo "Updated ${HOSTS_FILE}:"
grep "$MASTER_IP" "$HOSTS_FILE"

