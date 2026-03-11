#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"

cd "$FRONTEND_DIR"

if [[ -f .env.example && ! -f .env ]]; then
  cp .env.example .env
fi

npm install
exec npm run dev -- --host 0.0.0.0 --port 5173
