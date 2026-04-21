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
