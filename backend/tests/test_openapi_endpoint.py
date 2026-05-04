"""End-to-end tests for the runtime `/openapi.json` endpoint.

These exercise the three-step server-URL fallback chain:

1. ``settings.derive_api_public_url()`` from the existing
   ``CHECKOUT_SDK_EXFIL_URL`` env var (production lab pods).
2. The inbound request ``Host`` / ``X-Forwarded-Host`` headers (any reverse
   proxy that does not propagate the env var).
3. The hard-coded placeholder (offline / unit-test contexts).

They also smoke-test the docs and redoc HTML routes that we re-registered
after disabling the FastAPI built-ins.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import main as app_main  # noqa: E402
from app.config import Settings  # noqa: E402
from app.main import DEFAULT_API_PUBLIC_URL, app  # noqa: E402


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def _reset_openapi_cache() -> Iterator[None]:
    """Clear the per-app OpenAPI cache between tests so settings overrides take effect."""
    app.openapi_schema = None
    yield
    app.openapi_schema = None


# ---------------------------------------------------------------------------
# derive_api_public_url
# ---------------------------------------------------------------------------


def test_derive_api_public_url_swaps_role_subdomain_for_api() -> None:
    s = Settings(checkout_sdk_exfil_url="https://exfil.adaptive-database.sxplab.com/skim")
    assert s.derive_api_public_url() == "https://api.adaptive-database.sxplab.com"


def test_derive_api_public_url_returns_none_for_slug_placeholder() -> None:
    s = Settings(checkout_sdk_exfil_url="https://exfil.{SLUG}.sxplab.com/skim")
    assert s.derive_api_public_url() is None


def test_derive_api_public_url_returns_none_for_unknown_host_pattern() -> None:
    s = Settings(checkout_sdk_exfil_url="https://corp.example.com/skim")
    assert s.derive_api_public_url() is None


def test_derive_api_public_url_returns_none_for_empty_value() -> None:
    s = Settings(checkout_sdk_exfil_url="")
    assert s.derive_api_public_url() is None


# ---------------------------------------------------------------------------
# /openapi.json runtime fallback chain
# ---------------------------------------------------------------------------


def test_openapi_endpoint_uses_env_var_when_available(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        app_main.settings,
        "checkout_sdk_exfil_url",
        "https://exfil.adaptive-database.sxplab.com/skim",
    )

    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    assert resp.json()["servers"] == [{"url": "https://api.adaptive-database.sxplab.com"}]


def test_openapi_endpoint_falls_back_to_request_host_when_env_unhelpful(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Wipe the env var so derive_api_public_url() returns None.
    monkeypatch.setattr(app_main.settings, "checkout_sdk_exfil_url", "")

    resp = client.get(
        "/openapi.json",
        headers={"host": "api.requestor.example", "x-forwarded-proto": "https"},
    )
    assert resp.status_code == 200
    assert resp.json()["servers"] == [{"url": "https://api.requestor.example"}]


def test_openapi_endpoint_prefers_x_forwarded_host_over_host(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(app_main.settings, "checkout_sdk_exfil_url", "")

    resp = client.get(
        "/openapi.json",
        headers={
            "host": "internal.example",
            "x-forwarded-host": "public.example",
            "x-forwarded-proto": "https",
        },
    )
    assert resp.json()["servers"] == [{"url": "https://public.example"}]


def test_openapi_endpoint_takes_first_proto_token_when_x_forwarded_proto_is_a_list(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """RFC 7239 / nginx / HAProxy / AWS ALB can emit ``X-Forwarded-Proto: https, http``."""
    monkeypatch.setattr(app_main.settings, "checkout_sdk_exfil_url", "")

    resp = client.get(
        "/openapi.json",
        headers={
            "host": "api.requestor.example",
            "x-forwarded-proto": "https, http",
        },
    )
    assert resp.json()["servers"] == [{"url": "https://api.requestor.example"}]


def test_openapi_endpoint_rejects_unsafe_scheme_in_x_forwarded_proto(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A spoofed ``X-Forwarded-Proto: javascript`` must not poison the served servers URL."""
    monkeypatch.setattr(app_main.settings, "checkout_sdk_exfil_url", "")

    resp = client.get(
        "/openapi.json",
        headers={
            "host": "api.requestor.example",
            "x-forwarded-proto": "javascript",
        },
    )
    # Anything outside {http, https} is replaced with https.
    assert resp.json()["servers"] == [{"url": "https://api.requestor.example"}]


def test_openapi_endpoint_rejects_injected_host_with_path_separator(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``Host: evil.example/poison`` would otherwise produce a URL with a stray path."""
    monkeypatch.setattr(app_main.settings, "checkout_sdk_exfil_url", "")

    resp = client.get(
        "/openapi.json",
        headers={"host": "evil.example/poison"},
    )
    # Falls through to the placeholder because the host fails validation.
    assert resp.json()["servers"] == [{"url": app_main.DEFAULT_API_PUBLIC_URL}]


def test_openapi_endpoint_rejects_injected_host_with_userinfo(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``Host: user@evil.example`` would otherwise become ``https://user@evil.example``."""
    monkeypatch.setattr(app_main.settings, "checkout_sdk_exfil_url", "")

    resp = client.get(
        "/openapi.json",
        headers={"host": "attacker@evil.example"},
    )
    assert resp.json()["servers"] == [{"url": app_main.DEFAULT_API_PUBLIC_URL}]


# ---------------------------------------------------------------------------
# Cloudflare-compatibility invariants on the live response
# ---------------------------------------------------------------------------


def test_openapi_endpoint_returns_oas_3_0_3(client: TestClient) -> None:
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    assert resp.json()["openapi"] == "3.0.3"


def test_openapi_endpoint_emits_no_anyof_with_null(client: TestClient) -> None:
    """The whole point of the conversion: the response must be free of the
    nullable ``anyOf`` pattern that Cloudflare rejects."""
    body = client.get("/openapi.json").text
    assert '"type": "null"' not in body, (
        "Found a `type: null` entry in the served spec — the OpenAPI 3.1 → "
        "3.0.3 conversion in app.openapi_compat is not running."
    )


# ---------------------------------------------------------------------------
# Docs / Redoc still work after we replaced the built-in FastAPI routes
# ---------------------------------------------------------------------------


def test_docs_route_serves_swagger_ui(client: TestClient) -> None:
    resp = client.get("/docs")
    assert resp.status_code == 200
    assert "swagger-ui" in resp.text.lower()
    assert "/openapi.json" in resp.text


def test_redoc_route_serves_redoc(client: TestClient) -> None:
    resp = client.get("/redoc")
    assert resp.status_code == 200
    assert "redoc" in resp.text.lower()
    assert "/openapi.json" in resp.text
