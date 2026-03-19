import os
import time

import httpx
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import DBAPIError

_DEFAULT_TEST_USER_ACRONYM = os.getenv("TEST_USER_ACRONYM", "FDQC")


def _base_and_prefix() -> tuple[str, str]:
    base = os.getenv("API_BASE", "http://localhost:4175").rstrip("/")
    prefix = os.getenv("API_PREFIX", "/api/v1").rstrip("/")
    if prefix and not prefix.startswith("/"):
        prefix = f"/{prefix}"
    return base, prefix


def _build_base_url() -> str:
    base, prefix = _base_and_prefix()
    return f"{base}{prefix}"


def _merge_default_auth(kwargs: dict) -> dict:
    merged = dict(kwargs)
    if merged.pop("auth", True):
        headers = dict(merged.get("headers") or {})
        headers.setdefault("X-User-Id", _DEFAULT_TEST_USER_ACRONYM)
        merged["headers"] = headers
    return merged


def _request(client: httpx.Client, url: str, **kwargs) -> dict:
    start = time.perf_counter()
    response = client.get(url, **_merge_default_auth(kwargs))
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


def _build_admin_database_url() -> str:
    """Build the admin database URL for direct test-only constraint checks.

    Prefers TEST_DB_ADMIN_URL when provided. Otherwise it assembles a URL from
    TEST_DB_ADMIN_USER, TEST_DB_ADMIN_PASSWORD, POSTGRES_HOST, POSTGRES_PORT,
    and TEST_DB_NAME/POSTGRES_DB so the smoke tests can connect to the seeded
    database with admin privileges.
    """
    explicit_admin = os.getenv("TEST_DB_ADMIN_URL")
    if explicit_admin:
        return explicit_admin

    user = os.getenv("TEST_DB_ADMIN_USER", "postgres")
    password = os.getenv("TEST_DB_ADMIN_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5433")
    db_name = os.getenv("TEST_DB_NAME", os.getenv("POSTGRES_DB", "flow_db_test"))
    return str(
        URL.create(
            "postgresql+psycopg",
            username=user,
            password=password,
            host=host,
            port=int(port),
            database=db_name,
        ).render_as_string(hide_password=False)
    )


@pytest.mark.api_smoke
def test_all_get_endpoints():
    base, prefix = _base_and_prefix()
    with httpx.Client(timeout=10) as client:
        health = _request(client, f"{base}/health")
        assert 200 <= health["status"] < 300, f"/health failed: {health['status']}"

        root = _request(client, f"{base}/")
        assert 200 <= root["status"] < 300, f"/ failed: {root['status']}"

        metrics = _request(client, f"{base}/metrics", auth=False)
        assert 200 <= metrics["status"] < 300, f"/metrics failed: {metrics['status']}"
        assert isinstance(metrics["payload"], str), "/metrics must return text payload"

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
            ("/lookups/doc_rev_status_ui_behaviors", None),
            ("/lookups/doc_rev_statuses", None),
            ("/people/roles", None),
            ("/people/persons", None),
            ("/people/users", None),
            ("/people/permissions", None),
        ]

        if project_id is not None:
            endpoints.append(("/documents", {"project_id": project_id}))
        else:
            pytest.skip("No project_id available for /documents")

        for path, params in endpoints:
            result = _request(client, f"{base}{prefix}{path}", params=params)
            if result["status"] == 404:
                pytest.skip(f"{path} returned 404 (no data)")
            assert 200 <= result["status"] < 300, f"{path} failed: {result['status']}"


@pytest.mark.api_smoke
def test_revision_overview_represents_single_lifecycle_path():
    with httpx.Client(timeout=10) as client:
        result = _request(client, f"{_build_base_url()}/documents/revision_overview")
        assert result["status"] == 200
        assert isinstance(result["payload"], list)
        assert result["payload"], "Expected seeded revision overview steps"

        steps = result["payload"]
        step_ids = [step["rev_code_id"] for step in steps]
        assert len(step_ids) == len(set(step_ids))

        starts = [step for step in steps if step.get("start") is True]
        finals = [step for step in steps if step.get("final") is True]
        assert len(starts) == 1
        assert len(finals) == 1
        assert steps[0]["start"] is True
        assert steps[-1]["final"] is True

        for index, step in enumerate(steps):
            assert "next_rev_code_id" in step
            assert "revertible" in step
            assert "editable" in step
            assert "final" in step
            assert "start" in step
            if index < len(steps) - 1:
                assert step["next_rev_code_id"] == steps[index + 1]["rev_code_id"]
                assert step["final"] is False
            else:
                assert step["next_rev_code_id"] is None
                assert step["final"] is True


@pytest.mark.api_smoke
def test_revision_overview_constraints_reject_invalid_lifecycle_updates():
    engine = create_engine(_build_admin_database_url())
    with engine.begin() as conn:
        start_id = conn.execute(
            text(
                """
                SELECT rev_code_id
                FROM ref.revision_overview
                WHERE start IS TRUE
                """
            )
        ).scalar_one()
        final_id = conn.execute(
            text(
                """
                SELECT rev_code_id
                FROM ref.revision_overview
                WHERE final IS TRUE
                """
            )
        ).scalar_one()
        other_id = conn.execute(
            text(
                """
                SELECT rev_code_id
                FROM ref.revision_overview
                WHERE rev_code_id NOT IN (:start_id, :final_id)
                ORDER BY rev_code_id
                LIMIT 1
                """
            ),
            {"start_id": start_id, "final_id": final_id},
        ).scalar_one()

        invalid_statements = (
            (
                text(
                    """
                    UPDATE ref.revision_overview
                    SET next_rev_code_id = rev_code_id
                    WHERE rev_code_id = :rev_code_id
                    """
                ),
                {"rev_code_id": other_id},
            ),
            (
                text(
                    """
                    UPDATE ref.revision_overview
                    SET start = TRUE
                    WHERE rev_code_id = :rev_code_id
                    """
                ),
                {"rev_code_id": other_id},
            ),
            (
                text(
                    """
                    UPDATE ref.revision_overview
                    SET next_rev_code_id = :next_rev_code_id,
                        final = TRUE
                    WHERE rev_code_id = :rev_code_id
                    """
                ),
                {"next_rev_code_id": start_id, "rev_code_id": final_id},
            ),
            (
                text(
                    """
                    UPDATE ref.revision_overview
                    SET next_rev_code_id = :next_rev_code_id,
                        final = FALSE
                    WHERE rev_code_id = :rev_code_id
                    """
                ),
                {"next_rev_code_id": start_id, "rev_code_id": final_id},
            ),
        )

        for statement, params in invalid_statements:
            with pytest.raises(DBAPIError):
                with conn.begin_nested():
                    conn.execute(statement, params)
