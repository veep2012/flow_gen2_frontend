from api import main as api_main


def test_build_database_url_explicit(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:pass@host:5432/db",
    )
    assert api_main._build_database_url() == "postgresql+psycopg://user:pass@host:5432/db"


def test_build_database_url_from_parts(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("POSTGRES_USER", "flow_user_test")
    monkeypatch.setenv("POSTGRES_PASSWORD", "flow_pass_test")
    monkeypatch.setenv("POSTGRES_HOST", "db-host")
    monkeypatch.setenv("POSTGRES_PORT", "5544")
    monkeypatch.setenv("POSTGRES_DB", "flow_db_test")

    assert (
        api_main._build_database_url()
        == "postgresql+psycopg://flow_user_test:flow_pass_test@db-host:5544/flow_db_test"
    )
