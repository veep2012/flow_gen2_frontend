import os
import uuid
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
from sqlalchemy import create_engine, text

SCENARIO_MULTI_ROLE_UNION = "TS-AUTH-001"
SCENARIO_FAIL_CLOSED_SESSION = "TS-AUTH-002"
SCENARIO_FAIL_CLOSED_PREDICATE = "TS-AUTH-003"
SCENARIO_TRANSACTION_IDENTITY_ISOLATION = "TS-AUTH-004"
SCENARIO_UNSUPPORTED_SCOPE_FAIL_CLOSED = "TS-AUTH-005"


def _build_admin_database_url() -> str:
    explicit_admin = os.getenv("TEST_DB_ADMIN_URL")
    if explicit_admin:
        return explicit_admin

    user = os.getenv("TEST_DB_ADMIN_USER", "postgres")
    password = os.getenv("TEST_DB_ADMIN_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5433")
    db_name = os.getenv("TEST_DB_NAME", os.getenv("POSTGRES_DB", "flow_db_test"))
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db_name}"


def _build_app_user_database_url() -> str:
    explicit = os.getenv("APP_DATABASE_URL")
    if explicit:
        return os.path.expandvars(explicit)

    user = os.getenv("APP_DB_USER", "app_user")
    password = os.getenv("APP_DB_PASSWORD", "app_pass")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5433")
    db_name = os.getenv("POSTGRES_DB", "flow_db_test")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db_name}"


def _build_api_base_url() -> str:
    base = os.getenv("API_BASE", "http://localhost:4175").rstrip("/")
    prefix = os.getenv("API_PREFIX", "/api/v1").rstrip("/")
    if prefix and not prefix.startswith("/"):
        prefix = f"/{prefix}"
    return f"{base}{prefix}"


def _set_app_user_id(conn, user_id: int | None) -> None:
    value = "" if user_id is None else str(user_id)
    conn.execute(text("SELECT set_config('app.user_id', :value, true)"), {"value": value})


def _query_visible_ids(conn, *, user_id: int | None, sql_text: str, params: dict) -> list[int]:
    _set_app_user_id(conn, user_id)
    return list(conn.execute(text(sql_text), params).scalars())


def _load_two_distinct_users(conn) -> list[dict[str, int | str]]:
    rows = (
        conn.execute(
            text(
                """
                SELECT user_id, user_acronym
                FROM workflow.v_users
                WHERE user_acronym IS NOT NULL
                ORDER BY user_id
                LIMIT 2
                """
            )
        )
        .mappings()
        .all()
    )
    if len(rows) < 2:
        pytest.skip("Need at least two users for transaction identity isolation test")

    return [
        {"user_id": int(row["user_id"]), "user_acronym": str(row["user_acronym"])} for row in rows
    ]


def _prepare_rls_fixture(conn) -> dict:
    seed = (
        conn.execute(
            text(
                """
            WITH doc_pairs AS (
                SELECT
                    d1.doc_id AS doc_a,
                    d1.project_id AS project_a,
                    d2.doc_id AS doc_b,
                    d2.project_id AS project_b
                FROM core.doc d1
                JOIN core.doc d2 ON d2.project_id <> d1.project_id
                WHERE d1.voided IS FALSE
                  AND d2.voided IS FALSE
                LIMIT 1
            )
            SELECT
                p.doc_a,
                p.project_a,
                p.doc_b,
                p.project_b,
                (
                    SELECT r.rev_id
                    FROM core.doc_revision r
                    WHERE r.doc_id = p.doc_a
                    ORDER BY r.rev_id
                    LIMIT 1
                ) AS rev_a,
                (
                    SELECT r.rev_id
                    FROM core.doc_revision r
                    WHERE r.doc_id = p.doc_b
                    ORDER BY r.rev_id
                    LIMIT 1
                ) AS rev_b,
                (
                    SELECT p.duty_id
                    FROM ref.person p
                    ORDER BY p.person_id
                    LIMIT 1
                ) AS duty_id
            FROM doc_pairs p
            """
            )
        )
        .mappings()
        .one_or_none()
    )
    if not seed:
        pytest.skip("No pair of documents from distinct projects found for RLS authorization test")
    if seed["rev_a"] is None or seed["rev_b"] is None:
        pytest.skip("Expected revisions for selected documents were not found")
    if seed["duty_id"] is None:
        pytest.skip("No person duty found for RLS authorization test")

    marker = uuid.uuid4().hex[:10]
    role_name_a = f"TS_RLS_{marker}_A"
    role_name_b = f"TS_RLS_{marker}_B"
    role_code_a = f"TS_RLS_{marker}_A"
    role_code_b = f"TS_RLS_{marker}_B"

    role_a = conn.execute(
        text(
            """
            INSERT INTO ref.roles (role_name, role_code, external_name, is_super)
            VALUES (:role_name, :role_code, :external_name, FALSE)
            RETURNING role_id
            """
        ),
        {
            "role_name": role_name_a,
            "role_code": role_code_a,
            "external_name": f"TS_EXT_{marker}_A",
        },
    ).scalar_one()
    role_b = conn.execute(
        text(
            """
            INSERT INTO ref.roles (role_name, role_code, external_name, is_super)
            VALUES (:role_name, :role_code, :external_name, FALSE)
            RETURNING role_id
            """
        ),
        {
            "role_name": role_name_b,
            "role_code": role_code_b,
            "external_name": f"TS_EXT_{marker}_B",
        },
    ).scalar_one()

    temp_person_id = conn.execute(
        text(
            """
            INSERT INTO ref.person (person_name, duty_id)
            VALUES (:person_name, :duty_id)
            RETURNING person_id
            """
        ),
        {"person_name": f"TS RLS {marker}", "duty_id": seed["duty_id"]},
    ).scalar_one()

    temp_user_id = conn.execute(
        text(
            """
            INSERT INTO ref.users (person_id, user_acronym, role_id)
            VALUES (:person_id, :user_acronym, :role_id)
            RETURNING user_id
            """
        ),
        {
            "person_id": temp_person_id,
            "user_acronym": f"TSR{marker[:7]}",
            "role_id": 4,
        },
    ).scalar_one()

    # The insert sets ref.users.role_id=4 to satisfy the FK/default seeded shape.
    # Then we intentionally clear ref.user_roles so this fixture is driven only by
    # the two test-specific roles added below.
    conn.execute(
        text("DELETE FROM ref.user_roles WHERE user_id = :user_id"), {"user_id": temp_user_id}
    )

    for role_id in (role_a, role_b):
        conn.execute(
            text(
                """
                INSERT INTO ref.role_permissions (role_id, resource, capability)
                VALUES
                    (:role_id, 'doc', 'read-only'),
                    (:role_id, 'doc_revision', 'read-only'),
                    (:role_id, 'files', 'read-only'),
                    (:role_id, 'files_commented', 'read-only')
                """
            ),
            {"role_id": role_id},
        )

    conn.execute(
        text(
            """
            INSERT INTO ref.role_scopes (role_id, scope_type, entity_id, logic_group)
            VALUES
                (:role_a, 'PROJECT', :project_a, 1),
                (:role_b, 'PROJECT', :project_b, 1)
            """
        ),
        {
            "role_a": role_a,
            "project_a": seed["project_a"],
            "role_b": role_b,
            "project_b": seed["project_b"],
        },
    )
    conn.execute(
        text(
            """
            INSERT INTO ref.user_roles (user_id, role_id)
            VALUES (:user_id, :role_id)
            ON CONFLICT DO NOTHING
            """
        ),
        {"user_id": temp_user_id, "role_id": role_a},
    )
    conn.execute(
        text(
            """
            INSERT INTO ref.user_roles (user_id, role_id)
            VALUES (:user_id, :role_id)
            ON CONFLICT DO NOTHING
            """
        ),
        {"user_id": temp_user_id, "role_id": role_b},
    )

    file_a = conn.execute(
        text(
            """
            INSERT INTO core.files (rev_id, filename, s3_uid, mimetype, created_by, updated_by)
            VALUES (:rev_id, :filename, :s3_uid, 'application/pdf', :user_id, :user_id)
            RETURNING id
            """
        ),
        {
            "rev_id": seed["rev_a"],
            "filename": f"ts-rls-{marker}-a.pdf",
            "s3_uid": f"rls/{marker}/a.pdf",
            "user_id": temp_user_id,
        },
    ).scalar_one()
    file_b = conn.execute(
        text(
            """
            INSERT INTO core.files (rev_id, filename, s3_uid, mimetype, created_by, updated_by)
            VALUES (:rev_id, :filename, :s3_uid, 'application/pdf', :user_id, :user_id)
            RETURNING id
            """
        ),
        {
            "rev_id": seed["rev_b"],
            "filename": f"ts-rls-{marker}-b.pdf",
            "s3_uid": f"rls/{marker}/b.pdf",
            "user_id": temp_user_id,
        },
    ).scalar_one()
    commented_a = conn.execute(
        text(
            """
            INSERT INTO core.files_commented (
                file_id, user_id, s3_uid, mimetype, created_by, updated_by
            )
            VALUES (:file_id, :user_id, :s3_uid, 'application/pdf', :user_id, :user_id)
            RETURNING id
            """
        ),
        {
            "file_id": file_a,
            "user_id": temp_user_id,
            "s3_uid": f"rls/{marker}/a-commented.pdf",
        },
    ).scalar_one()
    commented_b = conn.execute(
        text(
            """
            INSERT INTO core.files_commented (
                file_id, user_id, s3_uid, mimetype, created_by, updated_by
            )
            VALUES (:file_id, :user_id, :s3_uid, 'application/pdf', :user_id, :user_id)
            RETURNING id
            """
        ),
        {
            "file_id": file_b,
            "user_id": temp_user_id,
            "s3_uid": f"rls/{marker}/b-commented.pdf",
        },
    ).scalar_one()

    return {
        "user_id": int(temp_user_id),
        "doc_a": int(seed["doc_a"]),
        "doc_b": int(seed["doc_b"]),
        "project_a": int(seed["project_a"]),
        "project_b": int(seed["project_b"]),
        "rev_a": int(seed["rev_a"]),
        "rev_b": int(seed["rev_b"]),
        "file_a": int(file_a),
        "file_b": int(file_b),
        "commented_a": int(commented_a),
        "commented_b": int(commented_b),
        "role_a": int(role_a),
        "role_b": int(role_b),
        "temp_person_id": int(temp_person_id),
    }


def _prepare_unsupported_scope_fixture(conn, scope_type: str) -> dict:
    if scope_type not in {"AREA", "UNIT"}:
        raise ValueError(f"Unsupported scope_type for fixture: {scope_type}")

    entity_column = "area_id" if scope_type == "AREA" else "unit_id"
    seed = (
        conn.execute(
            text(
                f"""
                SELECT
                    d.doc_id,
                    d.{entity_column} AS entity_id,
                    (
                        SELECT p.duty_id
                        FROM ref.person p
                        ORDER BY p.person_id
                        LIMIT 1
                    ) AS duty_id
                FROM core.doc d
                WHERE d.voided IS FALSE
                  AND d.{entity_column} IS NOT NULL
                ORDER BY d.doc_id
                LIMIT 1
                """
            )
        )
        .mappings()
        .one_or_none()
    )
    if not seed:
        pytest.skip(f"No document with non-null {entity_column} found for unsupported scope test")
    if seed["duty_id"] is None:
        pytest.skip("No person duty found for unsupported scope test")

    marker = uuid.uuid4().hex[:10]
    role_id = conn.execute(
        text(
            """
            INSERT INTO ref.roles (role_name, role_code, external_name, is_super)
            VALUES (:role_name, :role_code, :external_name, FALSE)
            RETURNING role_id
            """
        ),
        {
            "role_name": f"TS_UNSUPPORTED_{scope_type}_{marker}",
            "role_code": f"TS_UNSUPPORTED_{scope_type}_{marker}",
            "external_name": f"TS_UNSUPPORTED_EXT_{scope_type}_{marker}",
        },
    ).scalar_one()
    temp_person_id = conn.execute(
        text(
            """
            INSERT INTO ref.person (person_name, duty_id)
            VALUES (:person_name, :duty_id)
            RETURNING person_id
            """
        ),
        {"person_name": f"TS Unsupported {scope_type} {marker}", "duty_id": seed["duty_id"]},
    ).scalar_one()
    temp_user_id = conn.execute(
        text(
            """
            INSERT INTO ref.users (person_id, user_acronym, role_id)
            VALUES (:person_id, :user_acronym, :role_id)
            RETURNING user_id
            """
        ),
        {
            "person_id": temp_person_id,
            "user_acronym": f"TSU{marker[:7]}",
            "role_id": 4,
        },
    ).scalar_one()

    conn.execute(
        text("DELETE FROM ref.user_roles WHERE user_id = :user_id"), {"user_id": temp_user_id}
    )
    conn.execute(
        text(
            """
            INSERT INTO ref.role_permissions (role_id, resource, capability)
            VALUES (:role_id, 'doc', 'read-only')
            """
        ),
        {"role_id": role_id},
    )
    conn.execute(
        text(
            """
            INSERT INTO ref.role_scopes (role_id, scope_type, entity_id, logic_group)
            VALUES (:role_id, :scope_type, :entity_id, 1)
            """
        ),
        {
            "role_id": role_id,
            "scope_type": scope_type,
            "entity_id": seed["entity_id"],
        },
    )
    conn.execute(
        text(
            """
            INSERT INTO ref.user_roles (user_id, role_id)
            VALUES (:user_id, :role_id)
            ON CONFLICT DO NOTHING
            """
        ),
        {"user_id": temp_user_id, "role_id": role_id},
    )

    return {
        "user_id": int(temp_user_id),
        "doc_id": int(seed["doc_id"]),
        "role_id": int(role_id),
        "temp_person_id": int(temp_person_id),
    }


def _cleanup_rls_fixture(conn, fixture: dict) -> None:
    conn.execute(
        text(
            """
            DELETE FROM core.files_commented
            WHERE id = :commented_a OR id = :commented_b
            """
        ),
        {
            "commented_a": fixture["commented_a"],
            "commented_b": fixture["commented_b"],
        },
    )
    conn.execute(
        text(
            """
            DELETE FROM core.files
            WHERE id = :file_a OR id = :file_b
            """
        ),
        {
            "file_a": fixture["file_a"],
            "file_b": fixture["file_b"],
        },
    )
    conn.execute(
        text(
            """
            DELETE FROM ref.user_roles
            WHERE user_id = :user_id
              AND (role_id = :role_a OR role_id = :role_b)
            """
        ),
        {
            "user_id": fixture["user_id"],
            "role_a": fixture["role_a"],
            "role_b": fixture["role_b"],
        },
    )
    conn.execute(
        text(
            """
            DELETE FROM ref.role_scopes
            WHERE role_id = :role_a OR role_id = :role_b
            """
        ),
        {"role_a": fixture["role_a"], "role_b": fixture["role_b"]},
    )
    conn.execute(
        text(
            """
            DELETE FROM ref.role_permissions
            WHERE role_id = :role_a OR role_id = :role_b
            """
        ),
        {"role_a": fixture["role_a"], "role_b": fixture["role_b"]},
    )
    conn.execute(
        text(
            """
            DELETE FROM ref.roles
            WHERE role_id = :role_a OR role_id = :role_b
            """
        ),
        {"role_a": fixture["role_a"], "role_b": fixture["role_b"]},
    )
    conn.execute(
        text("DELETE FROM ref.users WHERE user_id = :user_id"), {"user_id": fixture["user_id"]}
    )
    conn.execute(
        text("DELETE FROM ref.person WHERE person_id = :person_id"),
        {"person_id": fixture["temp_person_id"]},
    )


def _cleanup_unsupported_scope_fixture(conn, fixture: dict) -> None:
    conn.execute(
        text(
            """
            DELETE FROM ref.user_roles
            WHERE user_id = :user_id
              AND role_id = :role_id
            """
        ),
        {
            "user_id": fixture["user_id"],
            "role_id": fixture["role_id"],
        },
    )
    conn.execute(
        text("DELETE FROM ref.role_scopes WHERE role_id = :role_id"),
        {"role_id": fixture["role_id"]},
    )
    conn.execute(
        text("DELETE FROM ref.role_permissions WHERE role_id = :role_id"),
        {"role_id": fixture["role_id"]},
    )
    conn.execute(
        text("DELETE FROM ref.roles WHERE role_id = :role_id"), {"role_id": fixture["role_id"]}
    )
    conn.execute(
        text("DELETE FROM ref.users WHERE user_id = :user_id"), {"user_id": fixture["user_id"]}
    )
    conn.execute(
        text("DELETE FROM ref.person WHERE person_id = :person_id"),
        {"person_id": fixture["temp_person_id"]},
    )


@pytest.mark.api_smoke
def test_read_rls_multi_role_scope_union():
    admin_engine = create_engine(_build_admin_database_url(), future=True)
    app_engine = create_engine(_build_app_user_database_url(), future=True)
    fixture = None
    try:
        with admin_engine.begin() as admin_conn:
            fixture = _prepare_rls_fixture(admin_conn)

        with app_engine.connect() as app_conn:
            visible_docs = _query_visible_ids(
                app_conn,
                user_id=fixture["user_id"],
                sql_text="""
                    SELECT doc_id
                    FROM workflow.v_documents
                    WHERE doc_id IN (:doc_a, :doc_b)
                    ORDER BY doc_id
                """,
                params={"doc_a": fixture["doc_a"], "doc_b": fixture["doc_b"]},
            )
            assert visible_docs == sorted(
                [fixture["doc_a"], fixture["doc_b"]]
            ), f"{SCENARIO_MULTI_ROLE_UNION} expected both docs to be visible"

            visible_projects = _query_visible_ids(
                app_conn,
                user_id=fixture["user_id"],
                sql_text="""
                    SELECT project_id
                    FROM workflow.v_projects
                    WHERE project_id IN (:project_a, :project_b)
                    ORDER BY project_id
                """,
                params={
                    "project_a": fixture["project_a"],
                    "project_b": fixture["project_b"],
                },
            )
            assert (
                len(visible_projects) == 2
            ), f"{SCENARIO_MULTI_ROLE_UNION} expected lookup projects to be scope-filtered"

            visible_areas = _query_visible_ids(
                app_conn,
                user_id=fixture["user_id"],
                sql_text="""
                    SELECT area_id
                    FROM workflow.v_areas
                    WHERE area_id IN (
                        (SELECT area_id FROM workflow.v_documents WHERE doc_id = :doc_a),
                        (SELECT area_id FROM workflow.v_documents WHERE doc_id = :doc_b)
                    )
                    ORDER BY area_id
                """,
                params={"doc_a": fixture["doc_a"], "doc_b": fixture["doc_b"]},
            )
            expected_areas = _query_visible_ids(
                app_conn,
                user_id=fixture["user_id"],
                sql_text="""
                    SELECT DISTINCT area_id
                    FROM workflow.v_documents
                    WHERE doc_id IN (:doc_a, :doc_b)
                    ORDER BY area_id
                """,
                params={"doc_a": fixture["doc_a"], "doc_b": fixture["doc_b"]},
            )
            assert visible_areas == expected_areas, (
                f"{SCENARIO_MULTI_ROLE_UNION} expected areas to be "
                "unfiltered in project-only scope mode"
            )

            visible_units = _query_visible_ids(
                app_conn,
                user_id=fixture["user_id"],
                sql_text="""
                    SELECT unit_id
                    FROM workflow.v_units
                    WHERE unit_id IN (
                        (SELECT unit_id FROM workflow.v_documents WHERE doc_id = :doc_a),
                        (SELECT unit_id FROM workflow.v_documents WHERE doc_id = :doc_b)
                    )
                    ORDER BY unit_id
                """,
                params={"doc_a": fixture["doc_a"], "doc_b": fixture["doc_b"]},
            )
            expected_units = _query_visible_ids(
                app_conn,
                user_id=fixture["user_id"],
                sql_text="""
                    SELECT DISTINCT unit_id
                    FROM workflow.v_documents
                    WHERE doc_id IN (:doc_a, :doc_b)
                    ORDER BY unit_id
                """,
                params={"doc_a": fixture["doc_a"], "doc_b": fixture["doc_b"]},
            )
            assert visible_units == expected_units, (
                f"{SCENARIO_MULTI_ROLE_UNION} expected units to be "
                "unfiltered in project-only scope mode"
            )

            visible_revisions = _query_visible_ids(
                app_conn,
                user_id=fixture["user_id"],
                sql_text="""
                    SELECT rev_id
                    FROM workflow.v_document_revisions
                    WHERE rev_id IN (:rev_a, :rev_b)
                    ORDER BY rev_id
                """,
                params={"rev_a": fixture["rev_a"], "rev_b": fixture["rev_b"]},
            )
            assert visible_revisions == sorted(
                [fixture["rev_a"], fixture["rev_b"]]
            ), f"{SCENARIO_MULTI_ROLE_UNION} expected inherited revision visibility"

            visible_files = _query_visible_ids(
                app_conn,
                user_id=fixture["user_id"],
                sql_text="""
                    SELECT id
                    FROM workflow.v_files
                    WHERE id IN (:file_a, :file_b)
                    ORDER BY id
                """,
                params={"file_a": fixture["file_a"], "file_b": fixture["file_b"]},
            )
            assert visible_files == sorted(
                [fixture["file_a"], fixture["file_b"]]
            ), f"{SCENARIO_MULTI_ROLE_UNION} expected inherited file visibility"

            visible_commented = _query_visible_ids(
                app_conn,
                user_id=fixture["user_id"],
                sql_text="""
                    SELECT id
                    FROM workflow.v_files_commented
                    WHERE id IN (:commented_a, :commented_b)
                    ORDER BY id
                """,
                params={
                    "commented_a": fixture["commented_a"],
                    "commented_b": fixture["commented_b"],
                },
            )
            assert visible_commented == sorted(
                [fixture["commented_a"], fixture["commented_b"]]
            ), f"{SCENARIO_MULTI_ROLE_UNION} expected inherited commented-file visibility"
    finally:
        if fixture is not None:
            with admin_engine.begin() as admin_conn:
                _cleanup_rls_fixture(admin_conn, fixture)
        admin_engine.dispose()
        app_engine.dispose()


@pytest.mark.api_smoke
def test_read_rls_fail_closed_for_missing_or_unknown_session_user():
    admin_engine = create_engine(_build_admin_database_url(), future=True)
    app_engine = create_engine(_build_app_user_database_url(), future=True)
    fixture = None
    try:
        with admin_engine.begin() as admin_conn:
            fixture = _prepare_rls_fixture(admin_conn)

        with app_engine.connect() as app_conn:
            no_session_docs = _query_visible_ids(
                app_conn,
                user_id=None,
                sql_text="""
                    SELECT doc_id
                    FROM workflow.v_documents
                    WHERE doc_id IN (:doc_a, :doc_b)
                    ORDER BY doc_id
                """,
                params={"doc_a": fixture["doc_a"], "doc_b": fixture["doc_b"]},
            )
            assert (
                no_session_docs == []
            ), f"{SCENARIO_FAIL_CLOSED_SESSION} expected empty result for missing app.user_id"

            unknown_user_docs = _query_visible_ids(
                app_conn,
                user_id=999999,
                sql_text="""
                    SELECT doc_id
                    FROM workflow.v_documents
                    WHERE doc_id IN (:doc_a, :doc_b)
                    ORDER BY doc_id
                """,
                params={"doc_a": fixture["doc_a"], "doc_b": fixture["doc_b"]},
            )
            assert (
                unknown_user_docs == []
            ), f"{SCENARIO_FAIL_CLOSED_SESSION} expected empty result for unknown app.user_id"
    finally:
        if fixture is not None:
            with admin_engine.begin() as admin_conn:
                _cleanup_rls_fixture(admin_conn, fixture)
        admin_engine.dispose()
        app_engine.dispose()


@pytest.mark.api_smoke
def test_check_user_permission_fail_closed_inputs():
    admin_engine = create_engine(_build_admin_database_url(), future=True)
    app_engine = create_engine(_build_app_user_database_url(), future=True)
    try:
        with admin_engine.connect() as admin_conn:
            sample = (
                admin_conn.execute(
                    text(
                        """
                    SELECT
                        (
                            SELECT u.user_id
                            FROM ref.users u
                            ORDER BY u.user_id
                            LIMIT 1
                        ) AS user_id,
                        (
                            SELECT d.doc_id
                            FROM core.doc d
                            WHERE d.voided IS FALSE
                            ORDER BY d.doc_id
                            LIMIT 1
                        ) AS doc_id
                    """
                    )
                )
                .mappings()
                .one()
            )
            if sample["user_id"] is None or sample["doc_id"] is None:
                pytest.skip("Missing user/doc seed data for permission predicate test")

        with app_engine.connect() as app_conn:
            invalid_capability = app_conn.execute(
                text(
                    """
                    SELECT workflow.check_user_permission(
                        :user_id,
                        'doc',
                        'invalid-capability',
                        :doc_id
                    )
                    """
                ),
                {"user_id": sample["user_id"], "doc_id": sample["doc_id"]},
            ).scalar_one()
            assert (
                invalid_capability is False
            ), f"{SCENARIO_FAIL_CLOSED_PREDICATE} invalid capability must fail closed"

            invalid_resource = app_conn.execute(
                text(
                    """
                    SELECT workflow.check_user_permission(
                        :user_id,
                        'invalid_resource',
                        'read-only',
                        :doc_id
                    )
                    """
                ),
                {"user_id": sample["user_id"], "doc_id": sample["doc_id"]},
            ).scalar_one()
            assert (
                invalid_resource is False
            ), f"{SCENARIO_FAIL_CLOSED_PREDICATE} invalid resource must fail closed"

            missing_doc = app_conn.execute(
                text(
                    """
                    SELECT workflow.check_user_permission(
                        :user_id,
                        'doc',
                        'read-only',
                        999999999
                    )
                    """
                ),
                {"user_id": sample["user_id"]},
            ).scalar_one()
            assert (
                missing_doc is False
            ), f"{SCENARIO_FAIL_CLOSED_PREDICATE} unresolved document must fail closed"

            unknown_user = app_conn.execute(
                text(
                    """
                    SELECT workflow.check_user_permission(
                        999999,
                        'doc',
                        'read-only',
                        :doc_id
                    )
                    """
                ),
                {"doc_id": sample["doc_id"]},
            ).scalar_one()
            assert (
                unknown_user is False
            ), f"{SCENARIO_FAIL_CLOSED_PREDICATE} unknown user must fail closed"
    finally:
        admin_engine.dispose()
        app_engine.dispose()


@pytest.mark.api_smoke
@pytest.mark.parametrize("scope_type", ["AREA", "UNIT"])
def test_read_rls_rejects_unsupported_scope_types(scope_type: str):
    admin_engine = create_engine(_build_admin_database_url(), future=True)
    app_engine = create_engine(_build_app_user_database_url(), future=True)
    fixture = None
    try:
        with admin_engine.begin() as admin_conn:
            fixture = _prepare_unsupported_scope_fixture(admin_conn, scope_type)

        with app_engine.connect() as app_conn:
            visible_docs = _query_visible_ids(
                app_conn,
                user_id=fixture["user_id"],
                sql_text="""
                    SELECT doc_id
                    FROM workflow.v_documents
                    WHERE doc_id = :doc_id
                """,
                params={"doc_id": fixture["doc_id"]},
            )
            assert visible_docs == [], (
                f"{SCENARIO_UNSUPPORTED_SCOPE_FAIL_CLOSED} expected no visibility for "
                f"unsupported {scope_type} scope assignments"
            )
    finally:
        if fixture is not None:
            with admin_engine.begin() as admin_conn:
                _cleanup_unsupported_scope_fixture(admin_conn, fixture)
        admin_engine.dispose()
        app_engine.dispose()


@pytest.mark.api_smoke
def test_current_user_identity_does_not_leak_across_rapid_requests():
    admin_engine = create_engine(_build_admin_database_url(), future=True)
    try:
        with admin_engine.connect() as admin_conn:
            users = _load_two_distinct_users(admin_conn)

        request_plan = [users[index % 2] for index in range(40)]
        url = f"{_build_api_base_url()}/people/users/current_user"

        def _fetch_current_user(
            expected_user: dict[str, int | str]
        ) -> tuple[dict[str, int | str], int, dict]:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    url,
                    headers={"X-User-Id": str(expected_user["user_acronym"])},
                )
            return expected_user, response.status_code, response.json()

        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(_fetch_current_user, request_plan))

        for expected_user, status_code, payload in results:
            assert status_code == 200, (
                f"{SCENARIO_TRANSACTION_IDENTITY_ISOLATION} expected 200 for "
                f"{expected_user['user_acronym']}"
            )
            assert payload["user_id"] == expected_user["user_id"], (
                f"{SCENARIO_TRANSACTION_IDENTITY_ISOLATION} expected user_id "
                f"{expected_user['user_id']} but got {payload['user_id']}"
            )
            assert payload["user_acronym"] == expected_user["user_acronym"], (
                f"{SCENARIO_TRANSACTION_IDENTITY_ISOLATION} expected acronym "
                f"{expected_user['user_acronym']} but got {payload['user_acronym']}"
            )
    finally:
        admin_engine.dispose()
