from api import main as api_main


def test_build_database_url_explicit(monkeypatch):
    monkeypatch.setenv(
        "APP_DATABASE_URL",
        "postgresql+psycopg://user:pass@host:5432/db",
    )
    assert api_main._build_database_url() == "postgresql+psycopg://user:pass@host:5432/db"


def test_build_database_url_from_parts(monkeypatch):
    monkeypatch.delenv("APP_DATABASE_URL", raising=False)
    monkeypatch.setenv("APP_DB_USER", "app_user_test")
    monkeypatch.setenv("APP_DB_PASSWORD", "app_pass_test")
    monkeypatch.setenv("POSTGRES_HOST", "db-host")
    monkeypatch.setenv("POSTGRES_PORT", "5544")
    monkeypatch.setenv("POSTGRES_DB", "flow_db_test")

    assert (
        api_main._build_database_url()
        == "postgresql+psycopg://app_user_test:app_pass_test@db-host:5544/flow_db_test"
    )
