#!/usr/bin/env bash
#
# smoke-test.sh — End-to-end reachability check for the 9 Implement AppSec labs.
#
# Usage:
#   ./scripts/smoke-test.sh [--verbose]
#
# Env:
#   API_BASE      base URL for the app (default: http://localhost:8000)
#
# Exit codes:
#   0 if every check passes; non-zero on first failure. Each check prints
#   [ok] / [fail] so a CI log tails cleanly.
#
# What this exercises:
#   - Read surface: health, products, orders, account, subscriptions,
#     wholesale inventory, sensor status
#   - AI: recommend + chat (canned responses when AI_GATEWAY_ENABLED=false)
#   - GraphQL: basic query
#   - Auth forms: /login and /admin credential POSTs (expect 401 for
#     fake creds — just checks the handlers are wired, not real auth)
#   - Alt-auth JSON: /api/v2/auth and /api/mobile/login
#   - File upload: /api/v1/upload and /contact/submit (EICAR string)
#   - Cookie bundles: /js/cart.js, /js/prefs.js, /js/cookie-consent.js
#   - Debug: /debug/headers
#   - Static scripts the frontend loads
#
set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8000}"
VERBOSE=false
if [[ "${1:-}" == "--verbose" ]]; then VERBOSE=true; fi

log_ok()   { echo "[ok]   $*"; }
log_fail() { echo "[fail] $*" >&2; exit 1; }

# check_status <expected-codes-regex> <method> <path> [curl args...]
check_status() {
  local expect="$1" method="$2" path="$3"; shift 3
  local actual
  actual=$(curl -sS -o /dev/null -w '%{http_code}' -X "$method" "$@" "${API_BASE}${path}") \
    || log_fail "curl error ${method} ${path}"
  if [[ ! "$actual" =~ ^${expect}$ ]]; then
    log_fail "${method} ${path} returned ${actual}, expected ${expect}"
  fi
  log_ok "${method} ${path} -> ${actual}"
}

check_body_contains() {
  local needle="$1" path="$2"
  local body
  body=$(curl -sS "${API_BASE}${path}") || log_fail "curl error GET ${path}"
  if [[ "$body" != *"$needle"* ]]; then
    log_fail "GET ${path} body did not contain '${needle}'"
  fi
  log_ok "GET ${path} body contains '${needle}'"
}

echo "== Smoke test against ${API_BASE} =="

# ── Read surface ───────────────────────────────────────────────────────────
check_status 200 GET /health
check_status 200 GET /api/v1/products
check_status 200 GET /api/v1/products/1
check_status 200 GET /api/v1/orders
check_status 200 GET /api/v1/account
check_status 200 GET /api/v1/subscriptions
check_status 200 GET /api/v1/wholesale/inventory
check_status 200 GET /api/v1/sensors/status

# ── AI ────────────────────────────────────────────────────────────────────
check_status 200 POST /api/v1/ai/recommend \
  -H "Content-Type: application/json" \
  -d '{"prompt":"recommend"}'

check_status '200|502' POST /api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"model":"brew-assistant-v1","messages":[{"role":"user","content":"hello"}]}'

# ── GraphQL ───────────────────────────────────────────────────────────────
check_status 200 POST /graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ products { id name slug } }"}'

# ── Form auth surfaces ────────────────────────────────────────────────────
# Fake creds → 401 (just proves the handlers are wired, not real auth)
check_status 401 POST /login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=smoketest@example.com&password=wrong"

check_status 401 POST /admin \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=smoketest@example.com&password=wrong"

# ── Alt-auth JSON surfaces ────────────────────────────────────────────────
check_status 401 POST /api/v2/auth \
  -H "Content-Type: application/json" \
  -d '{"username":"smoketest@example.com","password":"wrong"}'

check_status 401 POST /api/mobile/login \
  -H "Content-Type: application/json" \
  -d '{"email":"smoketest@example.com","password":"wrong"}'

# ── File upload (EICAR reachability, no mitigation assertion) ─────────────
EICAR_TMP=$(mktemp -t eicar-XXXXXX.txt)
trap 'rm -f "$EICAR_TMP"' EXIT
# shellcheck disable=SC2016
printf 'X5O!P%%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*\n' > "$EICAR_TMP"

check_status 200 POST /api/v1/upload \
  -F "file=@${EICAR_TMP}"

# ── Debug ─────────────────────────────────────────────────────────────────
check_status 200 GET /debug/headers -H "Cf-Client-Cert-Subject-DN: CN=smoke, O=Lab"
check_body_contains "cf-client-cert-subject-dn" /debug/headers

# ── Cookie bundles ────────────────────────────────────────────────────────
check_body_contains "so_cart=" /js/cart.js
check_body_contains "so_prefs=" /js/prefs.js
check_body_contains "so_consent=accepted" /js/cookie-consent.js
check_body_contains "_so_analytics=" /js/so-analytics.js
check_body_contains "_so_social=" /js/social-pixel.js

# ── checkout-sdk variants ─────────────────────────────────────────────────
check_body_contains "payments.singleorigin.example" /js/checkout-sdk.js
# Compromised variant must include the configured exfil host
check_body_contains "exfil" "/js/checkout-sdk.js?v=1.2.4"

echo
echo "Smoke test passed."
