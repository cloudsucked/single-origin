#!/usr/bin/env bash
#
# reset-lab.sh — Drop and re-seed the Single Origin lab database.
#
# Usage:
#   ./scripts/reset-lab.sh [--no-restart] [--quiet]
#
# Default behavior:
#   1. Remove the backend SQLite database.
#   2. Ensure the backend venv exists and dependencies are installed.
#   3. Run `python seed_db.py` to repopulate products, users, orders.
#   4. Restart the backend service (docker compose or systemd) so the
#      freshly seeded DB is what FastAPI sees.
#   5. Print a one-line summary of product / user / order counts.
#
# Flags:
#   --no-restart   Skip step 4; use when the backend is run via start-backend.sh
#                  in a dev shell and will pick up the new DB on next request.
#   --quiet        Suppress per-step [ok] lines; still print errors and summary.
#
# Exit codes:
#   0 on success, non-zero on any step failure.
#
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"

NO_RESTART=false
QUIET=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-restart) NO_RESTART=true; shift ;;
    --quiet)      QUIET=true; shift ;;
    -h|--help)
      sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      echo "Error: unknown flag '$1'" >&2
      exit 2
      ;;
  esac
done

ok()   { if ! $QUIET; then echo "[ok]   $*"; fi; }
fail() { echo "[fail] $*" >&2; exit 1; }

cd "$BACKEND_DIR"

# 1. Drop the DB
if [[ -f single_origin.db ]]; then
  rm single_origin.db || fail "could not remove single_origin.db"
  ok "removed previous single_origin.db"
else
  ok "no previous DB to remove"
fi

# 2. Venv + deps
if [[ ! -d .venv ]]; then
  python3 -m venv .venv || fail "could not create venv"
  ok "created .venv"
fi

# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install -q -r requirements.txt \
  || fail "pip install failed"
ok "dependencies up to date"

# 3. Seed
python seed_db.py \
  || fail "seed_db.py failed"
ok "database re-seeded"

# 4. Restart backend (best-effort; detect docker compose first, then systemd)
if ! $NO_RESTART; then
  if command -v docker >/dev/null 2>&1 && [[ -f "$ROOT_DIR/infra/docker-compose.dev.yml" ]]; then
    if (cd "$ROOT_DIR" && docker compose -f infra/docker-compose.dev.yml ps --services 2>/dev/null | grep -q .); then
      (cd "$ROOT_DIR" && docker compose -f infra/docker-compose.dev.yml restart backend 2>/dev/null) \
        && ok "restarted backend via docker compose" \
        || ok "docker compose restart skipped (service not running)"
    else
      ok "docker compose stack not running; skipped restart"
    fi
  elif command -v systemctl >/dev/null 2>&1 && systemctl list-units --type=service 2>/dev/null | grep -q singleorigin; then
    sudo systemctl restart singleorigin \
      && ok "restarted singleorigin systemd unit" \
      || fail "systemctl restart failed"
  else
    ok "no known restart mechanism detected (running in dev shell?); use --no-restart to silence"
  fi
fi

# 5. Row-count summary
SUMMARY=$(python - <<'PY'
import sqlite3
conn = sqlite3.connect("single_origin.db")
try:
    cur = conn.cursor()
    def count(table: str) -> int:
        try:
            return cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        except sqlite3.OperationalError:
            return -1
    products = count("products")
    users = count("users")
    orders = count("orders")
    subscriptions = count("subscriptions")
    print(f"products={products} users={users} orders={orders} subscriptions={subscriptions}")
finally:
    conn.close()
PY
)

if [[ $SUMMARY == *"products=-1"* || $SUMMARY == *"users=-1"* ]]; then
  fail "seed summary reports missing tables: $SUMMARY"
fi

echo "Lab data reset complete. $SUMMARY"
