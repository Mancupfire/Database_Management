#!/usr/bin/env bash
set -euo pipefail

# Basic UI smoke checks against running frontend (http://localhost:8080)
# Requires curl and the frontend server up (./run.sh or python3 -m http.server 8080)

BASE_URL="${BASE_URL:-http://localhost:8080}"

check() {
  local path="$1"
  local needle="$2"
  echo "Checking ${BASE_URL}${path} ..."
  body=$(curl -fsSL "${BASE_URL}${path}")
  if [[ "${body}" != *"${needle}"* ]]; then
    echo "❌ ${path} missing expected text: ${needle}"
    exit 1
  fi
  echo "✓ ${path}"
}

check "/" "MoneyMinder"
check "/css/style.css" "body"
check "/js/app.js" "MoneyMinder Frontend Application"

echo "UI smoke checks passed."
