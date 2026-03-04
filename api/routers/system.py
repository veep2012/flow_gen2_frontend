"""System endpoints (health, root)."""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from api.utils.observability import render_prometheus_text
from api.utils.responses import COMMON_RESPONSES

router = APIRouter(tags=["system"])


@router.get(
    "/",
    summary="Root endpoint returning a welcome message.",
    description="Returns a simple message indicating the Flow backend is operational.",
    operation_id="read_root",
    responses=COMMON_RESPONSES,
)
def read_root() -> dict[str, str]:
    """
    Root endpoint returning a welcome message.

    Returns a simple message indicating the Flow backend is operational.

    Returns:
        dict[str, str]: A message confirming the Flow backend is running.
    """
    return {"message": "Flow backend is running"}


@router.get(
    "/health",
    summary="Health check endpoint.",
    description="Returns the health status of the API service.",
    operation_id="health",
    responses=COMMON_RESPONSES,
)
def health() -> dict[str, str]:
    """
    Health check endpoint.

    Returns the health status of the API service.

    Returns:
        dict[str, str]: A status message indicating that the API service is healthy.
    """
    return {"status": "ok"}


@router.get(
    "/metrics",
    summary="Prometheus metrics endpoint.",
    description="Returns in-process API observability counters in Prometheus text format.",
    operation_id="metrics",
    response_class=PlainTextResponse,
    responses={
        200: {
            "description": "Prometheus metrics",
            "content": {"text/plain": {"schema": {"type": "string"}}},
        }
    },
)
def metrics() -> PlainTextResponse:
    """
    Prometheus metrics endpoint.

    Returns in-process API observability counters in Prometheus text format.
    """
    return PlainTextResponse(render_prometheus_text(), media_type="text/plain; version=0.0.4")
