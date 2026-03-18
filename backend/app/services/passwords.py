from __future__ import annotations

import base64
import hashlib
import hmac
import os

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 390000
SALT_BYTES = 16


def _b64_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")


def is_password_hash(value: str) -> bool:
    return value.startswith(f"{ALGORITHM}$")


def hash_password(password: str) -> str:
    salt = os.urandom(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"{ALGORITHM}${ITERATIONS}${_b64_encode(salt)}${_b64_encode(digest)}"


def verify_password(password: str, stored_password: str) -> bool:
    if not is_password_hash(stored_password):
        return hmac.compare_digest(stored_password, password)

    try:
        _, iterations_str, salt_b64, digest_b64 = stored_password.split("$", 3)
        iterations = int(iterations_str)
        salt = _b64_decode(salt_b64)
        expected_digest = _b64_decode(digest_b64)
    except (TypeError, ValueError):
        return False

    actual_digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual_digest, expected_digest)
