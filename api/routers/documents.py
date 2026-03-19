"""Documents endpoints for managing documents, revisions, milestones, and overviews."""

import json
import logging
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from api.db.models import (
    Discipline,
    DocRevMilestone,
    DocType,
    RevisionOverview,
)
from api.schemas.documents import (
    DeleteResult,
    DocCreate,
    DocOut,
    DocRevisionCreate,
    DocRevisionOut,
    DocRevisionStatusTransition,
    DocRevisionUpdate,
    DocRevMilestoneCreate,
    DocRevMilestoneOut,
    DocRevMilestoneUpdate,
    DocTypeCreate,
    DocTypeOut,
    DocTypeUpdate,
    DocUpdate,
    RevisionOverviewCreate,
    RevisionOverviewOut,
    RevisionOverviewUpdate,
)
from api.utils.database import get_db, require_effective_identity
from api.utils.helpers import (
    _example_for,
    _handle_integrity_error,
    _model_list,
    _model_out,
    _normalize_dt,
    _raise_for_dbapi_error,
    _require_non_null_fields,
)

router = APIRouter(
    prefix="/api/v1/documents",
    tags=["documents"],
    dependencies=[Depends(require_effective_identity)],
)
logger = logging.getLogger(__name__)


def _build_doc_type_out(doc_type: DocType, discipline: Discipline | None = None) -> DocTypeOut:
    discipline = discipline or doc_type.discipline
    return DocTypeOut(
        type_id=doc_type.type_id,
        doc_type_name=doc_type.doc_type_name,
        ref_discipline_id=doc_type.ref_discipline_id,
        doc_type_acronym=doc_type.doc_type_acronym,
        discipline_name=discipline.discipline_name if discipline else None,
        discipline_acronym=discipline.discipline_acronym if discipline else None,
    )


@router.get(
    "/doc_types",
    summary="List all document types.",
    description=(
        "Returns a list of all document types sorted by document type name, including discipline "
        "information."
    ),
    operation_id="list_doc_types",
    tags=["documents"],
    response_model=list[DocTypeOut],
    responses={
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Bad Request",
                    },
                },
            },
        },
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": (
                        {
                            "detail": [
                                {
                                    "loc": ["body", "field"],
                                    "msg": "Field required",
                                    "type": "missing",
                                }
                            ]
                        }
                    ),
                },
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal Server Error",
                    },
                },
            },
        },
    },
)
def list_doc_types(db: Session = Depends(get_db)) -> list[DocTypeOut]:
    """
    List all document types.

    Returns a list of all document types sorted by document type name, including discipline
    information.

    Returns:
        List of document types with id, name, acronym, and associated discipline details.
    """
    rows = (
        db.execute(
            text(
                """
                SELECT
                    dt.type_id,
                    dt.doc_type_name,
                    dt.ref_discipline_id,
                    dt.doc_type_acronym,
                    d.discipline_name,
                    d.discipline_acronym
                FROM workflow.v_doc_types AS dt
                JOIN workflow.v_disciplines AS d ON d.discipline_id = dt.ref_discipline_id
                ORDER BY dt.doc_type_name
                """
            )
        )
        .mappings()
        .all()
    )
    return _model_list(DocTypeOut, rows)


def insert_doc_type(
    payload: DocTypeCreate = Body(..., openapi_examples=_example_for(DocTypeCreate)),
    db: Session = Depends(get_db),
) -> DocTypeOut:
    """
    Create a new document type.

    Inserts a new document type with the specified name, acronym, and discipline reference.

    Args:
        payload: Document type creation data including name, acronym, and discipline reference.

    Returns:
        Newly created document type object.

    Raises:
        HTTPException: 400 if document type already exists.
        HTTPException: 404 if referenced discipline not found.
    """
    discipline = db.get(Discipline, payload.ref_discipline_id)
    if not discipline:
        raise HTTPException(status_code=404, detail="Discipline not found")

    doc_type = DocType(
        doc_type_name=payload.doc_type_name,
        ref_discipline_id=payload.ref_discipline_id,
        doc_type_acronym=payload.doc_type_acronym,
    )
    db.add(doc_type)
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Doc type already exists", err, "insert_doc_type")

    db.refresh(doc_type)
    return _build_doc_type_out(doc_type)


def update_doc_type(
    type_id: int,
    payload: DocTypeUpdate = Body(..., openapi_examples=_example_for(DocTypeUpdate)),
    db: Session = Depends(get_db),
) -> DocTypeOut:
    """
    Update an existing document type.

    Updates the name, acronym, and/or discipline reference of an existing document type.

    Args:
        type_id: Document type ID to update.
        payload: Document type update data including at least one field to update.

    Returns:
        Updated document type object.

    Raises:
        HTTPException: 400 if no fields provided or document type already exists.
        HTTPException: 404 if document type or referenced discipline not found.
    """
    if not {
        "doc_type_name",
        "doc_type_acronym",
        "ref_discipline_id",
    }.intersection(payload.model_fields_set):
        raise HTTPException(status_code=400, detail="No fields provided for update")
    _require_non_null_fields(
        payload,
        ("doc_type_name", "ref_discipline_id", "doc_type_acronym"),
    )

    doc_type = db.get(DocType, type_id)
    if not doc_type:
        raise HTTPException(status_code=404, detail="Doc type not found")

    if payload.ref_discipline_id is not None:
        discipline = db.get(Discipline, payload.ref_discipline_id)
        if not discipline:
            raise HTTPException(status_code=404, detail="Discipline not found")
        doc_type.ref_discipline_id = payload.ref_discipline_id

    if payload.doc_type_name is not None:
        doc_type.doc_type_name = payload.doc_type_name
    if payload.doc_type_acronym is not None:
        doc_type.doc_type_acronym = payload.doc_type_acronym

    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Doc type already exists", err, "update_doc_type")

    db.refresh(doc_type)
    return _build_doc_type_out(doc_type)


def delete_doc_type(type_id: int, db: Session = Depends(get_db)) -> None:
    """
    Delete a document type.

    Removes a document type from the database by its ID.

    Args:
        type_id: Document type ID to delete.

    Raises:
        HTTPException: 404 if document type not found.
    """
    doc_type = db.get(DocType, type_id)
    if not doc_type:
        raise HTTPException(status_code=404, detail="Doc type not found")
    db.delete(doc_type)
    db.commit()


@router.get(
    "",
    summary="List all documents for a specific project.",
    description=(
        "Returns a list of all documents for the specified project, including details about "
        "associated types, disciplines, areas, units, and revision information."
    ),
    operation_id="list_documents_for_project",
    tags=["documents"],
    response_model=list[DocOut],
    responses={
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Bad Request",
                    },
                },
            },
        },
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": (
                        {
                            "detail": [
                                {
                                    "loc": ["body", "field"],
                                    "msg": "Field required",
                                    "type": "missing",
                                }
                            ]
                        }
                    ),
                },
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal Server Error",
                    },
                },
            },
        },
    },
)
def list_documents_for_project(
    project_id: int = Query(..., description="Project ID to filter documents by"),
    show_voided: bool = Query(
        False,
        description="Include voided documents in results when true.",
    ),
    db: Session = Depends(get_db),
) -> list[DocOut]:
    """
    List all documents for a specific project.

    Returns a list of all documents for the specified project, including details about associated
    types, disciplines, areas, units, and revision information.

    Args:
        project_id: The project ID to filter documents by.

    Returns:
        List of documents with comprehensive metadata.
    """
    sql = """
        SELECT
            d.doc_id,
            d.doc_name_unique,
            d.title,
            d.project_id,
            p.project_name,
            d.jobpack_id,
            j.jobpack_name,
            d.type_id,
            dt.doc_type_name,
            dt.doc_type_acronym,
            d.area_id,
            a.area_name,
            a.area_acronym,
            d.unit_id,
            u.unit_name,
            d.rev_actual_id,
            d.rev_current_id,
            rc.seq_num AS rev_seq_num,
            disc.discipline_id,
            disc.discipline_name,
            disc.discipline_acronym,
            ro.rev_code_name,
            ro.rev_code_acronym,
            rs.rev_status_id,
            rs.rev_status_name,
            ro.percentage,
            d.voided,
            d.created_at,
            d.updated_at,
            d.created_by,
            d.updated_by
        FROM workflow.v_documents AS d
        JOIN workflow.v_doc_types AS dt ON dt.type_id = d.type_id
        JOIN workflow.v_disciplines AS disc ON disc.discipline_id = dt.ref_discipline_id
        LEFT JOIN workflow.v_projects AS p ON p.project_id = d.project_id
        LEFT JOIN workflow.v_jobpacks AS j ON j.jobpack_id = d.jobpack_id
        LEFT JOIN workflow.v_areas AS a ON a.area_id = d.area_id
        LEFT JOIN workflow.v_units AS u ON u.unit_id = d.unit_id
        LEFT JOIN workflow.v_document_revisions AS rc ON rc.rev_id = d.rev_current_id
        LEFT JOIN workflow.v_revision_overview AS ro ON ro.rev_code_id = rc.rev_code_id
        LEFT JOIN workflow.v_doc_rev_statuses AS rs ON rs.rev_status_id = rc.rev_status_id
        WHERE d.project_id = :project_id
    """
    params: dict[str, Any] = {"project_id": project_id}
    if not show_voided:
        sql += " AND d.voided IS FALSE"
    sql += " ORDER BY d.doc_name_unique"
    rows = db.execute(text(sql), params).mappings().all()
    return _model_list(DocOut, rows)


def _fetch_doc_out(db: Session, doc_id: int, *, allow_voided: bool = True) -> DocOut:
    row = (
        db.execute(
            text(
                """
                SELECT
                    d.doc_id,
                    d.doc_name_unique,
                    d.title,
                    d.project_id,
                    p.project_name,
                    d.jobpack_id,
                    j.jobpack_name,
                    d.type_id,
                    dt.doc_type_name,
                    dt.doc_type_acronym,
                    d.area_id,
                    a.area_name,
                    a.area_acronym,
                    d.unit_id,
                    u.unit_name,
                    d.rev_actual_id,
                    d.rev_current_id,
                    rc.seq_num AS rev_seq_num,
                    disc.discipline_id,
                    disc.discipline_name,
                    disc.discipline_acronym,
                    ro.rev_code_name,
                    ro.rev_code_acronym,
                    rs.rev_status_id,
                    rs.rev_status_name,
                    ro.percentage,
                    d.voided,
                    d.created_at,
                    d.updated_at,
                    d.created_by,
                    d.updated_by
                FROM workflow.v_documents AS d
                JOIN workflow.v_doc_types AS dt ON dt.type_id = d.type_id
                JOIN workflow.v_disciplines AS disc ON disc.discipline_id = dt.ref_discipline_id
                LEFT JOIN workflow.v_projects AS p ON p.project_id = d.project_id
                LEFT JOIN workflow.v_jobpacks AS j ON j.jobpack_id = d.jobpack_id
                LEFT JOIN workflow.v_areas AS a ON a.area_id = d.area_id
                LEFT JOIN workflow.v_units AS u ON u.unit_id = d.unit_id
                LEFT JOIN workflow.v_document_revisions AS rc ON rc.rev_id = d.rev_current_id
                LEFT JOIN workflow.v_revision_overview AS ro ON ro.rev_code_id = rc.rev_code_id
                LEFT JOIN workflow.v_doc_rev_statuses AS rs ON rs.rev_status_id = rc.rev_status_id
                WHERE d.doc_id = :doc_id
                """
            ),
            {"doc_id": doc_id},
        )
        .mappings()
        .one_or_none()
    )
    if not row or (not allow_voided and row["voided"]):
        raise HTTPException(status_code=404, detail="Document not found")
    return _model_out(DocOut, row)


@router.get(
    "/{doc_id}/revisions",
    summary="List all revisions for a document.",
    description=(
        "Returns a list of all revisions for the specified document, including revision code and "
        "status details."
    ),
    operation_id="list_document_revisions",
    tags=["documents"],
    response_model=list[DocRevisionOut],
    responses={
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Bad Request",
                    },
                },
            },
        },
        404: {
            "description": "Not Found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not Found",
                    },
                },
            },
        },
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": (
                        {
                            "detail": [
                                {
                                    "loc": ["body", "field"],
                                    "msg": "Field required",
                                    "type": "missing",
                                }
                            ]
                        }
                    ),
                },
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal Server Error",
                    },
                },
            },
        },
    },
)
def list_document_revisions(
    doc_id: int = Path(..., description="Document ID to list revisions for", gt=0),
    db: Session = Depends(get_db),
) -> list[DocRevisionOut]:
    """
    List all revisions for a document.

    Returns a list of all revisions for the specified document, including revision code and
    status details.

    Args:
        doc_id: The document ID to list revisions for.

    Returns:
        List of document revisions with metadata.

    Raises:
        HTTPException: 404 if the document is not found.
    """
    doc_row = (
        db.execute(
            text("SELECT doc_id, voided FROM workflow.v_documents WHERE doc_id = :doc_id"),
            {"doc_id": doc_id},
        )
        .mappings()
        .one_or_none()
    )
    if not doc_row or doc_row["voided"]:
        raise HTTPException(status_code=404, detail="Document not found")

    rows = (
        db.execute(
            text(
                """
                SELECT
                    r.rev_id,
                    r.doc_id,
                    r.seq_num,
                    r.rev_code_id,
                    ro.rev_code_name,
                    ro.rev_code_acronym,
                    ro.rev_description,
                    r.rev_author_id,
                    r.rev_originator_id,
                    r.rev_modifier_id,
                    r.transmital_current_revision,
                    r.milestone_id,
                    m.milestone_name,
                    r.planned_start_date,
                    r.planned_finish_date,
                    r.actual_start_date,
                    r.actual_finish_date,
                    r.canceled_date,
                    r.rev_status_id,
                    rs.rev_status_name,
                    r.as_built,
                    r.superseded,
                    r.modified_doc_date,
                    r.created_at,
                    r.updated_at,
                    r.created_by,
                    r.updated_by
                FROM workflow.v_document_revisions AS r
                LEFT JOIN workflow.v_revision_overview AS ro
                    ON ro.rev_code_id = r.rev_code_id
                LEFT JOIN workflow.v_doc_rev_milestones AS m
                    ON m.milestone_id = r.milestone_id
                LEFT JOIN workflow.v_doc_rev_statuses AS rs
                    ON rs.rev_status_id = r.rev_status_id
                WHERE r.doc_id = :doc_id
                ORDER BY r.seq_num, r.rev_id
                """
            ),
            {"doc_id": doc_id},
        )
        .mappings()
        .all()
    )
    return _model_list(DocRevisionOut, rows)


def update_document_revision(
    rev_id: int,
    payload: DocRevisionUpdate = Body(..., openapi_examples=_example_for(DocRevisionUpdate)),
    db: Session = Depends(get_db),
) -> DocRevisionOut:
    """
    Update an existing document revision.

    Updates fields of an existing document revision. The request supports partial updates; at
    least one field must be provided.

    Args:
        rev_id: Revision ID to update.
        payload: Revision update data including at least one field to update.

    Returns:
        Updated document revision with metadata.

    Raises:
        HTTPException: 400 if no fields provided.
        HTTPException: 404 if revision or referenced entities not found.
    """
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    _require_non_null_fields(
        payload,
        (
            "seq_num",
            "rev_code_id",
            "rev_author_id",
            "rev_originator_id",
            "rev_modifier_id",
            "transmital_current_revision",
            "planned_start_date",
            "planned_finish_date",
            "modified_doc_date",
            "as_built",
        ),
    )

    doc_row = (
        db.execute(
            text(
                """
                SELECT d.doc_id, d.voided
                FROM workflow.v_documents AS d
                JOIN workflow.v_document_revisions AS r ON r.doc_id = d.doc_id
                WHERE r.rev_id = :rev_id
                """
            ),
            {"rev_id": rev_id},
        )
        .mappings()
        .one_or_none()
    )
    if not doc_row:
        raise HTTPException(status_code=404, detail="Revision not found")
    if doc_row["voided"]:
        raise HTTPException(status_code=404, detail="Document not found")
    patch = {key: value for key, value in updates.items() if value is not None}
    if not patch:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    try:
        db.execute(
            text("SELECT * FROM workflow.update_revision(:rev_id, CAST(:patch AS jsonb))"),
            {"rev_id": rev_id, "patch": json.dumps(patch)},
        )
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Failed to update revision", err, "update_document_revision")
    except DBAPIError as err:
        db.rollback()
        _raise_for_dbapi_error(err, _UPDATE_REVISION_DB_ERROR_MAP)

    return _build_doc_revision_out(db, rev_id)


def _build_doc_revision_out(db: Session, rev_id: int) -> DocRevisionOut:
    row = (
        db.execute(
            text(
                """
                SELECT
                    r.rev_id,
                    r.doc_id,
                    r.seq_num,
                    r.rev_code_id,
                    ro.rev_code_name,
                    ro.rev_code_acronym,
                    ro.rev_description,
                    r.rev_author_id,
                    r.rev_originator_id,
                    r.rev_modifier_id,
                    r.transmital_current_revision,
                    r.milestone_id,
                    m.milestone_name,
                    r.planned_start_date,
                    r.planned_finish_date,
                    r.actual_start_date,
                    r.actual_finish_date,
                    r.canceled_date,
                    r.rev_status_id,
                    rs.rev_status_name,
                    r.as_built,
                    r.superseded,
                    r.modified_doc_date,
                    r.created_at,
                    r.updated_at,
                    r.created_by,
                    r.updated_by
                FROM workflow.v_document_revisions AS r
                LEFT JOIN workflow.v_revision_overview AS ro
                    ON ro.rev_code_id = r.rev_code_id
                LEFT JOIN workflow.v_doc_rev_milestones AS m
                    ON m.milestone_id = r.milestone_id
                LEFT JOIN workflow.v_doc_rev_statuses AS rs
                    ON rs.rev_status_id = r.rev_status_id
                WHERE r.rev_id = :rev_id
                """
            ),
            {"rev_id": rev_id},
        )
        .mappings()
        .one_or_none()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Revision not found")
    return _model_out(DocRevisionOut, row)


def _build_doc_revision_out_from_core_row(db: Session, row: dict[str, Any]) -> DocRevisionOut:
    rev_code = (
        db.execute(
            text(
                """
                SELECT rev_code_name, rev_code_acronym, rev_description
                FROM workflow.v_revision_overview
                WHERE rev_code_id = :rev_code_id
                """
            ),
            {"rev_code_id": row["rev_code_id"]},
        )
        .mappings()
        .one_or_none()
    )
    milestone = None
    if row.get("milestone_id") is not None:
        milestone = (
            db.execute(
                text(
                    """
                    SELECT milestone_name
                    FROM workflow.v_doc_rev_milestones
                    WHERE milestone_id = :milestone_id
                    """
                ),
                {"milestone_id": row["milestone_id"]},
            )
            .mappings()
            .one_or_none()
        )
    rev_status = (
        db.execute(
            text(
                """
                SELECT rev_status_name
                FROM workflow.v_doc_rev_statuses
                WHERE rev_status_id = :rev_status_id
                """
            ),
            {"rev_status_id": row["rev_status_id"]},
        )
        .mappings()
        .one_or_none()
    )
    return _model_out(
        DocRevisionOut,
        {
            **row,
            "rev_code_name": rev_code["rev_code_name"] if rev_code else None,
            "rev_code_acronym": rev_code["rev_code_acronym"] if rev_code else None,
            "rev_description": rev_code["rev_description"] if rev_code else None,
            "milestone_name": milestone["milestone_name"] if milestone else None,
            "rev_status_name": rev_status["rev_status_name"] if rev_status else None,
        },
    )


_REV_STATUS_TRANSITION_ERROR_MAP: tuple[tuple[str, int, str], ...] = (
    ("already at final status", 409, "Revision already at final status"),
    ("already at start status", 409, "Revision already at start status"),
    ("not revertible", 409, "Revision status not revertible"),
    (
        "superseded revision cannot be transitioned",
        409,
        "Superseded revision cannot be transitioned",
    ),
    ("previous status not found", 409, "Previous status not found"),
    (
        "files must exist before leaving the start status",
        409,
        "Files must exist before leaving the start status",
    ),
    ("invalid direction", 400, "Invalid direction"),
    ("revision not found", 404, "Revision not found"),
)


def _raise_for_status_transition_db_error(err: DBAPIError) -> None:
    _raise_for_dbapi_error(
        err,
        _REV_STATUS_TRANSITION_ERROR_MAP,
        default_detail="Failed to transition revision status",
    )


_UPDATE_REVISION_DB_ERROR_MAP: tuple[tuple[str, int, str], ...] = (
    ("revision not found", 404, "Revision not found"),
    ("no fields to update", 400, "No fields provided for update"),
    ("final revision is immutable", 409, "Final revision is immutable"),
)

_INSERT_REVISION_DB_ERROR_MAP: tuple[tuple[str, int, str], ...] = (
    ("document not found", 404, "Document not found"),
    ("revision code not found", 404, "Revision code not found"),
    ("milestone not found", 404, "Milestone not found"),
    ("revision author not found", 404, "Revision author not found"),
    ("revision originator not found", 404, "Revision originator not found"),
    ("revision modifier not found", 404, "Revision modifier not found"),
    ("no start status configured", 400, "No start status configured"),
    (
        "only one active (non-final, non-canceled) revision allowed per document",
        409,
        "Only one active (non-final, non-canceled) revision allowed per document",
    ),
)

_UPDATE_DOCUMENT_DB_ERROR_MAP: tuple[tuple[str, int, str], ...] = (
    ("document not found", 404, "Document not found"),
    ("no fields to update", 400, "No fields provided for update"),
)

_INSERT_DOCUMENT_DB_ERROR_MAP: tuple[tuple[str, int, str], ...] = (
    ("no start status configured", 400, "No start status configured"),
    ("project not found", 404, "Project not found"),
    ("jobpack not found", 404, "Jobpack not found"),
    ("doc type not found", 404, "Doc type not found"),
    ("area not found", 404, "Area not found"),
    ("unit not found", 404, "Unit not found"),
    ("revision code not found", 404, "Revision code not found"),
    ("milestone not found", 404, "Milestone not found"),
    ("revision author not found", 404, "Revision author not found"),
    ("revision originator not found", 404, "Revision originator not found"),
    ("revision modifier not found", 404, "Revision modifier not found"),
)

_CANCEL_REVISION_DB_ERROR_MAP: tuple[tuple[str, int, str], ...] = (
    ("revision not found", 404, "Revision not found"),
    ("final revision cannot be canceled", 409, "Final revision cannot be canceled"),
)

_DELETE_DOCUMENT_DB_ERROR_MAP: tuple[tuple[str, int, str], ...] = (
    ("document not found", 404, "Document not found"),
    ("no start status configured", 400, "No start status configured"),
)

_REVISION_OVERVIEW_DB_ERROR_MAP: tuple[tuple[str, int, str], ...] = (
    (
        "cycle detected in revision_overview",
        400,
        "Revision overview lifecycle cannot contain cycles",
    ),
    ("chk_revision_overview_no_self_ref", 400, "Revision overview step cannot point to itself"),
    ("chk_revision_overview_final_flags", 400, "Final revision overview step must be locked"),
    (
        "chk_revision_overview_final_next_eq",
        400,
        "Final revision overview step configuration is inconsistent",
    ),
    ("ux_revision_overview_single_start", 400, "Only one revision overview start step is allowed"),
    ("ux_revision_overview_single_final", 400, "Only one revision overview final step is allowed"),
    (
        "ux_revision_overview_single_predecessor",
        400,
        "Revision overview lifecycle must remain a single ordered path",
    ),
)


def create_revision_status_transition(
    rev_id: int,
    payload: DocRevisionStatusTransition = Body(
        ..., openapi_examples=_example_for(DocRevisionStatusTransition)
    ),
    db: Session = Depends(get_db),
) -> DocRevisionOut:
    """
    Transition a document revision status forward or back.

    Status changes are enforced by database rules (start/final/revertible).
    """
    try:
        rev_row = (
            db.execute(
                text("SELECT r.* FROM workflow.transition_revision(:rev_id, :direction) AS r"),
                {"rev_id": rev_id, "direction": payload.direction},
            )
            .mappings()
            .one()
        )
        db.commit()
    except DBAPIError as err:
        db.rollback()
        _raise_for_status_transition_db_error(err)

    return _build_doc_revision_out_from_core_row(db, dict(rev_row))


def insert_document_revision(
    doc_id: int,
    payload: DocRevisionCreate = Body(..., openapi_examples=_example_for(DocRevisionCreate)),
    db: Session = Depends(get_db),
) -> DocRevisionOut:
    """
    Create a new document revision.

    Creates a revision for the specified document. The sequence number is auto-assigned as
    max(seq_num)+1 for the document.

    Args:
        doc_id: Document ID to attach the revision to.
        payload: Revision creation data.

    Returns:
        Newly created document revision with metadata.

    Raises:
        HTTPException: 404 if document or referenced entities not found.
    """
    doc_row = (
        db.execute(
            text("SELECT doc_id, voided FROM workflow.v_documents WHERE doc_id = :doc_id"),
            {"doc_id": doc_id},
        )
        .mappings()
        .one_or_none()
    )
    if not doc_row or doc_row["voided"]:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        rev_id = db.execute(
            text(
                """
                SELECT workflow.create_revision(
                    :doc_id,
                    :rev_code_id,
                    :rev_author_id,
                    :rev_originator_id,
                    :rev_modifier_id,
                    :transmital_current_revision,
                    :milestone_id,
                    :planned_start_date,
                    :planned_finish_date,
                    :actual_start_date,
                    :actual_finish_date,
                    :modified_doc_date,
                    :as_built
                )
                """
            ),
            {
                "doc_id": doc_id,
                "rev_code_id": payload.rev_code_id,
                "rev_author_id": payload.rev_author_id,
                "rev_originator_id": payload.rev_originator_id,
                "rev_modifier_id": payload.rev_modifier_id,
                "transmital_current_revision": payload.transmital_current_revision,
                "milestone_id": payload.milestone_id,
                "planned_start_date": _normalize_dt(payload.planned_start_date),
                "planned_finish_date": _normalize_dt(payload.planned_finish_date),
                "actual_start_date": _normalize_dt(payload.actual_start_date),
                "actual_finish_date": _normalize_dt(payload.actual_finish_date),
                "modified_doc_date": _normalize_dt(payload.modified_doc_date),
                "as_built": payload.as_built,
            },
        ).scalar_one()
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Failed to create revision", err, "insert_document_revision")
    except DBAPIError as err:
        db.rollback()
        _raise_for_dbapi_error(err, _INSERT_REVISION_DB_ERROR_MAP)
    except Exception as err:
        db.rollback()
        logger.exception("Failed to create revision doc_id=%s", doc_id)
        raise HTTPException(status_code=500, detail="Internal Server Error") from err
    return _build_doc_revision_out(db, rev_id)


def update_document(
    doc_id: int,
    payload: DocUpdate = Body(..., openapi_examples=_example_for(DocUpdate)),
    db: Session = Depends(get_db),
) -> DocOut:
    """
    Update an existing document.

    Updates various fields of an existing document including name, title, project, jobpack, type,
    area, unit, and revision references. Validates all foreign key references and ensures document
    name uniqueness.

    Args:
        doc_id: Document ID to update.
        payload: Document update data including at least one field to update.

    Returns:
        Updated document with complete metadata.

    Raises:
        HTTPException: 400 if no fields provided, required field is null, or
        document name not unique.
        HTTPException: 404 if document or any referenced entity not found.
    """
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    _require_non_null_fields(
        payload,
        ("doc_name_unique", "title", "type_id", "area_id", "unit_id"),
    )

    patch = {key: value for key, value in updates.items() if value is not None}
    if not patch:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    try:
        db.execute(
            text("SELECT * FROM workflow.update_document(:doc_id, CAST(:patch AS jsonb))"),
            {"doc_id": doc_id, "patch": json.dumps(patch)},
        )
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Document name must be unique", err, "update_document")
    except DBAPIError as err:
        db.rollback()
        _raise_for_dbapi_error(err, _UPDATE_DOCUMENT_DB_ERROR_MAP)

    return _fetch_doc_out(db, doc_id, allow_voided=False)


def insert_document(
    payload: DocCreate = Body(..., openapi_examples=_example_for(DocCreate)),
    db: Session = Depends(get_db),
) -> DocOut:
    """
    Create a new document with an initial revision.

    Creates a new document and automatically creates an initial revision with the
    status that has start=true from doc_rev_statuses. The sequence number is set to 1.

    Args:
        payload: Document creation data including document details and initial revision details.

    Returns:
        Newly created document with metadata.

    Raises:
        HTTPException: 400 if document name already exists or no start status found.
        HTTPException: 404 if referenced entities not found.
    """
    # Create the document and initial revision in the database
    try:
        result = db.execute(
            text(
                """
                SELECT doc_id, rev_id
                FROM workflow.create_document(
                    :doc_name_unique,
                    :title,
                    :project_id,
                    :jobpack_id,
                    :type_id,
                    :area_id,
                    :unit_id,
                    :rev_code_id,
                    :rev_author_id,
                    :rev_originator_id,
                    :rev_modifier_id,
                    :transmital_current_revision,
                    :milestone_id,
                    :planned_start_date,
                    :planned_finish_date,
                    :actual_start_date,
                    :actual_finish_date,
                    :modified_doc_date,
                    :as_built
                )
                """
            ),
            {
                "doc_name_unique": payload.doc_name_unique,
                "title": payload.title,
                "project_id": payload.project_id,
                "jobpack_id": payload.jobpack_id,
                "type_id": payload.type_id,
                "area_id": payload.area_id,
                "unit_id": payload.unit_id,
                "rev_code_id": payload.rev_code_id,
                "rev_author_id": payload.rev_author_id,
                "rev_originator_id": payload.rev_originator_id,
                "rev_modifier_id": payload.rev_modifier_id,
                "transmital_current_revision": payload.transmital_current_revision,
                "milestone_id": payload.milestone_id,
                "planned_start_date": _normalize_dt(payload.planned_start_date),
                "planned_finish_date": _normalize_dt(payload.planned_finish_date),
                "actual_start_date": _normalize_dt(getattr(payload, "actual_start_date", None)),
                "actual_finish_date": _normalize_dt(getattr(payload, "actual_finish_date", None)),
                "modified_doc_date": _normalize_dt(getattr(payload, "modified_doc_date", None)),
                "as_built": getattr(payload, "as_built", False),
            },
        ).one()
        doc_id = result.doc_id
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Document name must be unique", err, "insert_document")
    except DBAPIError as err:
        db.rollback()
        _raise_for_dbapi_error(err, _INSERT_DOCUMENT_DB_ERROR_MAP)
    try:
        db.commit()
    except Exception as err:
        db.rollback()
        logger.exception("Failed to commit document doc_id=%s", doc_id)
        raise HTTPException(status_code=500, detail="Internal Server Error") from err

    return _fetch_doc_out(db, doc_id)


@router.get(
    "/doc_rev_milestones",
    summary="List all document revision milestones.",
    description="Returns a list of all document revision milestones sorted by milestone name.",
    operation_id="list_doc_rev_milestones",
    tags=["documents"],
    response_model=list[DocRevMilestoneOut],
    responses={
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Bad Request",
                    },
                },
            },
        },
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": (
                        {
                            "detail": [
                                {
                                    "loc": ["body", "field"],
                                    "msg": "Field required",
                                    "type": "missing",
                                }
                            ]
                        }
                    ),
                },
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal Server Error",
                    },
                },
            },
        },
    },
)
def list_doc_rev_milestones(db: Session = Depends(get_db)) -> list[DocRevMilestoneOut]:
    """
    List all document revision milestones.

    Returns a list of all document revision milestones sorted by milestone name.

    Returns:
        List of milestones with id, name, and progress percentage.
    """
    rows = (
        db.execute(
            text(
                """
                SELECT milestone_id, milestone_name, progress
                FROM workflow.v_doc_rev_milestones
                ORDER BY milestone_name
                """
            )
        )
        .mappings()
        .all()
    )
    return _model_list(DocRevMilestoneOut, rows)


def update_doc_rev_milestone(
    milestone_id: int,
    payload: DocRevMilestoneUpdate = Body(
        ..., openapi_examples=_example_for(DocRevMilestoneUpdate)
    ),
    db: Session = Depends(get_db),
) -> DocRevMilestoneOut:
    """
    Update an existing document revision milestone.

    Updates the name and/or progress percentage of an existing milestone.

    Args:
        milestone_id: Milestone ID to update.
        payload: Milestone update data including at least one field to update.

    Returns:
        Updated milestone object.

    Raises:
        HTTPException: 400 if no fields provided or milestone name already exists.
        HTTPException: 404 if milestone not found.
    """
    if not {"milestone_name", "progress"}.intersection(payload.model_fields_set):
        raise HTTPException(status_code=400, detail="No fields provided for update")
    _require_non_null_fields(payload, ("milestone_name",))

    milestone = db.get(DocRevMilestone, milestone_id)
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")

    if payload.milestone_name is not None:
        milestone.milestone_name = payload.milestone_name
    if payload.progress is not None:
        milestone.progress = payload.progress

    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Milestone name already exists", err, "update_doc_rev_milestone")

    db.refresh(milestone)
    return _model_out(DocRevMilestoneOut, milestone)


def insert_doc_rev_milestone(
    payload: DocRevMilestoneCreate = Body(
        ..., openapi_examples=_example_for(DocRevMilestoneCreate)
    ),
    db: Session = Depends(get_db),
) -> DocRevMilestoneOut:
    """
    Create a new document revision milestone.

    Inserts a new milestone with the specified name and optional progress percentage.

    Args:
        payload: Milestone creation data including name and optional progress.

    Returns:
        Newly created milestone object.

    Raises:
        HTTPException: 400 if milestone name already exists.
    """
    milestone = DocRevMilestone(milestone_name=payload.milestone_name, progress=payload.progress)
    db.add(milestone)
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Milestone name already exists", err, "insert_doc_rev_milestone")
    db.refresh(milestone)
    return _model_out(DocRevMilestoneOut, milestone)


def delete_doc_rev_milestone(milestone_id: int, db: Session = Depends(get_db)) -> None:
    """
    Delete a document revision milestone.

    Removes a milestone from the database by its ID.

    Args:
        milestone_id: Milestone ID to delete.

    Raises:
        HTTPException: 404 if milestone not found.
    """
    milestone = db.get(DocRevMilestone, milestone_id)
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    db.delete(milestone)
    db.commit()


@router.get(
    "/revision_overview",
    summary="List all revision overview entries.",
    description=(
        "Returns revision overview lifecycle steps ordered from the start step to the final step."
    ),
    operation_id="list_revision_overview",
    tags=["documents"],
    response_model=list[RevisionOverviewOut],
    responses={
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Bad Request",
                    },
                },
            },
        },
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": (
                        {
                            "detail": [
                                {
                                    "loc": ["body", "field"],
                                    "msg": "Field required",
                                    "type": "missing",
                                }
                            ]
                        }
                    ),
                },
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal Server Error",
                    },
                },
            },
        },
    },
)
def list_revision_overview(db: Session = Depends(get_db)) -> list[RevisionOverviewOut]:
    """
    List all revision overview entries.

    Returns revision overview lifecycle steps ordered from the configured start step and
    walking `next_rev_code_id` until the terminal step. The response order is path-derived,
    not name, ID, or percentage sorted.

    Returns:
        List of revision codes with lifecycle fields and percentage.
    """
    rows = (
        db.execute(
            text(
                """
                WITH RECURSIVE revision_flow AS (
                    SELECT
                        rev_code_id,
                        rev_code_name,
                        rev_code_acronym,
                        rev_description,
                        next_rev_code_id,
                        revertible,
                        editable,
                        final,
                        start,
                        percentage,
                        1 AS step_order
                    FROM workflow.v_revision_overview
                    WHERE start IS TRUE
                    UNION ALL
                    SELECT
                        child.rev_code_id,
                        child.rev_code_name,
                        child.rev_code_acronym,
                        child.rev_description,
                        child.next_rev_code_id,
                        child.revertible,
                        child.editable,
                        child.final,
                        child.start,
                        child.percentage,
                        parent.step_order + 1 AS step_order
                    FROM workflow.v_revision_overview AS child
                    JOIN revision_flow AS parent
                        ON child.rev_code_id = parent.next_rev_code_id
                )
                SELECT
                    rev_code_id,
                    rev_code_name,
                    rev_code_acronym,
                    rev_description,
                    next_rev_code_id,
                    revertible,
                    editable,
                    final,
                    start,
                    percentage
                FROM revision_flow
                ORDER BY step_order
                """
            )
        )
        .mappings()
        .all()
    )
    return _model_list(RevisionOverviewOut, rows)


def update_revision_overview(
    rev_code_id: int,
    payload: RevisionOverviewUpdate = Body(
        ..., openapi_examples=_example_for(RevisionOverviewUpdate)
    ),
    db: Session = Depends(get_db),
) -> RevisionOverviewOut:
    """
    Update an existing revision overview entry.

    Updates the name, acronym, description, and/or percentage of an existing revision overview
    entry.

    Args:
        rev_code_id: Revision code ID to update.
        payload: Revision overview update data including at least one field to update.

    Returns:
        Updated revision overview object.

    Raises:
        HTTPException: 400 if no fields provided or revision overview already exists.
        HTTPException: 404 if revision overview entry not found.
    """
    if not {
        "rev_code_name",
        "rev_code_acronym",
        "rev_description",
        "next_rev_code_id",
        "revertible",
        "editable",
        "final",
        "start",
        "percentage",
    }.intersection(payload.model_fields_set):
        raise HTTPException(status_code=400, detail="No fields provided for update")
    _require_non_null_fields(
        payload,
        ("rev_code_name", "rev_code_acronym", "rev_description"),
    )

    revision = db.get(RevisionOverview, rev_code_id)
    if not revision:
        raise HTTPException(status_code=404, detail="Revision overview entry not found")

    if payload.rev_code_name is not None:
        revision.rev_code_name = payload.rev_code_name
    if payload.rev_code_acronym is not None:
        revision.rev_code_acronym = payload.rev_code_acronym
    if payload.rev_description is not None:
        revision.rev_description = payload.rev_description
    if "next_rev_code_id" in payload.model_fields_set:
        revision.next_rev_code_id = payload.next_rev_code_id
    if payload.revertible is not None:
        revision.revertible = payload.revertible
    if payload.editable is not None:
        revision.editable = payload.editable
    if payload.final is not None:
        revision.final = payload.final
    if payload.start is not None:
        revision.start = payload.start
    if payload.percentage is not None:
        revision.percentage = payload.percentage

    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _raise_for_dbapi_error(
            err,
            _REVISION_OVERVIEW_DB_ERROR_MAP,
            default_status=400,
            default_detail="Revision overview entry already exists",
        )
    except DBAPIError as err:
        db.rollback()
        _raise_for_dbapi_error(
            err,
            _REVISION_OVERVIEW_DB_ERROR_MAP,
            default_status=400,
            default_detail="Invalid revision overview lifecycle",
        )

    db.refresh(revision)
    return _model_out(RevisionOverviewOut, revision)


def insert_revision_overview(
    payload: RevisionOverviewCreate = Body(
        ..., openapi_examples=_example_for(RevisionOverviewCreate)
    ),
    db: Session = Depends(get_db),
) -> RevisionOverviewOut:
    """
    Create a new revision overview entry.

    Inserts a new revision overview entry with the specified code, acronym, description, and
    percentage.

    Args:
        payload: Revision overview creation data including code name, acronym,
        description, and optional percentage.

    Returns:
        Newly created revision overview object.

    Raises:
        HTTPException: 400 if revision overview entry already exists.
    """
    revision = RevisionOverview(
        rev_code_name=payload.rev_code_name,
        rev_code_acronym=payload.rev_code_acronym,
        rev_description=payload.rev_description,
        next_rev_code_id=payload.next_rev_code_id,
        revertible=payload.revertible,
        editable=payload.editable,
        final=payload.final,
        start=payload.start,
        percentage=payload.percentage,
    )
    db.add(revision)
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _raise_for_dbapi_error(
            err,
            _REVISION_OVERVIEW_DB_ERROR_MAP,
            default_status=400,
            default_detail="Revision overview entry already exists",
        )
    except DBAPIError as err:
        db.rollback()
        _raise_for_dbapi_error(
            err,
            _REVISION_OVERVIEW_DB_ERROR_MAP,
            default_status=400,
            default_detail="Invalid revision overview lifecycle",
        )
    db.refresh(revision)
    return _model_out(RevisionOverviewOut, revision)


def delete_revision_overview(rev_code_id: int, db: Session = Depends(get_db)) -> None:
    """
    Delete a revision overview entry.

    Removes a revision overview entry from the database by its ID.

    Args:
        rev_code_id: Revision overview ID to delete.

    Raises:
        HTTPException: 404 if revision overview entry not found.
    """
    revision = db.get(RevisionOverview, rev_code_id)
    if not revision:
        raise HTTPException(status_code=404, detail="Revision overview entry not found")
    db.delete(revision)
    db.commit()


# ---------------------------------------------------------------------------
# RESTful aliases (POST collection, PUT/DELETE item)
# ---------------------------------------------------------------------------

_REST_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {
        "description": "Bad Request",
        "content": {"application/json": {"example": {"detail": "Bad Request"}}},
    },
    404: {
        "description": "Not Found",
        "content": {"application/json": {"example": {"detail": "Not Found"}}},
    },
    409: {
        "description": "Conflict",
        "content": {"application/json": {"example": {"detail": "Conflict"}}},
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
}


@router.put(
    "/{doc_id}",
    summary="Update an existing document (REST).",
    description="Updates the metadata of an existing document.",
    response_model=DocOut,
    tags=["documents"],
    responses=_REST_RESPONSES,
)
def update_document_rest(
    doc_id: int,
    payload: DocUpdate = Body(..., openapi_examples=_example_for(DocUpdate)),
    db: Session = Depends(get_db),
) -> DocOut:
    return update_document(doc_id, payload, db)


@router.put(
    "/revisions/{rev_id}",
    summary="Update a document revision (REST).",
    description="Updates fields of an existing document revision.",
    response_model=DocRevisionOut,
    tags=["documents"],
    responses=_REST_RESPONSES,
)
def update_document_revision_rest(
    rev_id: int,
    payload: DocRevisionUpdate = Body(..., openapi_examples=_example_for(DocRevisionUpdate)),
    db: Session = Depends(get_db),
) -> DocRevisionOut:
    return update_document_revision(rev_id, payload, db)


@router.post(
    "/revisions/{rev_id}/status-transitions",
    summary="Transition a document revision status (REST).",
    description="Moves a revision status forward or back according to workflow rules.",
    response_model=DocRevisionOut,
    tags=["documents"],
    responses=_REST_RESPONSES,
)
def create_revision_status_transition_rest(
    rev_id: int,
    payload: DocRevisionStatusTransition = Body(
        ..., openapi_examples=_example_for(DocRevisionStatusTransition)
    ),
    db: Session = Depends(get_db),
) -> DocRevisionOut:
    return create_revision_status_transition(rev_id, payload, db)


@router.post(
    "/{doc_id}/revisions",
    summary="Create a document revision (REST).",
    description="Creates a revision for the specified document.",
    response_model=DocRevisionOut,
    status_code=201,
    tags=["documents"],
    responses=_REST_RESPONSES,
)
def create_document_revision_rest(
    doc_id: int,
    payload: DocRevisionCreate = Body(..., openapi_examples=_example_for(DocRevisionCreate)),
    db: Session = Depends(get_db),
) -> DocRevisionOut:
    return insert_document_revision(doc_id, payload, db)


@router.post(
    "",
    summary="Create a new document (REST).",
    description=(
        "Creates a new document with an initial revision. The initial revision automatically "
        "uses the status with start=true from doc_rev_statuses."
    ),
    response_model=DocOut,
    status_code=201,
    tags=["documents"],
    responses=_REST_RESPONSES,
)
def create_document_rest(
    payload: DocCreate = Body(..., openapi_examples=_example_for(DocCreate)),
    db: Session = Depends(get_db),
) -> DocOut:
    return insert_document(payload, db)


@router.patch(
    "/revisions/{rev_id}/cancel",
    summary="Cancel a document revision.",
    description=(
        "Sets the canceled_date to the current datetime for the specified revision. "
        "Idempotent: if already canceled, returns the existing state. "
        "Cancellation is rejected for final revision statuses. "
        "Permissions: none enforced by API (auth TBD)."
    ),
    response_model=DocRevisionOut,
    tags=["documents"],
    responses=_REST_RESPONSES,
)
def cancel_revision(
    rev_id: int = Path(..., description="Revision ID to cancel", gt=0),
    db: Session = Depends(get_db),
) -> DocRevisionOut:
    """
    Cancel a document revision.

    Sets the cancelled_date to the current datetime for the specified revision.

    Args:
        rev_id: The revision ID to cancel.

    Returns:
        Updated document revision with cancelled_date set.

    Raises:
        HTTPException: 404 if revision not found.
    """
    try:
        rev_row = (
            db.execute(
                text("SELECT r.* FROM workflow.cancel_revision(:rev_id) AS r"),
                {"rev_id": rev_id},
            )
            .mappings()
            .one()
        )
        db.commit()
    except DBAPIError as err:
        db.rollback()
        _raise_for_dbapi_error(err, _CANCEL_REVISION_DB_ERROR_MAP)
    return _build_doc_revision_out_from_core_row(db, dict(rev_row))


@router.delete(
    "/{doc_id}",
    summary="Delete a document.",
    description=(
        "Deletes a document if it has only one revision with start status. "
        "Otherwise, sets the voided field to true. Returns a result indicating "
        "whether the document was deleted or voided. "
        "Permissions: none enforced by API (auth TBD)."
    ),
    response_model=DeleteResult,
    tags=["documents"],
    responses=_REST_RESPONSES,
)
def delete_document(
    doc_id: int = Path(..., description="Document ID to delete", gt=0),
    db: Session = Depends(get_db),
) -> DeleteResult:
    """
    Delete a document.

    If the document has only one revision with a status equal to the start status,
    the document is deleted (cascading to revisions). Otherwise, the document's
    voided field is set to true.

    Args:
        doc_id: The document ID to delete.

    Raises:
        HTTPException: 404 if document not found.
    """
    try:
        result = db.execute(
            text("SELECT workflow.delete_document(:doc_id)"),
            {"doc_id": doc_id},
        ).scalar_one()
        db.commit()
    except DBAPIError as err:
        db.rollback()
        _raise_for_dbapi_error(err, _DELETE_DOCUMENT_DB_ERROR_MAP)
    return DeleteResult(result=result)
