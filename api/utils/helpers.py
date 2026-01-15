"""Helper functions for model validation and conversion."""

import logging
import os
from datetime import datetime
from typing import Any, Iterable, TypeVar

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

ModelT = TypeVar("ModelT", bound=BaseModel)

logger = logging.getLogger(__name__)
DEBUG_MODE = os.getenv("DEBUG", "").lower() in {"1", "true", "yes", "on", "debug"}


def _normalize_dt(value: datetime | str | None) -> datetime | None:
    """
    Normalize datetime values to timezone-naive datetime objects.

    Handles both datetime objects and ISO format strings. If the input has timezone
    information, it is removed (converted to naive datetime).

    Args:
        value: A datetime object, ISO format string, or None.

    Returns:
        Timezone-naive datetime object or None.

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
        return parsed.replace(tzinfo=None) if parsed.tzinfo else parsed
    return value.replace(tzinfo=None) if value.tzinfo else value


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
    message = detail if not DEBUG_MODE else f"{detail} ({err})"
    raise HTTPException(status_code=400, detail=message)
