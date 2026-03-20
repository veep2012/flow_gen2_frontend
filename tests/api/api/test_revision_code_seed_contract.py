import json
import os
import subprocess
import uuid
from pathlib import Path

from sqlalchemy import create_engine, text

REPO_ROOT = Path(__file__).resolve().parents[3]
FLOW_INIT = REPO_ROOT / "ci" / "init" / "flow_init.psql"
FLOW_SEED = REPO_ROOT / "ci" / "init" / "flow_seed.sql"

EXPECTED_REVISION_CODES = [
    (1, "IDC", "B", 2, False, False),
    (2, "IFRC", "C", 3, False, False),
    (3, "AFD", "D", 4, False, False),
    (4, "AFC", "E", 5, False, False),
    (5, "AS-BUILT", "Z", None, True, False),
    (6, "INDESIGN", "A", 1, False, True),
]


def _admin_params() -> dict[str, str]:
    return {
        "user": os.getenv("TEST_DB_ADMIN_USER", "postgres"),
        "password": os.getenv("TEST_DB_ADMIN_PASSWORD", "postgres"),
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": os.getenv("POSTGRES_PORT", "5433"),
        "postgres_db": os.getenv("TEST_DB_ADMIN_MAINT_DB", "postgres"),
    }


def _database_url(db_name: str) -> str:
    params = _admin_params()
    return (
        f"postgresql+psycopg://{params['user']}:{params['password']}"
        f"@{params['host']}:{params['port']}/{db_name}"
    )


def _run_psql(db_name: str, script: Path) -> None:
    params = _admin_params()
    env = os.environ.copy()
    env["PGPASSWORD"] = params["password"]
    subprocess.run(
        [
            "psql",
            "-v",
            "ON_ERROR_STOP=1",
            "-h",
            params["host"],
            "-p",
            params["port"],
            "-U",
            params["user"],
            "-d",
            db_name,
            "-f",
            str(script),
        ],
        cwd=REPO_ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def _recreate_database(db_name: str) -> None:
    admin_engine = create_engine(_database_url(_admin_params()["postgres_db"]))
    try:
        with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.exec_driver_sql(f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)')
            conn.exec_driver_sql(f'CREATE DATABASE "{db_name}"')
    finally:
        admin_engine.dispose()


def _drop_database(db_name: str) -> None:
    admin_engine = create_engine(_database_url(_admin_params()["postgres_db"]))
    try:
        with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.exec_driver_sql(f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)')
    finally:
        admin_engine.dispose()


def _assert_revision_overview_shape_and_fk(engine) -> None:
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT
                    rev_code_id,
                    rev_code_name,
                    rev_code_acronym,
                    next_rev_code_id,
                    final,
                    start
                FROM ref.revision_overview
                ORDER BY rev_code_id
                """
            )
        ).all()
        assert rows == EXPECTED_REVISION_CODES

        next_id = conn.execute(
            text(
                """
                SELECT nextval(pg_get_serial_sequence('ref.revision_overview', 'rev_code_id'))
                """
            )
        ).scalar_one()
        assert next_id > EXPECTED_REVISION_CODES[-1][0]

        missing_fk_refs = conn.execute(
            text(
                """
                SELECT COUNT(*)
                FROM core.doc_revision AS r
                LEFT JOIN ref.revision_overview AS ro
                  ON ro.rev_code_id = r.rev_code_id
                WHERE ro.rev_code_id IS NULL
                """
            )
        ).scalar_one()
        assert missing_fk_refs == 0


def _assert_revision_overview_write_paths(engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("SELECT set_config('app.user', '1', true)"))
        created = (
            conn.execute(
                text(
                    """
                SELECT doc_id, rev_id
                FROM workflow.create_document(
                    :doc_name_unique,
                    :title,
                    :project_id,
                    :jobpack_id,
                    :type_id,
                    :area_id,
                    :unit_id,
                    :rev_code_id,
                    :rev_author_id,
                    :rev_originator_id,
                    :rev_modifier_id,
                    :transmital_current_revision,
                    :milestone_id,
                    :planned_start_date,
                    :planned_finish_date,
                    NULL,
                    NULL,
                    NULL,
                    FALSE
                )
                """
                ),
                {
                    "doc_name_unique": f"SEED-CHECK-{uuid.uuid4().hex[:8].upper()}",
                    "title": "Seed contract check",
                    "project_id": 1,
                    "jobpack_id": 1,
                    "type_id": 1,
                    "area_id": 1,
                    "unit_id": 1,
                    "rev_code_id": 6,
                    "rev_author_id": 1,
                    "rev_originator_id": 1,
                    "rev_modifier_id": 1,
                    "transmital_current_revision": "TR-SEED-CHECK",
                    "milestone_id": 1,
                    "planned_start_date": "2024-01-01T00:00:00Z",
                    "planned_finish_date": "2024-01-05T00:00:00Z",
                },
            )
            .mappings()
            .one()
        )

        created_rev_code_id = conn.execute(
            text("SELECT rev_code_id FROM core.doc_revision WHERE rev_id = :rev_id"),
            {"rev_id": created["rev_id"]},
        ).scalar_one()
        assert created_rev_code_id == 6

        conn.execute(
            text("SELECT * FROM workflow.update_revision(:rev_id, CAST(:patch AS jsonb))"),
            {"rev_id": created["rev_id"], "patch": json.dumps({"rev_code_id": 1})},
        )
        updated_rev_code_id = conn.execute(
            text("SELECT rev_code_id FROM core.doc_revision WHERE rev_id = :rev_id"),
            {"rev_id": created["rev_id"]},
        ).scalar_one()
        assert updated_rev_code_id == 1


def _assert_seed_contract(engine) -> None:
    _assert_revision_overview_shape_and_fk(engine)
    _assert_revision_overview_write_paths(engine)


def test_revision_code_seed_bootstrap_is_repeatable_and_preserves_identity():
    db_name = f"flow_seed_contract_{uuid.uuid4().hex[:8]}"
    try:
        _recreate_database(db_name)

        _run_psql(db_name, FLOW_INIT)
        _run_psql(db_name, FLOW_SEED)
        engine = create_engine(_database_url(db_name))
        try:
            _assert_seed_contract(engine)
        finally:
            engine.dispose()

        _run_psql(db_name, FLOW_INIT)
        _run_psql(db_name, FLOW_SEED)
        engine = create_engine(_database_url(db_name))
        try:
            _assert_seed_contract(engine)
        finally:
            engine.dispose()
    finally:
        _drop_database(db_name)
