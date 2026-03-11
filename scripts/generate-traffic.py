#!/usr/bin/env python3
from __future__ import annotations

import json
import random
import time
import urllib.parse
import urllib.request

BASE = "http://localhost:8000"


def req(path: str, method: str = "GET", data: dict | None = None, headers: dict | None = None) -> None:
    body = None
    req_headers = headers or {}
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    request = urllib.request.Request(f"{BASE}{path}", data=body, method=method, headers=req_headers)
    try:
        with urllib.request.urlopen(request, timeout=5):
            return
    except Exception:
        return


def legit_flow() -> None:
    req("/api/v1/products")
    req("/api/v1/products/1")
    req("/api/v1/cart/items", method="POST", data={"product_id": 1, "quantity": 1})
    req("/api/v1/orders", method="POST", data={"items": [{"product_id": 1, "quantity": 1}]})


def noisy_flow() -> None:
    payload = random.choice([
        "coffee' OR 1=1--",
        "<script>alert(1)</script>",
        "../../../etc/passwd",
    ])
    q = urllib.parse.quote_plus(payload)
    req(f"/api/v1/search?q={q}")


def main() -> None:
    for _ in range(200):
        if random.random() < 0.75:
            legit_flow()
        else:
            noisy_flow()
        time.sleep(random.uniform(0.05, 0.2))
    print("Traffic generation complete")


if __name__ == "__main__":
    main()
