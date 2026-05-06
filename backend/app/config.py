from __future__ import annotations

import re
from urllib.parse import urlparse

from pydantic_settings import BaseSettings, SettingsConfigDict

# Recognises the lab-pod hostname pattern used by every CML-provisioned pod.
# Matches the leftmost subdomain of "<role>.<slug>.sxplab.com" so we can
# substitute "api" for "<role>" and reuse the slug across other lab URLs
# without needing CML to plumb a second env var.
_SXPLAB_HOST_RE = re.compile(r"^(?P<role>[^.]+)\.(?P<slug>[^.]+)\.sxplab\.com$")


class Settings(BaseSettings):
    app_name: str = "Single Origin API"
    app_version: str = "0.1.0"
    cors_origin: str = "*"
    turnstile_secret_key: str = ""
    turnstile_expected_hostname: str = ""
    enforce_turnstile: bool = False

    # JWT signing — HS256 symmetric key (default / dev mode)
    jwt_secret_key: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"

    # Lab mode: when LAB_JWT_PRIVATE_KEY is set, the app switches to RS256 signing.
    # The private key is a PEM string with literal \n escape sequences (as stored
    # in environment variables / Terraform variables). The app normalises \n → newlines
    # at startup. Setting this also activates the JWKS endpoint with the matching
    # public key so Cloudflare API Shield JWT Validation can verify lab tokens.
    lab_jwt_private_key: str = ""

    database_path: str = "single_origin.db"
    seed_demo_email: str = "demo@singleorigin.example"
    seed_demo_password: str = ""
    seed_wholesale_email: str = "wholesale@cafepartner.example"
    seed_wholesale_password: str = ""
    seed_admin_email: str = "admin@singleorigin.example"
    seed_admin_password: str = ""
    seed_test_users_password: str = ""

    # In-memory cart guardrails. The lab traffic generator may use many
    # synthetic sessions, so carts must be bounded even though they are not
    # persisted in SQLite.
    cart_ttl_seconds: int = 3600
    cart_max_sessions: int = 200
    cart_max_items_per_session: int = 25

    # Page Shield checkout-sdk compromised-variant exfil target. The app serves
    # two variants from `/js/checkout-sdk.js`: `v=1.2.3` (safe) and `v=1.2.4`
    # (compromised, exfils cart to this URL). Default is a lab-zone subdomain
    # so DNS resolves and Cloudflare can log the outbound connection; override
    # via CHECKOUT_SDK_EXFIL_URL in CML pod env to point at a different host.
    # Use the literal `{SLUG}` placeholder in the default to force an explicit
    # choice in every pod (no accidental shared default).
    checkout_sdk_exfil_url: str = "https://exfil.{SLUG}.sxplab.com/skim"

    # AI Gateway proxy mode. When AI_GATEWAY_ENABLED=true, /api/v1/ai/chat and
    # /api/v1/ai/recommend proxy the prompt to Cloudflare AI Gateway instead
    # of returning the canned lab response. The AI Security for Apps course
    # depends on real prompt traffic flowing through the gateway so the
    # learner can observe PII redaction, prompt-injection detection, etc.
    ai_gateway_enabled: bool = False
    ai_gateway_url: str = ""  # e.g. "https://gateway.ai.cloudflare.com/v1/{account_id}/{gateway_id}/workers-ai/@cf/meta/llama-3.1-8b-instruct"
    ai_gateway_token: str = ""  # Bearer token passed as `cf-aig-authorization: Bearer <token>`
    ai_model: str = "@cf/meta/llama-3.1-8b-instruct"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def derive_api_public_url(self) -> str | None:
        """Best-effort derivation of the public API base URL from existing env.

        Cloudflare API Shield Schema validation requires an absolute server
        URL in the OpenAPI ``servers`` array. Rather than asking the CML
        ``generic-origin`` template to plumb a second env var, we piggyback
        on ``CHECKOUT_SDK_EXFIL_URL`` which already carries the pod slug
        (e.g. ``https://exfil.adaptive-database.sxplab.com/skim``). The API
        is reached at the same slug under the ``api`` subdomain
        (``https://api.adaptive-database.sxplab.com``), so we swap the
        leftmost subdomain.

        Returns ``None`` when:
        - the env var is unset,
        - the value still contains the literal ``{SLUG}`` placeholder, or
        - the host does not match the standard ``<role>.<slug>.sxplab.com``
          pattern (dev shells, custom deployments).

        In any of those cases the caller should fall back to deriving the
        URL from the inbound request ``Host`` header.
        """
        url = self.checkout_sdk_exfil_url
        if not url or "{SLUG}" in url:
            return None
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.hostname:
            return None
        match = _SXPLAB_HOST_RE.match(parsed.hostname)
        if not match:
            return None
        return f"{parsed.scheme}://api.{match.group('slug')}.sxplab.com"


settings = Settings()
