#!/usr/bin/env bash
#
# prune-db.sh - Soft-reset the Single Origin SQLite database.
#
# Usage:
#   ./scripts/prune-db.sh [--quiet] [--vacuum]
#
# Purpose:
#   The lab traffic generators continuously create orders, contacts, audit logs,
#   and new user registrations. Over time this bloats single_origin.db until
#   the origin process crashes or the VM disk fills. This script trims the
#   four unbounded tables back to their seeded baseline while keeping the
#   backend running.
#
# What it preserves (seeded baseline):
#   - users: id 1-53 (demo, wholesale, admin, 50 test users)
#   - products: id 1-14 (seed catalog)
#   - orders: id 1 (seed order)
#   - subscriptions: id 1 (seed subscription)
#
# What it removes:
#   - orders where id > 1
#   - contacts (all; none are seeded)
#   - audit_logs (all; none are seeded)
#   - subscriptions where id > 1
#   - users where id > 53 (traffic-generated registrations)
#
# Flags:
#   --quiet    Suppress per-step [ok] lines; still print errors and summary.
#   --vacuum   Run VACUUM after deletes to reclaim disk space. This needs a
#              brief exclusive lock on the DB file; if the backend is under
#              heavy load the vacuum may be skipped with a warning.
#
# Exit codes:
#   0 on success, non-zero on any step failure.
#
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"

QUIET=false
VACUUM=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --quiet)  QUIET=true; shift ;;
    --vacuum) VACUUM=true; shift ;;
    -h|--help)
      sed -n '2,28p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      echo "Error: unknown flag '$1'" >&2
      exit 2
      ;;
  esac
done

ok()   { if ! $QUIET; then echo "[ok]   $*"; fi; }
warn() { echo "[warn] $*" >&2; }
fail() { echo "[fail] $*" >&2; exit 1; }

cd "$BACKEND_DIR"

[[ -f single_origin.db ]] || fail "single_origin.db not found in $BACKEND_DIR"

# ---------------------------------------------------------------------------
# Prune (Python does the heavy lifting so we don't parse structured data in bash)
# ---------------------------------------------------------------------------
SUMMARY=$(python3 - "$VACUUM" <<'PY'
import sqlite3
import sys

db = "single_origin.db"
conn = sqlite3.connect(db)
conn.execute("PRAGMA foreign_keys = OFF")
cur = conn.cursor()

# When run via heredoc sys.argv[1] is the bash $VACUUM string ("true"/"false")
should_vacuum = sys.argv[1].lower() == "true" if len(sys.argv) > 1 else False

def count(table: str) -> int:
    try:
        return cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    except sqlite3.OperationalError:
        return -1

before = {
    "orders": count("orders"),
    "contacts": count("contacts"),
    "audit_logs": count("audit_logs"),
    "subscriptions": count("subscriptions"),
    "users": count("users"),
}

# Seed baseline IDs:
#   users 1-53   = demo, wholesale, admin, 50 test users
#   orders 1     = seed order
#   subscriptions 1 = seed subscription
#   contacts, audit_logs = none seeded

deletes = [
    ("orders", "DELETE FROM orders WHERE id > 1"),
    ("contacts", "DELETE FROM contacts"),
    ("audit_logs", "DELETE FROM audit_logs"),
    ("subscriptions", "DELETE FROM subscriptions WHERE id > 1"),
    ("users", "DELETE FROM users WHERE id > 53"),
]

for name, sql in deletes:
    try:
        cur.execute(sql)
    except sqlite3.OperationalError as e:
        print(f"error={name}:{e}", file=sys.stderr)
        sys.exit(1)

# Keep generated IDs predictable after each prune.
try:
    cur.execute("DELETE FROM sqlite_sequence WHERE name IN ('contacts', 'audit_logs')")
    cur.execute("UPDATE sqlite_sequence SET seq = 1 WHERE name = 'orders'")
    cur.execute("UPDATE sqlite_sequence SET seq = 1 WHERE name = 'subscriptions'")
    cur.execute("UPDATE sqlite_sequence SET seq = 53 WHERE name = 'users'")
except sqlite3.OperationalError:
    pass

conn.commit()

after = {
    "orders": count("orders"),
    "contacts": count("contacts"),
    "audit_logs": count("audit_logs"),
    "subscriptions": count("subscriptions"),
    "users": count("users"),
}

# Reclaim disk space if requested
vacuum_ok = False
if should_vacuum:
    try:
        cur.execute("VACUUM")
        vacuum_ok = True
    except sqlite3.OperationalError as e:
        print(f"vacuum_error={e}", file=sys.stderr)

# Emit a machine-readable summary
parts = []
for key in ("orders", "contacts", "audit_logs", "subscriptions", "users"):
    b = before[key]
    a = after[key]
    removed = b - a if b >= 0 and a >= 0 else -1
    parts.append(f"{key}_removed={removed}")
parts.append(f"vacuum={'ok' if vacuum_ok else 'skipped'}")
print(" ".join(parts))

conn.close()
PY
)

[[ $? -eq 0 ]] || fail "prune python block failed"

ok "database pruned"
echo "Prune complete. $SUMMARY"
