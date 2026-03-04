"""Flow Backend API - Refactored main entry point."""

import inspect
import os
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute

# Import routers
from api.routers import (
    distribution_lists,
    documents,
    files,
    files_commented,
    lookups,
    notifications,
    people,
    system,
    written_comments,
)
from api.utils.database import (
    REQUEST_ID_HEADER,
    _build_database_url,  # noqa: F401
    get_auth_mode,
    get_endpoint_label,
    validate_startup_app_user_mode,
)
from api.utils.minio import _build_file_object_key, _s3_safe_segment  # noqa: F401
from api.utils.observability import increment_counter


@asynccontextmanager
async def _app_lifespan(_: FastAPI):
    validate_startup_app_user_mode()
    yield


app = FastAPI(title="Flow Backend", version="0.1.0", lifespan=_app_lifespan)

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


@app.middleware("http")
async def attach_request_id(request: Request, call_next):
    request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
    request.state.request_id = request_id
    request.state.auth_mode = "unknown"
    request.state.auth_identity_present = False
    response = await call_next(request)
    is_current_user_unresolved = (
        response.status_code == 404 and request.url.path == "/api/v1/people/users/current_user"
    )
    is_authenticated_forbidden = response.status_code == 403 and bool(
        getattr(request.state, "auth_identity_present", False)
    )
    if is_current_user_unresolved or is_authenticated_forbidden:
        increment_counter(
            "flow_auth_denied_by_rls_total",
            endpoint=get_endpoint_label(request),
            status_code=str(response.status_code),
            auth_mode=get_auth_mode(request),
        )
    response.headers[REQUEST_ID_HEADER] = request_id
    return response


# Register routers
app.include_router(system.router)
app.include_router(lookups.router)
app.include_router(documents.router)
# Keep commented files routes before files to avoid /files/{file_id} matching /files/commented.
app.include_router(files_commented.router)
app.include_router(written_comments.router)
app.include_router(files.router)
app.include_router(notifications.router)
app.include_router(distribution_lists.router)
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
