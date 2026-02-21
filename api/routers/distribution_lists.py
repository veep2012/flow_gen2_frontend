"""Distribution list endpoints backed by workflow functions."""

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from api.schemas.distribution_lists import (
    DistributionListCreate,
    DistributionListMemberCreate,
    DistributionListMemberOut,
    DistributionListOut,
)
from api.utils.database import get_db
from api.utils.helpers import _example_for, _model_list, _model_out, _raise_for_dbapi_error

router = APIRouter(prefix="/api/v1/distribution-lists", tags=["distribution-lists"])

_DL_DB_ERROR_MAP: tuple[tuple[str, int, str], ...] = (
    ("distribution list not found", 404, "Distribution list not found"),
    ("distribution list is referenced by notifications", 409, "Distribution list is in use"),
    ("distribution list member not found", 404, "Distribution list member not found"),
    ("document not found", 404, "Document not found"),
    ("user not found", 404, "User not found"),
    ("duplicate key", 400, "Distribution list or membership already exists"),
)

_COMMON_RESPONSES: dict[int | str, dict[str, Any]] = {
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

_SQLSTATE_DOCUMENT_NOT_FOUND = "P0404"


@router.get(
    "",
    summary="List distribution lists.",
    description="Returns all distribution lists.",
    operation_id="list_distribution_lists",
    response_model=list[DistributionListOut],
    responses=_COMMON_RESPONSES,
)
def list_distribution_lists(
    doc_id: int | None = Query(None, description="Filter by linked document ID.", gt=0),
    db: Session = Depends(get_db),
) -> list[DistributionListOut]:
    """
    List distribution lists.

    Returns all distribution lists from workflow view.
    """
    clauses = [
        """
        SELECT dist_id, distribution_list_name, doc_id
        FROM workflow.distribution_list
        """
    ]
    params: dict[str, int] = {}
    if doc_id is not None:
        clauses.append("WHERE doc_id = :doc_id")
        params["doc_id"] = doc_id
    clauses.append("ORDER BY distribution_list_name, dist_id")
    sql = "\n".join(clauses)
    rows = db.execute(text(sql), params).mappings().all()
    return _model_list(DistributionListOut, rows)


@router.post(
    "",
    summary="Create distribution list.",
    description="Creates a distribution list through workflow function.",
    operation_id="create_distribution_list",
    response_model=DistributionListOut,
    status_code=201,
    responses=_COMMON_RESPONSES,
)
def create_distribution_list(
    payload: DistributionListCreate = Body(
        ...,
        openapi_examples=_example_for(DistributionListCreate),
    ),
    db: Session = Depends(get_db),
) -> DistributionListOut:
    """
    Create distribution list.

    Creates a distribution list with unique name, optionally linked to a document.
    """
    try:
        row = (
            db.execute(
                text(
                    """
                    SELECT dist_id, distribution_list_name, doc_id
                    FROM workflow.create_distribution_list(
                        :distribution_list_name,
                        :doc_id
                    )
                    """
                ),
                {
                    "distribution_list_name": payload.distribution_list_name,
                    "doc_id": payload.doc_id,
                },
            )
            .mappings()
            .one()
        )
        db.commit()
    except DBAPIError as err:
        db.rollback()
        sqlstate = getattr(getattr(err, "orig", None), "sqlstate", None)
        if sqlstate == _SQLSTATE_DOCUMENT_NOT_FOUND:
            raise HTTPException(status_code=404, detail="Document not found") from err
        _raise_for_dbapi_error(err, _DL_DB_ERROR_MAP)
    return _model_out(DistributionListOut, row)


@router.delete(
    "/{dist_id}",
    summary="Delete distribution list.",
    description="Deletes distribution list and all list members.",
    operation_id="delete_distribution_list",
    responses={
        **_COMMON_RESPONSES,
        200: {
            "description": "Deleted",
            "content": {"application/json": {"example": {"result": "ok"}}},
        },
    },
)
def delete_distribution_list(
    dist_id: int = Path(..., description="Distribution list ID.", gt=0),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """
    Delete distribution list.

    Removes list and membership rows via workflow function.
    """
    try:
        db.execute(
            text("SELECT workflow.delete_distribution_list(:dist_id)"),
            {"dist_id": dist_id},
        )
        db.commit()
    except DBAPIError as err:
        db.rollback()
        _raise_for_dbapi_error(err, _DL_DB_ERROR_MAP)
    return {"result": "ok"}


@router.get(
    "/{dist_id}/members",
    summary="List distribution list members.",
    description="Returns users assigned as members of the distribution list.",
    operation_id="list_distribution_list_members",
    response_model=list[DistributionListMemberOut],
    responses=_COMMON_RESPONSES,
)
def list_distribution_list_members(
    dist_id: int = Path(..., description="Distribution list ID.", gt=0),
    db: Session = Depends(get_db),
) -> list[DistributionListMemberOut]:
    """
    List distribution list members.

    Returns user membership rows with user/person display data.
    """
    exists = (
        db.execute(
            text("SELECT 1 FROM workflow.distribution_list WHERE dist_id = :dist_id"),
            {"dist_id": dist_id},
        )
        .mappings()
        .one_or_none()
    )
    if not exists:
        raise HTTPException(status_code=404, detail="Distribution list not found")

    rows = (
        db.execute(
            text(
                """
                SELECT
                    dlc.dist_id,
                    dlc.user_id,
                    u.person_id,
                    u.user_acronym,
                    p.person_name
                FROM workflow.distribution_list_content dlc
                JOIN workflow.users u ON u.user_id = dlc.user_id
                LEFT JOIN workflow.person p ON p.person_id = u.person_id
                WHERE dlc.dist_id = :dist_id
                ORDER BY u.user_acronym, dlc.user_id
                """
            ),
            {"dist_id": dist_id},
        )
        .mappings()
        .all()
    )
    return _model_list(DistributionListMemberOut, rows)


@router.post(
    "/{dist_id}/members",
    summary="Add distribution list member.",
    description="Adds a user to distribution list membership.",
    operation_id="add_distribution_list_member",
    response_model=DistributionListMemberOut,
    status_code=201,
    responses=_COMMON_RESPONSES,
)
def add_distribution_list_member(
    dist_id: int = Path(..., description="Distribution list ID.", gt=0),
    payload: DistributionListMemberCreate = Body(
        ..., openapi_examples=_example_for(DistributionListMemberCreate)
    ),
    db: Session = Depends(get_db),
) -> DistributionListMemberOut:
    """
    Add distribution list member.

    Adds a user to the specified distribution list.
    """
    try:
        db.execute(
            text(
                """
                SELECT dist_id, user_id
                FROM workflow.add_distribution_list_member(
                    :dist_id,
                    :user_id
                )
                """
            ),
            {"dist_id": dist_id, "user_id": payload.user_id},
        ).mappings().one()

        row = (
            db.execute(
                text(
                    """
                    SELECT
                        dlc.dist_id,
                        dlc.user_id,
                        u.person_id,
                        u.user_acronym,
                        p.person_name
                    FROM workflow.distribution_list_content dlc
                    JOIN workflow.users u ON u.user_id = dlc.user_id
                    LEFT JOIN workflow.person p ON p.person_id = u.person_id
                    WHERE dlc.dist_id = :dist_id
                      AND dlc.user_id = :user_id
                    """
                ),
                {"dist_id": dist_id, "user_id": payload.user_id},
            )
            .mappings()
            .one()
        )
        db.commit()
    except DBAPIError as err:
        db.rollback()
        _raise_for_dbapi_error(err, _DL_DB_ERROR_MAP)
    return _model_out(DistributionListMemberOut, row)


@router.delete(
    "/{dist_id}/members/{user_id}",
    summary="Remove distribution list member.",
    description="Removes a user from distribution list membership.",
    operation_id="remove_distribution_list_member",
    responses={
        **_COMMON_RESPONSES,
        200: {
            "description": "Deleted",
            "content": {"application/json": {"example": {"result": "ok"}}},
        },
    },
)
def remove_distribution_list_member(
    dist_id: int = Path(..., description="Distribution list ID.", gt=0),
    user_id: int = Path(..., description="User ID.", gt=0),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """
    Remove distribution list member.

    Deletes user membership from the specified list.
    """
    try:
        db.execute(
            text(
                """
                SELECT workflow.remove_distribution_list_member(
                    :dist_id,
                    :user_id
                )
                """
            ),
            {"dist_id": dist_id, "user_id": user_id},
        )
        db.commit()
    except DBAPIError as err:
        db.rollback()
        _raise_for_dbapi_error(err, _DL_DB_ERROR_MAP)
    return {"result": "ok"}
