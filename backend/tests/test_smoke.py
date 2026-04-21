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


# ── /checkout/submit form handler ─────────────────────────────────────────


def _checkout_form_payload() -> dict[str, str]:
    return {
        "card_number": "4242424242424242",
        "card_exp": "12/29",
        "card_cvv": "123",
        "billing_name": "Alex Demo",
        "billing_address": "123 Roast St",
        "billing_city": "San Francisco",
        "billing_country": "US",
        "billing_zip": "94107",
        "phone": "+1-555-0100",
        "email": "demo@singleorigin.example",
        "total": "59.50",
    }


def test_checkout_submit_browser_flow_returns_303_redirect() -> None:
    response = client.post(
        "/checkout/submit",
        data=_checkout_form_payload(),
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith("/checkout/confirmation?order_id=")


def test_checkout_submit_api_flow_returns_json_order_id() -> None:
    response = client.post(
        "/checkout/submit",
        data=_checkout_form_payload(),
        headers={"Accept": "application/json"},
        follow_redirects=False,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "placed"
    assert isinstance(body["order_id"], int) and body["order_id"] > 0
    # Only last 4 of card number is persisted; full PAN must not round-trip.
    assert body["order"]["card_last4"] == "4242"
    assert "4242424242424242" not in str(body)


# ── POST /admin credential-stuffing form handler ─────────────────────────


def test_admin_form_login_rejects_unknown_user_with_401() -> None:
    response = client.post(
        "/admin",
        data={"username": "nobody@example.com", "password": "wrong"},
    )
    assert response.status_code == 401
    assert response.json()["error"] == "invalid_credentials"


def test_admin_form_login_rejects_non_admin_user_with_403() -> None:
    """A valid non-admin user authenticates but is denied admin access."""
    from secrets import token_urlsafe

    email = f"non-admin-{token_urlsafe(6)}@example.com"
    password = token_urlsafe(20)
    # Fresh non-admin user via the normal register flow.
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "name": "Not An Admin"},
    )
    assert reg.status_code == 200
    response = client.post(
        "/admin",
        data={"username": email, "password": password},
    )
    assert response.status_code == 403
    assert response.json()["error"] == "not_admin"


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
