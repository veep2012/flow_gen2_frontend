"""Notifications endpoints for create/list/replace/delete/read flows."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from api.schemas.notifications import (
    NotificationActionResult,
    NotificationCreate,
    NotificationDelete,
    NotificationMarkRead,
    NotificationOut,
    NotificationRecipientStateOut,
    NotificationReplace,
)
from api.utils.database import get_db
from api.utils.helpers import (
    _example_for,
    _model_list,
    _model_out,
    _normalize_dt,
    _raise_for_dbapi_error,
)

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])

_NOTIFICATION_DB_ERROR_MAP: tuple[tuple[str, int, str], ...] = (
    ("notification not found", 404, "Notification not found"),
    ("notification is already dropped", 400, "Notification is already dropped"),
    ("only sender or superuser", 403, "Only sender or superuser can perform this action"),
    ("revision not found", 404, "Revision not found"),
    ("sender user not found", 404, "Sender user not found"),
    ("superseded notification not found", 404, "Superseded notification not found"),
    (
        "commented file does not belong to revision",
        400,
        "Commented file does not belong to revision",
    ),
    ("no valid recipients resolved for notification", 400, "No valid recipients resolved"),
    ("notification delivery row not found", 404, "Notification delivery row not found"),
)

_COMMON_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {
        "description": "Bad Request",
        "content": {"application/json": {"example": {"detail": "Bad Request"}}},
    },
    403: {
        "description": "Forbidden",
        "content": {"application/json": {"example": {"detail": "Forbidden"}}},
    },
    404: {
        "description": "Not Found",
        "content": {"application/json": {"example": {"detail": "Not Found"}}},
    },
    422: {
        "description": "Validation Error",
        "content": {
            "application/json": {
                "example": {
                    "detail": [
                        {
                            "loc": ["body", "field"],
                            "msg": "Field required",
                            "type": "missing",
                        }
                    ]
                }
            }
        },
    },
    500: {
        "description": "Internal Server Error",
        "content": {"application/json": {"example": {"detail": "Internal Server Error"}}},
    },
}


def _current_app_user_id(db: Session) -> int | None:
    row = (
        db.execute(
            text("SELECT NULLIF(current_setting('app.user', true), '')::SMALLINT AS user_id")
        )
        .mappings()
        .one()
    )
    return row["user_id"]


def _resolve_user_or_fail(db: Session, explicit_user_id: int | None, *, field_name: str) -> int:
    user_id = explicit_user_id or _current_app_user_id(db)
    if not user_id:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} is required (body or X-User-Id header)",
        )
    return user_id


def _require_current_user(db: Session) -> int:
    user_id = _current_app_user_id(db)
    if not user_id:
        raise HTTPException(
            status_code=400,
            detail="Current user is required (set X-User-Id header)",
        )
    return user_id


@router.post(
    "",
    summary="Create notification.",
    description=(
        "Creates a notification with direct users and/or DL targets, resolves recipients, and "
        "stores unread per-recipient delivery rows."
    ),
    operation_id="create_notification",
    response_model=NotificationActionResult,
    status_code=201,
    responses=_COMMON_RESPONSES,
)
def create_notification(
    payload: NotificationCreate = Body(..., openapi_examples=_example_for(NotificationCreate)),
    db: Session = Depends(get_db),
) -> NotificationActionResult:
    """
    Create notification.

    Creates a regular notification and resolves recipients from direct users and distribution lists.
    """
    sender_user_id = _resolve_user_or_fail(
        db,
        payload.sender_user_id,
        field_name="sender_user_id",
    )
    try:
        row = (
            db.execute(
                text(
                    """
                    SELECT notification_id, recipient_count
                    FROM workflow.create_notification(
                        :sender_user_id,
                        :title,
                        :body,
                        :rev_id,
                        :commented_file_id,
                        :recipient_user_ids,
                        :recipient_dist_ids,
                        :event_type,
                        :remark,
                        :supersedes_notification_id
                    )
                    """
                ),
                {
                    "sender_user_id": sender_user_id,
                    "title": payload.title,
                    "body": payload.body,
                    "rev_id": payload.rev_id,
                    "commented_file_id": payload.commented_file_id,
                    "recipient_user_ids": payload.recipient_user_ids,
                    "recipient_dist_ids": payload.recipient_dist_ids,
                    "event_type": "regular",
                    "remark": payload.remark,
                    "supersedes_notification_id": None,
                },
            )
            .mappings()
            .one()
        )
        db.commit()
    except DBAPIError as err:
        db.rollback()
        _raise_for_dbapi_error(err, _NOTIFICATION_DB_ERROR_MAP)

    return _model_out(NotificationActionResult, row)


@router.get(
    "",
    summary="List notifications for recipient.",
    description=(
        "Returns notifications for a recipient with optional filters: unread only, date range, "
        "and sender."
    ),
    operation_id="list_notifications_for_recipient",
    response_model=list[NotificationOut],
    responses=_COMMON_RESPONSES,
)
def list_notifications_for_recipient(
    recipient_user_id: int | None = Query(
        None,
        description="Recipient user ID. If omitted, uses X-User-Id.",
        gt=0,
    ),
    unread_only: bool = Query(False, description="When true, returns unread notifications only."),
    sender_user_id: int | None = Query(None, description="Filter by sender user ID.", gt=0),
    date_from: datetime | None = Query(None, description="Filter delivered_at >= this timestamp."),
    date_to: datetime | None = Query(None, description="Filter delivered_at <= this timestamp."),
    db: Session = Depends(get_db),
) -> list[NotificationOut]:
    """
    List notifications for recipient.

    Returns recipient inbox rows from workflow view with optional sender/date/unread filters.
    """
    resolved_recipient_user_id = _resolve_user_or_fail(
        db, recipient_user_id, field_name="recipient_user_id"
    )
    dt_from = _normalize_dt(date_from)
    dt_to = _normalize_dt(date_to)
    if dt_from and dt_to and dt_from > dt_to:
        raise HTTPException(status_code=400, detail="date_from cannot be later than date_to")

    filters = ["recipient_user_id = :recipient_user_id"]
    params: dict[str, Any] = {"recipient_user_id": resolved_recipient_user_id}
    if unread_only:
        filters.append("read_at IS NULL")
    if sender_user_id is not None:
        filters.append("sender_user_id = :sender_user_id")
        params["sender_user_id"] = sender_user_id
    if dt_from is not None:
        filters.append("delivered_at >= :date_from")
        params["date_from"] = dt_from
    if dt_to is not None:
        filters.append("delivered_at <= :date_to")
        params["date_to"] = dt_to

    sql = f"""
        SELECT
            notification_id,
            sender_user_id,
            event_type,
            title,
            body,
            remark,
            rev_id,
            commented_file_id,
            created_at,
            dropped_at,
            dropped_by_user_id,
            superseded_by_notification_id,
            recipient_user_id,
            delivered_at,
            read_at
        FROM workflow.v_notification_inbox
        WHERE {' AND '.join(filters)}
        ORDER BY delivered_at DESC, notification_id DESC
    """
    rows = db.execute(text(sql), params).mappings().all()
    return _model_list(NotificationOut, rows)


@router.post(
    "/{notification_id}/replace",
    summary="Replace notification.",
    description=(
        "Drops original notification and creates a new linked changed notification for the same "
        "recipients."
    ),
    operation_id="replace_notification",
    response_model=NotificationActionResult,
    responses=_COMMON_RESPONSES,
)
def replace_notification(
    notification_id: int = Path(..., description="Notification ID to replace.", gt=0),
    payload: NotificationReplace = Body(..., openapi_examples=_example_for(NotificationReplace)),
    db: Session = Depends(get_db),
) -> NotificationActionResult:
    """
    Replace notification.

    Sender or superuser can drop the original and create a changed notice as a new notification.
    """
    actor_user_id = _require_current_user(db)
    try:
        row = (
            db.execute(
                text(
                    """
                    SELECT notification_id, recipient_count
                    FROM workflow.replace_notification(
                        :actor_user_id,
                        :notification_id,
                        :title,
                        :body,
                        :remark
                    )
                    """
                ),
                {
                    "actor_user_id": actor_user_id,
                    "notification_id": notification_id,
                    "title": payload.title,
                    "body": payload.body,
                    "remark": payload.remark,
                },
            )
            .mappings()
            .one()
        )
        db.commit()
    except DBAPIError as err:
        db.rollback()
        _raise_for_dbapi_error(err, _NOTIFICATION_DB_ERROR_MAP)

    return _model_out(NotificationActionResult, row)


@router.post(
    "/{notification_id}/delete",
    summary="Drop notification.",
    description=(
        "Drops original notification and creates a new linked dropped notice for the same "
        "recipients."
    ),
    operation_id="drop_notification",
    response_model=NotificationActionResult,
    responses=_COMMON_RESPONSES,
)
def drop_notification(
    notification_id: int = Path(..., description="Notification ID to drop.", gt=0),
    payload: NotificationDelete = Body(..., openapi_examples=_example_for(NotificationDelete)),
    db: Session = Depends(get_db),
) -> NotificationActionResult:
    """
    Drop notification.

    Sender or superuser can drop the original and emit a dropped notice to recipients.
    """
    actor_user_id = _require_current_user(db)
    try:
        row = (
            db.execute(
                text(
                    """
                    SELECT notification_id, recipient_count
                    FROM workflow.delete_notification(
                        :actor_user_id,
                        :notification_id,
                        :remark
                    )
                    """
                ),
                {
                    "actor_user_id": actor_user_id,
                    "notification_id": notification_id,
                    "remark": payload.remark,
                },
            )
            .mappings()
            .one()
        )
        db.commit()
    except DBAPIError as err:
        db.rollback()
        _raise_for_dbapi_error(err, _NOTIFICATION_DB_ERROR_MAP)

    return _model_out(NotificationActionResult, row)


@router.post(
    "/{notification_id}/read",
    summary="Mark notification as read.",
    description="Marks the current recipient delivery row as read (idempotent).",
    operation_id="mark_notification_read",
    response_model=NotificationRecipientStateOut,
    responses=_COMMON_RESPONSES,
)
def mark_notification_read(
    notification_id: int = Path(..., description="Notification ID to mark as read.", gt=0),
    _payload: NotificationMarkRead = Body(..., openapi_examples=_example_for(NotificationMarkRead)),
    db: Session = Depends(get_db),
) -> NotificationRecipientStateOut:
    """
    Mark notification as read.

    Updates only recipient's delivery row; does not affect other recipients.
    """
    recipient_user_id = _require_current_user(db)
    try:
        row = (
            db.execute(
                text(
                    """
                    SELECT
                        notification_id,
                        recipient_user_id,
                        delivered_at,
                        read_at
                    FROM workflow.mark_notification_read(
                        :notification_id,
                        :recipient_user_id
                    )
                    """
                ),
                {
                    "notification_id": notification_id,
                    "recipient_user_id": recipient_user_id,
                },
            )
            .mappings()
            .one()
        )
        db.commit()
    except DBAPIError as err:
        db.rollback()
        _raise_for_dbapi_error(err, _NOTIFICATION_DB_ERROR_MAP)

    return _model_out(NotificationRecipientStateOut, row)
