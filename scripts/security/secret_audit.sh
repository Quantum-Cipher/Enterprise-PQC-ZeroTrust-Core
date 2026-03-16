#!/usr/bin/env bash
set -euo pipefail

echo "Starting Deep Security Scan for Hardcoded Secrets..."

ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT_DIR"

SCAN_REGEX='^[[:space:]]*(export[[:space:]]+)?(PRIVATE_KEY|SECRET|PASSWORD|API_KEY|ACCESS_KEY|TOKEN|MNEMONIC)[[:space:]]*='

MATCHES="$(
  grep -RInE "$SCAN_REGEX" . \
    --exclude=secret_audit.sh \
    --exclude=cleanup_vulnerability_markers.sh \
    --exclude-dir=.git \
    --exclude-dir=node_modules \
    --exclude-dir=dist \
    --exclude-dir=build \
    --exclude-dir=.next \
    --exclude-dir=coverage \
    --exclude-dir=vendor \
    --exclude-dir=.venv \
    --exclude-dir=venv \
    --exclude-dir=__pycache__ \
    --exclude-dir=threat-detector-flow \
    2>/dev/null \
    || true
)"

if [[ -n "$MATCHES" ]]; then
  echo "CRITICAL FAILURE: Sensitive assignment pattern detected:"
  printf '%s\n' "$MATCHES"
  echo "Deployment Blocked: Remove hardcoded secrets before committing or pushing."
  exit 1
fi

echo "Deep Security Scan Passed: No hardcoded secrets detected."
