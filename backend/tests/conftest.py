from __future__ import annotations

import os
from secrets import token_urlsafe


os.environ.setdefault("SEED_DEMO_EMAIL", "demo@singleorigin.example")
os.environ.setdefault("SEED_WHOLESALE_EMAIL", "wholesale@cafepartner.example")
os.environ.setdefault("SEED_ADMIN_EMAIL", "admin@singleorigin.example")
os.environ.setdefault("SEED_DEMO_PASSWORD", token_urlsafe(20))
os.environ.setdefault("SEED_WHOLESALE_PASSWORD", token_urlsafe(20))
os.environ.setdefault("SEED_ADMIN_PASSWORD", token_urlsafe(20))
os.environ.setdefault("SEED_TEST_USERS_PASSWORD", token_urlsafe(20))
