"""Helper functions for model validation and conversion."""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Iterable, TypeVar

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import DBAPIError, IntegrityError

ModelT = TypeVar("ModelT", bound=BaseModel)
DbErrorMapping = tuple[str, int, str]

logger = logging.getLogger(__name__)
DEBUG_MODE = os.getenv("DEBUG", "").lower() in {"1", "true", "yes", "on", "debug"}


def _normalize_dt(value: datetime | str | None) -> datetime | None:
    """
    Normalize datetime values to timezone-aware UTC datetimes.

    Handles both datetime objects and ISO format strings. If the input has no timezone
    information, UTC is assumed.

    Args:
        value: A datetime object, ISO format string, or None.

    Returns:
        Timezone-aware datetime object in UTC, or None.

    Raises:
        HTTPException: If the datetime string format is invalid.
    """
    if value is None:
        return None
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid datetime format") from exc
        if parsed.tzinfo:
            return parsed.astimezone(timezone.utc)
        return parsed.replace(tzinfo=timezone.utc)
    if value.tzinfo:
        return value.astimezone(timezone.utc)
    return value.replace(tzinfo=timezone.utc)


def _example_for(model_cls: type[ModelT]) -> dict[str, Any]:
    schema = model_cls.model_json_schema()
    props = schema.get("properties", {}) if isinstance(schema, dict) else {}
    example: dict[str, object] = {}
    for name, prop in props.items():
        if not isinstance(prop, dict):
            continue
        if prop.get("examples"):
            example[name] = prop["examples"][0]
        elif "example" in prop:
            example[name] = prop["example"]
    if not example:
        return {}
    return {"default": {"summary": f"{model_cls.__name__} example", "value": example}}


def _model_out(model_cls: type[ModelT], obj: object) -> ModelT:
    return model_cls.model_validate(obj)


def _model_list(model_cls: type[ModelT], items: Iterable[object]) -> list[ModelT]:
    return [model_cls.model_validate(item) for item in items]


def _handle_integrity_error(detail: str, err: IntegrityError, context: str | None = None) -> None:
    ctx = f" during {context}" if context else ""
    logger.exception("IntegrityError%s: %s", ctx, err)
    # Always include error details for easier debugging
    message = f"{detail} ({err})"
    raise HTTPException(status_code=400, detail=message)


def _require_non_null_fields(payload: BaseModel, fields: Iterable[str]) -> None:
    missing = [
        field
        for field in fields
        if field in payload.model_fields_set and getattr(payload, field) is None
    ]
    if not missing:
        return
    label = "Field" if len(missing) == 1 else "Fields"
    joined = ", ".join(missing)
    raise HTTPException(status_code=400, detail=f"{label} cannot be null: {joined}")


def _raise_for_dbapi_error(
    err: DBAPIError,
    mappings: Iterable[DbErrorMapping],
    *,
    default_status: int = 500,
    default_detail: str = "Internal Server Error",
) -> None:
    message = str(err.orig) if getattr(err, "orig", None) else str(err)
    lowered = message.lower()
    for needle, status_code, detail in mappings:
        if needle in lowered:
            final_detail = detail if not DEBUG_MODE else f"{detail} ({message})"
            raise HTTPException(status_code=status_code, detail=final_detail) from err
    final_default = default_detail if not DEBUG_MODE else f"{default_detail} ({message})"
    raise HTTPException(status_code=default_status, detail=final_default) from err
