#!/usr/bin/env bash
set -euo pipefail

BACKEND_URL="${BACKEND_URL:-https://suna-backend-3teh.onrender.com/v1}"
FRONTEND_URL="${FRONTEND_URL:-https://mira-frontend-d85v.onrender.com}"

failures=0

check_json_endpoint() {
  local name="$1"
  local url="$2"

  printf 'Checking %s... ' "$name"
  if curl -fsS "$url" >/tmp/mira-smoke-response.json; then
    printf 'PASS\n'
  else
    printf 'FAIL\n'
    failures=$((failures + 1))
  fi
}

check_status() {
  local name="$1"
  local url="$2"
  local expected="$3"
  local actual

  printf 'Checking %s... ' "$name"
  actual="$(curl -sS -o /dev/null -w '%{http_code}' "$url" || true)"
  if [ "$actual" = "$expected" ]; then
    printf 'PASS (%s)\n' "$actual"
  else
    printf 'FAIL (expected %s, got %s)\n' "$expected" "$actual"
    failures=$((failures + 1))
  fi
}

check_json_endpoint "backend health" "$BACKEND_URL/health"
check_json_endpoint "redis health" "$BACKEND_URL/debug/redis"
check_json_endpoint "runtime config" "$BACKEND_URL/debug/config"
check_json_endpoint "canvas/media health" "$BACKEND_URL/canvas-ai/health"
check_json_endpoint "composio health" "$BACKEND_URL/composio/health"
check_status "unauthenticated threads blocked" "$BACKEND_URL/threads" "401"
check_status "frontend availability" "$FRONTEND_URL" "200"

if [ "$failures" -gt 0 ]; then
  printf '\nSmoke check failed with %s failure(s).\n' "$failures"
  exit 1
fi

printf '\nSmoke check passed.\n'
