"""Flow Backend API - Refactored main entry point."""

import inspect
import os
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute

# Import routers
from api.routers import documents, files, files_commented, lookups, notifications, people, system
from api.utils.database import _build_database_url  # noqa: F401
from api.utils.minio import _build_file_object_key, _s3_safe_segment  # noqa: F401

app = FastAPI(title="Flow Backend", version="0.1.0")

# CORS configuration
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

# Wildcard cannot be used with credentials. Disable credentials when "*" is present
# to stay spec-compliant.
allow_credentials = "*" not in allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(system.router)
app.include_router(lookups.router)
app.include_router(documents.router)
# Keep commented files routes before files to avoid /files/{file_id} matching /files/commented.
app.include_router(files_commented.router)
app.include_router(files.router)
app.include_router(notifications.router)
app.include_router(people.router)


def _sync_route_descriptions() -> None:
    """Sync docstrings to route descriptions."""
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        doc = inspect.getdoc(route.endpoint)
        if doc:
            route.description = doc


def _custom_openapi() -> dict[str, Any]:
    """Generate custom OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema

    _sync_route_descriptions()
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = _custom_openapi  # type: ignore[method-assign]
