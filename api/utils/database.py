"""Database configuration and session management."""

import os
from typing import Iterable

from fastapi import HTTPException, Request
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker


def _build_database_url() -> str:
    explicit = os.getenv("DATABASE_URL")
    if explicit:
        return os.path.expandvars(explicit)

    user = os.getenv("POSTGRES_USER", "flow_user")
    password = os.getenv("POSTGRES_PASSWORD", "flow_pass")
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "flow_db")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db_name}"


DATABASE_URL = _build_database_url()

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def _set_app_user(db: Session, request: Request) -> None:
    header_value = request.headers.get("X-User-Id")
    if header_value is None:
        user_value = os.getenv("DEFAULT_APP_USER", "")
    else:
        user_value = header_value.strip()
        if user_value:
            try:
                int(user_value)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Invalid X-User-Id header") from exc
    if user_value:
        db.execute(
            text("SELECT set_config('app.user', :user_id, true)"),
            {"user_id": user_value},
        )
    else:
        db.execute(text("SELECT set_config('app.user', '', true)"))


def get_db(request: Request) -> Iterable[Session]:
    """Dependency for getting database sessions."""
    db = SessionLocal()
    try:
        _set_app_user(db, request)
        yield db
    finally:
        db.close()
