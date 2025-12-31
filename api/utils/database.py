"""Database configuration and session management."""

import os
from typing import Iterable

from sqlalchemy import create_engine
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


def get_db() -> Iterable[Session]:
    """Dependency for getting database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
