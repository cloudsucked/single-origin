#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8000}"

echo "== Smoke test against ${API_BASE} =="

curl -fsS "${API_BASE}/health" >/dev/null
curl -fsS "${API_BASE}/api/v1/products" >/dev/null
curl -fsS "${API_BASE}/api/v1/products/1" >/dev/null
curl -fsS "${API_BASE}/api/v1/orders" >/dev/null
curl -fsS "${API_BASE}/api/v1/account" >/dev/null
curl -fsS "${API_BASE}/api/v1/subscriptions" >/dev/null
curl -fsS "${API_BASE}/api/v1/wholesale/inventory" >/dev/null
curl -fsS "${API_BASE}/api/v1/sensors/status" >/dev/null

curl -fsS -X POST "${API_BASE}/api/v1/ai/recommend" \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"recommend"}' >/dev/null

curl -fsS -X POST "${API_BASE}/graphql" \
  -H 'Content-Type: application/json' \
  -d '{"query":"{ products { id name slug } }"}' >/dev/null

echo "Smoke test passed."
