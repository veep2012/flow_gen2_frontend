import os
import time
import uuid

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
    """TS-GET-002: revision overview ordering must follow the configured lifecycle path."""
    with httpx.Client(timeout=10) as client:
        result = _request(client, f"{_build_base_url()}/documents/revision_overview")
        assert result["status"] == 200
        assert isinstance(result["payload"], list)
        assert result["payload"], "Expected seeded revision overview steps"

        steps = result["payload"]
        returned_ids = [step["rev_code_id"] for step in steps]
        assert len(returned_ids) == len(set(returned_ids))

        starts = [step for step in steps if step.get("start") is True]
        finals = [step for step in steps if step.get("final") is True]
        assert len(starts) == 1
        assert len(finals) == 1
        assert steps[0]["start"] is True
        assert steps[-1]["final"] is True

        engine = create_engine(_build_admin_database_url())
        with engine.begin() as conn:
            path_ids = list(
                conn.execute(
                    text(
                        """
                        WITH RECURSIVE revision_flow AS (
                            SELECT rev_code_id, next_rev_code_id, 1 AS step_order
                            FROM ref.revision_overview
                            WHERE start IS TRUE
                            UNION ALL
                            SELECT child.rev_code_id, child.next_rev_code_id, parent.step_order + 1
                            FROM ref.revision_overview AS child
                            JOIN revision_flow AS parent
                              ON child.rev_code_id = parent.next_rev_code_id
                        )
                        SELECT rev_code_id
                        FROM revision_flow
                        ORDER BY step_order
                        """
                    )
                ).scalars()
            )
            id_sorted_ids = list(
                conn.execute(
                    text(
                        """
                        SELECT rev_code_id
                        FROM ref.revision_overview
                        ORDER BY rev_code_id
                        """
                    )
                ).scalars()
            )
            name_sorted_ids = list(
                conn.execute(
                    text(
                        """
                        SELECT rev_code_id
                        FROM ref.revision_overview
                        ORDER BY rev_code_name
                        """
                    )
                ).scalars()
            )

        assert returned_ids == path_ids
        assert path_ids != id_sorted_ids
        assert path_ids != name_sorted_ids

        for index, step in enumerate(steps):
            assert "next_rev_code_id" in step
            assert "final" in step
            assert "start" in step
            if index < len(steps) - 1:
                assert step["next_rev_code_id"] == steps[index + 1]["rev_code_id"]
                assert step["final"] is False
                assert step["next_rev_code_id"] is not None
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
        predecessor_of_final_id = conn.execute(
            text(
                """
                SELECT rev_code_id
                FROM ref.revision_overview
                WHERE next_rev_code_id = :final_id
                """
            ),
            {"final_id": final_id},
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
                    SET next_rev_code_id = :start_id
                    WHERE rev_code_id = :rev_code_id
                    """
                ),
                {"start_id": start_id, "rev_code_id": predecessor_of_final_id},
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

        with pytest.raises(DBAPIError):
            with conn.begin_nested():
                conn.execute(
                    text(
                        """
                        INSERT INTO ref.revision_overview (
                            rev_code_name,
                            rev_code_acronym,
                            rev_description,
                            next_rev_code_id,
                            final,
                            start,
                            percentage
                        ) VALUES (
                            'QDISC-CONNECT',
                            'QDCON',
                            'DISCONNECTED CONNECTIVITY CHECK',
                            :start_id,
                            FALSE,
                            FALSE,
                            15
                        )
                        """
                    ),
                    {"start_id": start_id},
                )
                conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))


@pytest.mark.api_smoke
def test_revision_overview_transactional_reconfiguration_and_insert_guards():
    """
    TS-GET-004: transactional chain extension must succeed while insert guardrails stay immediate.
    """
    engine = create_engine(_build_admin_database_url())
    token = uuid.uuid4().hex[:6].upper()
    with engine.begin() as conn:
        final_id = conn.execute(
            text(
                """
                SELECT rev_code_id
                FROM ref.revision_overview
                WHERE final IS TRUE
                """
            )
        ).scalar_one()
        start_id = conn.execute(
            text(
                """
                SELECT rev_code_id
                FROM ref.revision_overview
                WHERE start IS TRUE
                """
            )
        ).scalar_one()
        start_predecessor_count = conn.execute(
            text(
                """
                SELECT COUNT(*)
                FROM ref.revision_overview
                WHERE next_rev_code_id = :start_id
                """
            ),
            {"start_id": start_id},
        ).scalar_one()
        original_count = conn.execute(
            text("SELECT COUNT(*) FROM ref.revision_overview")
        ).scalar_one()
        original_path_ids = list(
            conn.execute(
                text(
                    """
                    WITH RECURSIVE revision_flow AS (
                        SELECT rev_code_id, next_rev_code_id, 1 AS step_order
                        FROM ref.revision_overview
                        WHERE start IS TRUE
                        UNION ALL
                        SELECT child.rev_code_id, child.next_rev_code_id, parent.step_order + 1
                        FROM ref.revision_overview AS child
                        JOIN revision_flow AS parent
                          ON child.rev_code_id = parent.next_rev_code_id
                    )
                    SELECT rev_code_id
                    FROM revision_flow
                    ORDER BY step_order
                    """
                )
            ).scalars()
        )
        assert start_predecessor_count == 0

        nested = conn.begin_nested()
        try:
            inserted_id = conn.execute(
                text(
                    """
                    INSERT INTO ref.revision_overview (
                        rev_code_name,
                        rev_code_acronym,
                        rev_description,
                        next_rev_code_id,
                        final,
                        start,
                        percentage
                    ) VALUES (
                        :rev_code_name,
                        :rev_code_acronym,
                        :rev_description,
                        :next_rev_code_id,
                        FALSE,
                        FALSE,
                        95
                    )
                    RETURNING rev_code_id
                    """
                ),
                {
                    "rev_code_name": f"QA{token}",
                    "rev_code_acronym": token[:5],
                    "rev_description": f"QA TRANSITION {token}",
                    "next_rev_code_id": start_id,
                },
            ).scalar_one()

            conn.execute(
                text(
                    """
                    UPDATE ref.revision_overview
                    SET start = FALSE
                    WHERE rev_code_id = :start_id
                    """
                ),
                {"start_id": start_id},
            )
            conn.execute(
                text(
                    """
                    UPDATE ref.revision_overview
                    SET start = TRUE
                    WHERE rev_code_id = :inserted_id
                    """
                ),
                {"inserted_id": inserted_id},
            )
            conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))

            path_ids = list(
                conn.execute(
                    text(
                        """
                        WITH RECURSIVE revision_flow AS (
                            SELECT rev_code_id, next_rev_code_id, 1 AS step_order
                            FROM ref.revision_overview
                            WHERE start IS TRUE
                            UNION ALL
                            SELECT child.rev_code_id, child.next_rev_code_id, parent.step_order + 1
                            FROM ref.revision_overview AS child
                            JOIN revision_flow AS parent
                              ON child.rev_code_id = parent.next_rev_code_id
                        )
                        SELECT rev_code_id
                        FROM revision_flow
                        ORDER BY step_order
                        """
                    )
                ).scalars()
            )
            assert len(path_ids) == original_count + 1
            assert path_ids[0] == inserted_id
            assert path_ids[1] == start_id
            assert path_ids[-1] == final_id
            assert conn.execute(
                text("SELECT COUNT(*) FROM ref.revision_overview")
            ).scalar_one() == (original_count + 1)
        finally:
            nested.rollback()

        assert (
            conn.execute(text("SELECT COUNT(*) FROM ref.revision_overview")).scalar_one()
            == original_count
        )
        assert (
            list(
                conn.execute(
                    text(
                        """
                    WITH RECURSIVE revision_flow AS (
                        SELECT rev_code_id, next_rev_code_id, 1 AS step_order
                        FROM ref.revision_overview
                        WHERE start IS TRUE
                        UNION ALL
                        SELECT child.rev_code_id, child.next_rev_code_id, parent.step_order + 1
                        FROM ref.revision_overview AS child
                        JOIN revision_flow AS parent
                          ON child.rev_code_id = parent.next_rev_code_id
                    )
                    SELECT rev_code_id
                    FROM revision_flow
                    ORDER BY step_order
                    """
                    )
                ).scalars()
            )
            == original_path_ids
        )

        invalid_inserts = (
            (
                text(
                    """
                    INSERT INTO ref.revision_overview (
                        rev_code_name,
                        rev_code_acronym,
                        rev_description,
                        next_rev_code_id,
                        final,
                        start,
                        percentage
                    ) VALUES (
                        :rev_code_name,
                        :rev_code_acronym,
                        :rev_description,
                        :next_rev_code_id,
                        FALSE,
                        TRUE,
                        5
                    )
                    """
                ),
                {
                    "rev_code_name": f"QS{token}",
                    "rev_code_acronym": f"S{token[:4]}",
                    "rev_description": f"QA START {token}",
                    "next_rev_code_id": start_id,
                },
            ),
            (
                text(
                    """
                    INSERT INTO ref.revision_overview (
                        rev_code_name,
                        rev_code_acronym,
                        rev_description,
                        next_rev_code_id,
                        final,
                        start,
                        percentage
                    ) VALUES (
                        :rev_code_name,
                        :rev_code_acronym,
                        :rev_description,
                        NULL,
                        TRUE,
                        FALSE,
                        100
                    )
                    """
                ),
                {
                    "rev_code_name": f"QF{token}",
                    "rev_code_acronym": f"F{token[:4]}",
                    "rev_description": f"QA FINAL {token}",
                },
            ),
            (
                text(
                    """
                    INSERT INTO ref.revision_overview (
                        rev_code_name,
                        rev_code_acronym,
                        rev_description,
                        next_rev_code_id,
                        final,
                        start,
                        percentage
                    ) VALUES (
                        :rev_code_name,
                        :rev_code_acronym,
                        :rev_description,
                        :next_rev_code_id,
                        FALSE,
                        FALSE,
                        85
                    )
                    """
                ),
                {
                    "rev_code_name": f"QP{token}",
                    "rev_code_acronym": f"P{token[:4]}",
                    "rev_description": f"QA PRED {token}",
                    "next_rev_code_id": final_id,
                },
            ),
            (
                text(
                    """
                    INSERT INTO ref.revision_overview (
                        rev_code_name,
                        rev_code_acronym,
                        rev_description,
                        next_rev_code_id,
                        final,
                        start,
                        percentage
                    ) VALUES (
                        :rev_code_name,
                        :rev_code_acronym,
                        :rev_description,
                        :next_rev_code_id,
                        FALSE,
                        FALSE,
                        15
                    )
                    """
                ),
                {
                    "rev_code_name": f"QC{token}",
                    "rev_code_acronym": f"C{token[:4]}",
                    "rev_description": f"QA CONNECT {token}",
                    "next_rev_code_id": start_id,
                },
            ),
        )

        for statement, params in invalid_inserts:
            with pytest.raises(DBAPIError):
                with conn.begin_nested():
                    conn.execute(statement, params)
                    conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
