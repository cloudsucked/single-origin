from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.db import init_db, seed_db
from app.main import app

init_db()
seed_db()


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"


def test_products_endpoint_returns_seeded_data() -> None:
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert len(payload) >= 1


def test_debug_headers_echoes_incoming_headers() -> None:
    response = client.get(
        "/debug/headers",
        headers={
            "Cf-Client-Cert-Subject-DN": "CN=lab-client, O=Cloudflare Lab",
            "Cf-Client-Cert-Fingerprint-Sha256": "deadbeef",
            "X-Lab-Test": "hello",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["method"] == "GET"
    assert payload["path"] == "/debug/headers"
    names = {h["name"].lower(): h["value"] for h in payload["headers"]}
    assert names.get("cf-client-cert-subject-dn") == "CN=lab-client, O=Cloudflare Lab"
    assert names.get("cf-client-cert-fingerprint-sha256") == "deadbeef"
    assert names.get("x-lab-test") == "hello"


def test_debug_headers_rejects_non_get_methods() -> None:
    response = client.post("/debug/headers")
    assert response.status_code == 405


# ── Cookie fixture set (Page Shield Cookie Monitor) ─────────────────────────


def test_js_so_analytics_sets_analytics_cookie() -> None:
    response = client.get("/js/so-analytics.js")
    assert response.status_code == 200
    assert "_so_analytics=" in response.text
    assert "samesite=lax" in response.text.lower()


def test_js_social_pixel_sets_social_cookie() -> None:
    response = client.get("/js/social-pixel.js")
    assert response.status_code == 200
    assert "_so_social=" in response.text


def test_js_cart_and_prefs_bundles_exist_and_set_cookies() -> None:
    cart = client.get("/js/cart.js")
    assert cart.status_code == 200
    assert "so_cart=" in cart.text

    prefs = client.get("/js/prefs.js")
    assert prefs.status_code == 200
    assert "so_prefs=" in prefs.text
    # default prefs payload
    assert "roast" in prefs.text
    assert "display" in prefs.text


def test_cookie_consent_script_sets_consent_cookie() -> None:
    response = client.get("/js/cookie-consent.js")
    assert response.status_code == 200
    assert "so_consent=accepted" in response.text


def test_checkout_sdk_safe_variant_has_no_exfil() -> None:
    """The default `v=1.2.3` variant must not fetch the exfil target."""
    response = client.get("/js/checkout-sdk.js")
    assert response.status_code == 200
    assert "exfil" not in response.text.lower()
    assert "payments.singleorigin.example" in response.text


def test_checkout_sdk_compromised_variant_includes_configured_exfil_url() -> None:
    """The `v=1.2.4` variant fetches the URL from `CHECKOUT_SDK_EXFIL_URL`."""
    from app.config import settings

    response = client.get("/js/checkout-sdk.js?v=1.2.4")
    assert response.status_code == 200
    # Exfil URL from settings is baked into the served JS
    assert settings.checkout_sdk_exfil_url in response.text
    # Safe-path fetch still present
    assert "payments.singleorigin.example" in response.text


def test_register_api_sets_so_session_cookie() -> None:
    """Successful auth flows set the `so_session` fixture cookie.

    Registers a fresh user (isolated from seeded accounts) so this test
    doesn't depend on seed password state across the suite.
    """
    from secrets import token_urlsafe

    email = f"cookie-probe-{token_urlsafe(6)}@example.com"
    password = token_urlsafe(20)
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "name": "Cookie Probe"},
    )
    assert response.status_code == 200, response.text
    # The JSON body still carries the token for existing clients…
    body = response.json()
    assert "token" in body
    # …and the so_session cookie is set for Page Shield Cookie Monitor.
    assert "so_session" in response.cookies
    assert response.cookies["so_session"] == body["token"]
