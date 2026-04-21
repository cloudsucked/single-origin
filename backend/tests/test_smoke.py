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


# ── Alt-auth JSON variants (Traffic Detections) ──────────────────────────


def test_api_v2_auth_rejects_invalid_credentials() -> None:
    response = client.post(
        "/api/v2/auth",
        json={"username": "nobody@example.com", "password": "wrong"},
    )
    assert response.status_code == 401


def test_api_v2_auth_issues_token_on_valid_credentials() -> None:
    from secrets import token_urlsafe

    email = f"altauth-v2-{token_urlsafe(6)}@example.com"
    password = token_urlsafe(20)
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "name": "Alt V2"},
    )
    assert reg.status_code == 200
    response = client.post(
        "/api/v2/auth",
        json={"username": email, "password": password},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["version"] == "v2"
    assert "token" in body
    assert body["user"]["email"] == email


def test_api_mobile_login_rejects_invalid_credentials() -> None:
    response = client.post(
        "/api/mobile/login",
        json={"email": "nobody@example.com", "password": "wrong"},
    )
    assert response.status_code == 401


def test_api_mobile_login_uses_email_field_and_issues_token() -> None:
    from secrets import token_urlsafe

    email = f"altauth-mobile-{token_urlsafe(6)}@example.com"
    password = token_urlsafe(20)
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "name": "Alt Mobile"},
    )
    assert reg.status_code == 200
    response = client.post(
        "/api/mobile/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["version"] == "mobile"
    assert "token" in body


def test_api_mobile_login_rejects_username_field() -> None:
    """Field must be `email`; passing `username` should fail with 400."""
    response = client.post(
        "/api/mobile/login",
        json={"username": "demo@singleorigin.example", "password": "anything"},
    )
    assert response.status_code == 400


# ── AI Gateway proxy mode ────────────────────────────────────────────────


def test_ai_chat_defaults_to_canned_response_when_gateway_disabled() -> None:
    """With AI_GATEWAY_ENABLED=false (default), the canned lab response flows."""
    response = client.post(
        "/api/v1/ai/chat",
        json={"model": "brew-assistant-v1", "messages": [{"role": "user", "content": "test"}]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "chatcmpl-so-1"
    assert "Yirgacheffe" in body["choices"][0]["message"]["content"]


def test_ai_chat_proxies_to_ai_gateway_when_enabled(monkeypatch) -> None:
    """When AI_GATEWAY_ENABLED=true, the handler proxies and normalizes the response."""
    import httpx

    from app.config import settings

    captured = {}

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "id": "chatcmpl-abc123",
                "object": "chat.completion",
                "choices": [
                    {"index": 0, "message": {"role": "assistant", "content": "Fake gateway reply"}}
                ],
            }

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, headers=None, json=None):
            captured["url"] = url
            captured["headers"] = headers or {}
            captured["json"] = json or {}
            return FakeResponse()

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(settings, "ai_gateway_enabled", True)
    monkeypatch.setattr(
        settings,
        "ai_gateway_url",
        "https://gateway.ai.cloudflare.com/v1/acc/gw/workers-ai/@cf/meta/llama-3.1-8b-instruct",
    )
    monkeypatch.setattr(settings, "ai_gateway_token", "test-token-xyz")

    response = client.post(
        "/api/v1/ai/chat",
        json={"model": "brew-assistant-v1", "messages": [{"role": "user", "content": "hi"}]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "chatcmpl-abc123"
    assert body["choices"][0]["message"]["content"] == "Fake gateway reply"

    # Verify the proxy actually called the gateway with the right headers and
    # that the model alias was rewritten from the lab name to the real model.
    assert captured["url"] == settings.ai_gateway_url
    assert captured["headers"]["cf-aig-authorization"] == "Bearer test-token-xyz"
    assert captured["json"]["model"] == settings.ai_model


def test_ai_chat_returns_502_when_gateway_misconfigured(monkeypatch) -> None:
    """Enabled but no URL configured → 502, not a silent fallback."""
    from app.config import settings

    monkeypatch.setattr(settings, "ai_gateway_enabled", True)
    monkeypatch.setattr(settings, "ai_gateway_url", "")

    response = client.post(
        "/api/v1/ai/chat",
        json={"model": "brew-assistant-v1", "messages": [{"role": "user", "content": "hi"}]},
    )
    assert response.status_code == 502
    body = response.json()
    assert "ai_gateway_url_missing" in str(body)


# ── Strawberry GraphQL schema ────────────────────────────────────────────


def test_graphql_returns_products_from_real_schema() -> None:
    response = client.post(
        "/graphql",
        json={"query": "{ products(limit: 5) { id name slug price } }"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body, body
    products = body["data"]["products"]
    assert len(products) >= 1
    first = products[0]
    assert "id" in first and "name" in first and "price" in first
    # `price` is a real Float, not a string — confirms the schema resolved it.
    assert isinstance(first["price"], (int, float))


def test_graphql_supports_deep_farm_origin_nesting() -> None:
    """Self-referential Farm→Origin→Farm nesting is the depth fixture."""
    deep_query = """
    {
      product(id: "1") {
        id
        name
        farm {
          name
          origin {
            country
            farm {
              name
              origin {
                country
                farm {
                  name
                }
              }
            }
          }
        }
      }
    }
    """
    response = client.post("/graphql", json={"query": deep_query})
    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body, body
    inner = body["data"]["product"]["farm"]["origin"]["farm"]["origin"]["farm"]["name"]
    assert isinstance(inner, str) and len(inner) > 0


def test_graphql_sets_complexity_score_header() -> None:
    response = client.post(
        "/graphql",
        json={"query": "{ products { id } }"},
    )
    assert response.status_code == 200
    assert COMPLEXITY_HEADER in response.headers


def test_graphql_rejects_invalid_json_with_400() -> None:
    response = client.post(
        "/graphql",
        content="not json at all",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400


# imported at top of test file helper block
from app.services.complexity import COMPLEXITY_HEADER  # noqa: E402


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
