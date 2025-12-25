import os
import time

import httpx
import pytest


def _build_base_url() -> str:
    base = os.getenv("API_BASE", "http://localhost:5556").rstrip("/")
    prefix = os.getenv("API_PREFIX", "/api/v1").rstrip("/")
    if not prefix.startswith("/"):
        prefix = f"/{prefix}"
    return f"{base}{prefix}"


def _request(client: httpx.Client, method: str, path: str, **kwargs) -> dict:
    url = f"{_build_base_url()}{path}"
    start = time.perf_counter()
    response = client.request(method, url, **kwargs)
    duration_ms = (time.perf_counter() - start) * 1000
    payload = None
    if response.content:
        try:
            payload = response.json()
        except ValueError:
            payload = response.text
    return {
        "status": response.status_code,
        "payload": payload,
        "duration_ms": duration_ms,
    }


@pytest.mark.api_smoke
def test_selectable_lookup_endpoints():
    endpoints = [
        "/lookups/projects",
        "/lookups/areas",
        "/lookups/units",
        "/lookups/jobpacks",
        "/lookups/disciplines",
        "/documents/doc_types",
        "/documents/revision_overview",
        "/lookups/doc_rev_statuses",
    ]

    with httpx.Client(timeout=10) as client:
        for path in endpoints:
            result = _request(client, "GET", path)
            if result["status"] == 404:
                pytest.skip(f"{path} returned 404 (no data)")
            assert 200 <= result["status"] < 300, f"{path} failed: {result['status']}"
            assert isinstance(result["payload"], list), f"{path} payload is not a list"
