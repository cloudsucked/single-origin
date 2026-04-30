from __future__ import annotations

import os
from secrets import token_urlsafe


os.environ.setdefault("SEED_DEMO_EMAIL", "demo@singleorigin.example")
os.environ.setdefault("SEED_WHOLESALE_EMAIL", "wholesale@cafepartner.example")
os.environ.setdefault("SEED_ADMIN_EMAIL", "admin@singleorigin.example")
# Demo seed password is pinned (not randomised) so tests can perform real
# /auth/login round-trips against the seeded credentials. The other roles
# stay randomised because no test logs into them.
os.environ.setdefault("SEED_DEMO_PASSWORD", "demo-password")
os.environ.setdefault("SEED_WHOLESALE_PASSWORD", token_urlsafe(20))
os.environ.setdefault("SEED_ADMIN_PASSWORD", token_urlsafe(20))
os.environ.setdefault("SEED_TEST_USERS_PASSWORD", token_urlsafe(20))
