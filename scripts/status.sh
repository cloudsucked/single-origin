#!/usr/bin/env bash
set -euo pipefail

echo "== Backend (uvicorn) =="
pgrep -fa "uvicorn app.main:app" || echo "not running"

echo ""
echo "== Frontend (vite) =="
pgrep -fa "vite dev" || echo "not running"
