import os
import time
import uuid

import httpx
import pytest
from sqlalchemy import create_engine, text

CORE_AUDIT_TABLES = (
    "doc",
    "doc_revision",
    "files",
    "files_commented",
    "written_comments",
    "distribution_list",
    "distribution_list_content",
    "notifications",
    "notification_targets",
    "notification_recipients",
)
ZAML_PROJECT_ID = 3


def _build_base_url() -> str:
    base = os.getenv("API_BASE", "http://localhost:4175").rstrip("/")
    prefix = os.getenv("API_PREFIX", "/api/v1").rstrip("/")
    if prefix and not prefix.startswith("/"):
        prefix = f"/{prefix}"
    return f"{base}{prefix}"


def _request(client: httpx.Client, method: str, path: str, **kwargs) -> dict:
    url = f"{_build_base_url()}{path}"
    start = time.perf_counter()
    response = client.request(method, url, **kwargs)
    duration_ms = (time.perf_counter() - start) * 1000
    payload = None
    if response.content and "application/json" in response.headers.get("content-type", ""):
        payload = response.json()
    return {
        "status": response.status_code,
        "payload": payload,
        "duration_ms": duration_ms,
    }


def _build_test_database_url() -> str:
    explicit_admin = os.getenv("TEST_DB_ADMIN_URL")
    if explicit_admin:
        return explicit_admin

    user = os.getenv("TEST_DB_ADMIN_USER", "postgres")
    password = os.getenv("TEST_DB_ADMIN_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5433")
    db_name = os.getenv("TEST_DB_NAME", os.getenv("POSTGRES_DB", "flow_db_test"))
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db_name}"


def _ensure_list(result: dict) -> list:
    if result["status"] == 404:
        return []
    assert 200 <= result["status"] < 300, f"list failed: {result['status']}"
    return result["payload"]


def _pick_id(items: list, key: str) -> int | None:
    for item in items:
        if isinstance(item, dict) and item.get(key) is not None:
            return item[key]
    return None


@pytest.mark.api_smoke
def test_audit_fields_document_and_revision():
    suffix = uuid.uuid4().hex[:6]
    with httpx.Client(timeout=10) as client:
        areas = _ensure_list(_request(client, "GET", "/lookups/areas"))
        units = _ensure_list(_request(client, "GET", "/lookups/units"))
        projects = _ensure_list(_request(client, "GET", "/lookups/projects"))
        doc_types = _ensure_list(_request(client, "GET", "/documents/doc_types"))
        rev_codes = _ensure_list(_request(client, "GET", "/documents/revision_overview"))
        people = _ensure_list(_request(client, "GET", "/people/persons"))

        area_id = _pick_id(areas, "area_id")
        unit_id = _pick_id(units, "unit_id")
        project_id = (
            ZAML_PROJECT_ID
            if any(p.get("project_id") == ZAML_PROJECT_ID for p in projects)
            else None
        )
        type_id = _pick_id(doc_types, "type_id")
        rev_code_id = _pick_id(rev_codes, "rev_code_id")
        person_id = _pick_id(people, "person_id")

        if None in (area_id, unit_id, project_id, type_id, rev_code_id, person_id):
            pytest.skip("Missing reference data for audit field test")

        payload = {
            "doc_name_unique": f"DOC-AUD-{suffix}",
            "title": f"Audit Document {suffix}",
            "project_id": project_id,
            "type_id": type_id,
            "area_id": area_id,
            "unit_id": unit_id,
            "rev_code_id": rev_code_id,
            "rev_author_id": person_id,
            "rev_originator_id": person_id,
            "rev_modifier_id": person_id,
            "transmital_current_revision": f"TR-{suffix}",
            "planned_start_date": "2024-01-01T00:00:00Z",
            "planned_finish_date": "2024-12-31T23:59:59Z",
        }

        created = _request(
            client,
            "POST",
            "/documents",
            headers={"X-User-Id": "ZAML"},
            json=payload,
        )
        assert 200 <= created["status"] < 300, f"document create failed: {created['status']}"
        doc = created["payload"]
        assert doc.get("created_by") == 1
        assert doc.get("updated_by") == 1
        assert doc.get("created_at") is not None
        assert doc.get("updated_at") is not None

        doc_id = doc.get("doc_id")
        assert doc_id is not None

        updated = _request(
            client,
            "PUT",
            f"/documents/{doc_id}",
            headers={"X-User-Id": "FDQC"},
            json={"title": f"Audit Document Updated {suffix}"},
        )
        assert 200 <= updated["status"] < 300, f"document update failed: {updated['status']}"
        updated_doc = updated["payload"]
        assert updated_doc.get("created_by") == 1
        assert updated_doc.get("updated_by") == 2
        assert updated_doc.get("updated_at") is not None
        assert updated_doc.get("updated_at") != doc.get("updated_at")

        revisions = _request(client, "GET", f"/documents/{doc_id}/revisions")
        assert 200 <= revisions["status"] < 300
        assert revisions["payload"], "expected at least one revision"
        rev = revisions["payload"][0]
        assert rev.get("created_by") == 1
        assert rev.get("updated_by") == 1
        assert rev.get("created_at") is not None
        assert rev.get("updated_at") is not None

        rev_id = rev.get("rev_id")
        assert rev_id is not None
        rev_update = _request(
            client,
            "PUT",
            f"/documents/revisions/{rev_id}",
            headers={"X-User-Id": "ASBB"},
            json={"transmital_current_revision": f"TR-AUD-{suffix}"},
        )
        assert 200 <= rev_update["status"] < 300
        rev_out = rev_update["payload"]
        assert rev_out.get("updated_by") == 3
        assert rev_out.get("updated_at") is not None


@pytest.mark.api_smoke
def test_audit_fields_files_and_commented():
    suffix = uuid.uuid4().hex[:6]
    with httpx.Client(timeout=10) as client:
        projects = _ensure_list(_request(client, "GET", "/lookups/projects"))
        project_id = (
            ZAML_PROJECT_ID
            if any(p.get("project_id") == ZAML_PROJECT_ID for p in projects)
            else None
        )
        if project_id is None:
            pytest.skip("No projects available for files audit test")

        docs = _request(
            client,
            "GET",
            "/documents",
            headers={"X-User-Id": "ZAML"},
            params={"project_id": project_id},
        )
        if not (200 <= docs["status"] < 300) or not docs["payload"]:
            pytest.skip("No documents available for files audit test")
        doc_id = _pick_id(docs["payload"], "doc_id")
        if doc_id is None:
            pytest.skip("No doc_id available for files audit test")

        revisions = _request(
            client,
            "GET",
            f"/documents/{doc_id}/revisions",
            headers={"X-User-Id": "ZAML"},
        )
        if not (200 <= revisions["status"] < 300) or not revisions["payload"]:
            pytest.skip("No revisions available for files audit test")
        rev_id = revisions["payload"][0].get("rev_id")
        if rev_id is None:
            pytest.skip("No rev_id available for files audit test")

        file_payload = {
            "file": (f"audit-{suffix}.pdf", b"%PDF-1.4\n%AUDIT\n", "application/pdf"),
        }
        created_file = _request(
            client,
            "POST",
            "/files/",
            headers={"X-User-Id": "ZAML"},
            files=file_payload,
            data={"rev_id": str(rev_id)},
        )
        assert 200 <= created_file["status"] < 300, f"file create failed: {created_file['status']}"
        file_row = created_file["payload"]
        assert file_row.get("created_by") == 1
        assert file_row.get("updated_by") == 1
        assert file_row.get("created_at") is not None
        assert file_row.get("updated_at") is not None

        file_id = file_row.get("id") or file_row.get("file_id")
        if file_id is None:
            pytest.skip("No file_id returned for files audit test")

        commented_payload = {
            "file": (f"commented-{suffix}.pdf", b"%PDF-1.4\n%COMMENTED\n", "application/pdf"),
        }
        created_commented = _request(
            client,
            "POST",
            "/files/commented/",
            headers={"X-User-Id": "FDQC"},
            files=commented_payload,
            data={"file_id": str(file_id), "user_id": "1"},
        )
        assert (
            200 <= created_commented["status"] < 300
        ), f"commented file create failed: {created_commented['status']}"
        commented_row = created_commented["payload"]
        assert commented_row.get("created_by") == 2
        assert commented_row.get("updated_by") == 2
        assert commented_row.get("created_at") is not None
        assert commented_row.get("updated_at") is not None


@pytest.mark.api_smoke
def test_audit_fields_core_schema_contract():
    # TS-AUD-003
    db_url = _build_test_database_url()
    engine = create_engine(db_url, future=True)
    table_names_sql = ", ".join(f"'{name}'" for name in CORE_AUDIT_TABLES)

    columns_query = text(
        f"""
        SELECT
            table_name,
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'core'
          AND table_name IN ({table_names_sql})
          AND column_name IN ('created_at', 'updated_at', 'created_by', 'updated_by')
        """
    )
    fks_query = text(
        f"""
        SELECT
            kcu.table_name,
            kcu.column_name,
            ccu.table_schema AS foreign_table_schema,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
         AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
          ON ccu.constraint_name = tc.constraint_name
         AND ccu.constraint_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_schema = 'core'
          AND kcu.table_name IN ({table_names_sql})
          AND kcu.column_name IN ('created_by', 'updated_by')
        """
    )

    try:
        with engine.connect() as conn:
            column_rows = [dict(row._mapping) for row in conn.execute(columns_query)]
            fk_rows = [dict(row._mapping) for row in conn.execute(fks_query)]
    except Exception as exc:
        pytest.skip(f"Cannot introspect core schema for TS-AUD-003: {exc}")
    engine.dispose()
    if not column_rows:
        pytest.skip("No visible core schema metadata rows for TS-AUD-003")

    column_map = {
        (row["table_name"], row["column_name"]): {
            "data_type": row["data_type"],
            "is_nullable": row["is_nullable"],
            "column_default": row["column_default"] or "",
        }
        for row in column_rows
    }

    for table in CORE_AUDIT_TABLES:
        for column in ("created_at", "updated_at", "created_by", "updated_by"):
            assert (table, column) in column_map, f"missing {table}.{column}"

        created_at = column_map[(table, "created_at")]
        updated_at = column_map[(table, "updated_at")]
        created_by = column_map[(table, "created_by")]
        updated_by = column_map[(table, "updated_by")]

        assert created_at["data_type"] == "timestamp with time zone"
        assert created_at["is_nullable"] == "NO"
        assert "current_timestamp" in created_at["column_default"].lower()

        assert updated_at["data_type"] == "timestamp with time zone"
        assert updated_at["is_nullable"] == "NO"
        assert "current_timestamp" in updated_at["column_default"].lower()

        assert created_by["data_type"] == "smallint"
        assert updated_by["data_type"] == "smallint"

    fk_map = {
        (
            row["table_name"],
            row["column_name"],
            row["foreign_table_schema"],
            row["foreign_table_name"],
            row["foreign_column_name"],
        )
        for row in fk_rows
    }

    for table in CORE_AUDIT_TABLES:
        assert (table, "created_by", "ref", "users", "user_id") in fk_map
        assert (table, "updated_by", "ref", "users", "user_id") in fk_map
