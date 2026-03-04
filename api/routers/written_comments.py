"""Written comments endpoints for revision comment operations."""

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from api.schemas.written_comments import (
    WrittenCommentCreate,
    WrittenCommentOut,
    WrittenCommentUpdate,
)
from api.utils.database import (
    MISSING_IDENTITY_DETAIL,
    get_db,
    get_effective_user_id,
    require_effective_identity,
)
from api.utils.helpers import _model_list, _model_out, _raise_for_dbapi_error

router = APIRouter(
    prefix="/api/v1/documents/revisions",
    tags=["comments"],
    dependencies=[Depends(require_effective_identity)],
)

_WRITTEN_COMMENT_DB_ERROR_MAP: tuple[tuple[str, int, str], ...] = (
    ("revision not found", 404, "Revision not found"),
    ("user not found", 404, "User not found"),
    ("written comment not found", 404, "Written comment not found"),
    (
        "only comment author or superuser",
        403,
        "Only comment author or superuser can delete written comment",
    ),
    (
        "only comment author or superuser can update written comment",
        403,
        "Only comment author or superuser can update written comment",
    ),
    ("comment text must not be blank", 400, "Comment text must not be blank"),
)


@router.get(
    "/{rev_id}/comments",
    summary="List written comments for a revision.",
    description=(
        "Returns written comments linked to the specified revision. Optionally filters by user."
    ),
    operation_id="list_written_comments_for_revision",
    tags=["comments"],
    response_model=list[WrittenCommentOut],
    responses={
        400: {
            "description": "Bad Request",
            "content": {"application/json": {"example": {"detail": "Bad Request"}}},
        },
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {"loc": ["body", "field"], "msg": "Field required", "type": "missing"}
                        ]
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {"application/json": {"example": {"detail": "Internal Server Error"}}},
        },
    },
)
def list_written_comments_for_revision(
    rev_id: int = Path(..., gt=0, description="Revision ID to list comments for", examples=[1]),
    user_id: int | None = Query(
        None, gt=0, description="Optional user ID filter for comments", examples=[1]
    ),
    db: Session = Depends(get_db),
) -> list[WrittenCommentOut]:
    """
    List written comments for a revision.

    Args:
        rev_id: Revision ID to filter comments by.
        user_id: Optional user ID to filter comments by.

    Returns:
        List of written comments ordered by id.
    """
    sql = """
        SELECT
            id,
            rev_id,
            user_id,
            comment_text,
            created_at,
            updated_at,
            created_by,
            updated_by
        FROM workflow.v_written_comments
        WHERE rev_id = :rev_id
    """
    params: dict[str, Any] = {"rev_id": rev_id}
    if user_id is not None:
        sql += " AND user_id = :user_id"
        params["user_id"] = user_id
    sql += " ORDER BY id"
    rows = db.execute(text(sql), params).mappings().all()
    return _model_list(WrittenCommentOut, rows)


@router.post(
    "/{rev_id}/comments",
    summary="Create written comment.",
    description="Creates a short written comment linked to revision and user.",
    operation_id="create_written_comment",
    tags=["comments"],
    response_model=WrittenCommentOut,
    status_code=201,
    responses={
        400: {
            "description": "Bad Request",
            "content": {"application/json": {"example": {"detail": "Bad Request"}}},
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
                            {"loc": ["body", "field"], "msg": "Field required", "type": "missing"}
                        ]
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {"application/json": {"example": {"detail": "Internal Server Error"}}},
        },
    },
)
def create_written_comment(
    rev_id: int = Path(..., gt=0, description="Revision ID to attach comment to", examples=[1]),
    payload: WrittenCommentCreate = Body(...),
    db: Session = Depends(get_db),
) -> WrittenCommentOut:
    """
    Create written comment.

    Args:
        payload: Written comment payload with revision, user, and comment text.

    Returns:
        Newly created written comment.
    """
    user_exists = db.execute(
        text("SELECT user_id FROM workflow.v_users WHERE user_id = :user_id"),
        {"user_id": payload.user_id},
    ).scalar_one_or_none()
    if not user_exists:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        row = (
            db.execute(
                text(
                    """
                    SELECT
                        id,
                        rev_id,
                        user_id,
                        comment_text,
                        created_at,
                        updated_at,
                        created_by,
                        updated_by
                    FROM workflow.create_written_comment(
                        :rev_id,
                        :user_id,
                        :comment_text
                    )
                    """
                ),
                {
                    "rev_id": rev_id,
                    "user_id": payload.user_id,
                    "comment_text": payload.comment_text,
                },
            )
            .mappings()
            .one()
        )
        db.commit()
    except DBAPIError as err:
        db.rollback()
        _raise_for_dbapi_error(err, _WRITTEN_COMMENT_DB_ERROR_MAP)

    return _model_out(WrittenCommentOut, row)


@router.put(
    "/comments/{id}",
    summary="Update written comment.",
    description="Updates written comment text. Allowed for comment author or superuser.",
    operation_id="update_written_comment",
    tags=["comments"],
    response_model=WrittenCommentOut,
    responses={
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
                            {"loc": ["body", "field"], "msg": "Field required", "type": "missing"}
                        ]
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {"application/json": {"example": {"detail": "Internal Server Error"}}},
        },
    },
)
def update_written_comment(
    id: int = Path(..., description="Written comment ID to update", gt=0),
    payload: WrittenCommentUpdate = Body(...),
    db: Session = Depends(get_db),
) -> WrittenCommentOut:
    """
    Update written comment.

    Uses current app user (X-User-Id header) as actor for authorization.
    """
    actor_user_id = get_effective_user_id(db)
    if not actor_user_id:
        raise HTTPException(status_code=401, detail=MISSING_IDENTITY_DETAIL)
    try:
        row = (
            db.execute(
                text(
                    """
                    SELECT
                        id,
                        rev_id,
                        user_id,
                        comment_text,
                        created_at,
                        updated_at,
                        created_by,
                        updated_by
                    FROM workflow.update_written_comment(
                        :id,
                        :actor_user_id,
                        :comment_text
                    )
                    """
                ),
                {
                    "id": id,
                    "actor_user_id": actor_user_id,
                    "comment_text": payload.comment_text,
                },
            )
            .mappings()
            .one()
        )
        db.commit()
    except DBAPIError as err:
        db.rollback()
        _raise_for_dbapi_error(err, _WRITTEN_COMMENT_DB_ERROR_MAP)

    return _model_out(WrittenCommentOut, row)


@router.delete(
    "/comments/{id}",
    summary="Delete written comment.",
    description="Deletes written comment. Allowed for comment author or superuser.",
    operation_id="delete_written_comment",
    tags=["comments"],
    status_code=204,
    responses={
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
                            {"loc": ["body", "field"], "msg": "Field required", "type": "missing"}
                        ]
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {"application/json": {"example": {"detail": "Internal Server Error"}}},
        },
    },
)
def delete_written_comment(
    id: int = Path(..., description="Written comment ID to delete", gt=0),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete written comment.

    Uses current app user (X-User-Id header) as actor for authorization.
    """
    actor_user_id = get_effective_user_id(db)
    if not actor_user_id:
        raise HTTPException(status_code=401, detail=MISSING_IDENTITY_DETAIL)
    row = (
        db.execute(
            text("SELECT id FROM workflow.v_written_comments WHERE id = :id"),
            {"id": id},
        )
        .mappings()
        .one_or_none()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Written comment not found")
    try:
        db.execute(
            text("SELECT workflow.delete_written_comment(:id, :actor_user_id)"),
            {"id": id, "actor_user_id": actor_user_id},
        )
        db.commit()
    except DBAPIError as err:
        db.rollback()
        _raise_for_dbapi_error(err, _WRITTEN_COMMENT_DB_ERROR_MAP)
