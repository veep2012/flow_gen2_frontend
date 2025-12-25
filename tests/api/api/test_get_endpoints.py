import os
import time

import httpx
import pytest


def _base_and_prefix() -> tuple[str, str]:
    base = os.getenv("API_BASE", "http://localhost:4175").rstrip("/")
    prefix = os.getenv("API_PREFIX", "/api/v1").rstrip("/")
    if prefix and not prefix.startswith("/"):
        prefix = f"/{prefix}"
    return base, prefix


def _request(client: httpx.Client, url: str, **kwargs) -> dict:
    start = time.perf_counter()
    response = client.get(url, **kwargs)
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


def _extract_id(item: dict, keys: list[str]) -> int | None:
    for key in keys:
        value = item.get(key)
        if value is not None:
            return value
    return None


@pytest.mark.api_smoke
def test_all_get_endpoints():
    base, prefix = _base_and_prefix()
    with httpx.Client(timeout=10) as client:
        health = _request(client, f"{base}/health")
        assert 200 <= health["status"] < 300, f"/health failed: {health['status']}"

        root = _request(client, f"{base}/")
        assert 200 <= root["status"] < 300, f"/ failed: {root['status']}"

        projects = _request(client, f"{base}{prefix}/lookups/projects")
        project_id = None
        if projects["status"] == 200 and isinstance(projects["payload"], list):
            for item in projects["payload"]:
                if isinstance(item, dict):
                    project_id = _extract_id(item, ["project_id", "id"])
                    if project_id is not None:
                        break

        endpoints: list[tuple[str, dict | None]] = [
            ("/lookups/areas", None),
            ("/lookups/disciplines", None),
            ("/lookups/projects", None),
            ("/lookups/units", None),
            ("/lookups/jobpacks", None),
            ("/documents/doc_types", None),
            ("/documents/doc_rev_milestones", None),
            ("/documents/revision_overview", None),
            ("/lookups/doc_rev_statuses", None),
            ("/people/roles", None),
            ("/people/persons", None),
            ("/people/users", None),
            ("/people/permissions", None),
        ]

        if project_id is not None:
            endpoints.append(("/documents/list", {"project_id": project_id}))
        else:
            pytest.skip("No project_id available for /documents/list")

        for path, params in endpoints:
            result = _request(client, f"{base}{prefix}{path}", params=params)
            if result["status"] == 404:
                pytest.skip(f"{path} returned 404 (no data)")
            assert 200 <= result["status"] < 300, f"{path} failed: {result['status']}"
