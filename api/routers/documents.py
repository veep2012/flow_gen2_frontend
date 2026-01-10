"""Documents endpoints for managing documents, revisions, milestones, and overviews."""

from typing import Any, TypeVar

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased, joinedload

from api.db.models import (
    Area,
    Discipline,
    Doc,
    DocRevision,
    DocRevMilestone,
    DocType,
    Jobpack,
    Project,
    RevisionOverview,
    Unit,
)
from api.schemas.documents import (
    DocOut,
    DocRevMilestoneCreate,
    DocRevMilestoneDelete,
    DocRevMilestoneOut,
    DocRevMilestoneUpdate,
    DocTypeCreate,
    DocTypeDelete,
    DocTypeOut,
    DocTypeUpdate,
    DocUpdate,
    RevisionOverviewCreate,
    RevisionOverviewDelete,
    RevisionOverviewOut,
    RevisionOverviewUpdate,
)
from api.utils.database import get_db
from api.utils.helpers import _example_for, _handle_integrity_error, _model_list, _model_out

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


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
def list_doc_types(db: Session = Depends(get_db)) -> list[DocTypeOut]:
    """
    List all document types.

    Returns a list of all document types sorted by document type name, including discipline
    information.

    Returns:
        List of document types with id, name, acronym, and associated discipline details.

    Raises:
        HTTPException: 404 if no document types are found.
    """
    doc_types = (
        db.query(DocType, Discipline)
        .join(Discipline, DocType.ref_discipline_id == Discipline.discipline_id)
        .order_by(DocType.doc_type_name)
        .all()
    )
    if not doc_types:
        raise HTTPException(status_code=404, detail="No doc types found")
    return [_build_doc_type_out(dt, disc) for dt, disc in doc_types]


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
    payload: DocTypeUpdate = Body(..., openapi_examples=_example_for(DocTypeUpdate)),
    db: Session = Depends(get_db),
) -> DocTypeOut:
    """
    Update an existing document type.

    Updates the name, acronym, and/or discipline reference of an existing document type.

    Args:
        payload: Document type update data including type_id and at least one field to update.

    Returns:
        Updated document type object.

    Raises:
        HTTPException: 400 if no fields provided or document type already exists.
        HTTPException: 404 if document type or referenced discipline not found.
    """
    if (
        payload.doc_type_name is None
        and payload.doc_type_acronym is None
        and payload.ref_discipline_id is None
    ):
        raise HTTPException(status_code=400, detail="No fields provided for update")

    doc_type = db.get(DocType, payload.type_id)
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


def delete_doc_type(
    payload: DocTypeDelete = Body(..., openapi_examples=_example_for(DocTypeDelete)),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a document type.

    Removes a document type from the database by its ID.

    Args:
        payload: Document type deletion data including type_id.

    Raises:
        HTTPException: 404 if document type not found.
    """
    doc_type = db.get(DocType, payload.type_id)
    if not doc_type:
        raise HTTPException(status_code=404, detail="Doc type not found")
    db.delete(doc_type)
    db.commit()


@router.get(
    "/list",
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
def list_documents_for_project(
    project_id: int = Query(..., description="Project ID to filter documents by"),
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

    Raises:
        HTTPException: 404 if no documents are found for the project.
    """
    rev_current = aliased(DocRevision)
    docs = (
        db.query(
            Doc, DocType, Discipline, Project, Jobpack, Area, Unit, rev_current, RevisionOverview
        )
        .join(DocType, Doc.type_id == DocType.type_id)
        .join(Discipline, DocType.ref_discipline_id == Discipline.discipline_id)
        .outerjoin(Project, Doc.project_id == Project.project_id)
        .outerjoin(Jobpack, Doc.jobpack_id == Jobpack.jobpack_id)
        .outerjoin(Area, Doc.area_id == Area.area_id)
        .outerjoin(Unit, Doc.unit_id == Unit.unit_id)
        .outerjoin(rev_current, Doc.rev_current_id == rev_current.rev_id)
        .outerjoin(RevisionOverview, rev_current.rev_code_id == RevisionOverview.rev_code_id)
        .filter(Doc.project_id == project_id)
        .order_by(Doc.doc_name_unique)
        .all()
    )
    if not docs:
        raise HTTPException(status_code=404, detail="No documents found for project")
    return [
        DocOut(
            doc_id=doc.doc_id,
            doc_name_unique=doc.doc_name_unique,
            title=doc.title,
            project_id=doc.project_id,
            project_name=project.project_name if project else None,
            jobpack_id=doc.jobpack_id,
            jobpack_name=jobpack.jobpack_name if jobpack else None,
            type_id=doc.type_id,
            doc_type_name=doc_type.doc_type_name,
            doc_type_acronym=doc_type.doc_type_acronym,
            area_id=doc.area_id,
            area_name=area.area_name,
            area_acronym=area.area_acronym,
            unit_id=doc.unit_id,
            unit_name=unit.unit_name,
            rev_actual_id=doc.rev_actual_id,
            rev_current_id=doc.rev_current_id,
            rev_seq_num=rev_current_row.seq_num if rev_current_row else None,
            discipline_id=discipline.discipline_id,
            discipline_name=discipline.discipline_name,
            discipline_acronym=discipline.discipline_acronym,
            rev_code_name=revision_overview.rev_code_name if revision_overview else None,
            rev_code_acronym=revision_overview.rev_code_acronym if revision_overview else None,
            percentage=revision_overview.percentage if revision_overview else None,
        )
        for (
            doc,
            doc_type,
            discipline,
            project,
            jobpack,
            area,
            unit,
            rev_current_row,
            revision_overview,
        ) in docs
    ]


def update_document(
    payload: DocUpdate = Body(..., openapi_examples=_example_for(DocUpdate)),
    db: Session = Depends(get_db),
) -> DocOut:
    """
    Update an existing document.

    Updates various fields of an existing document including name, title, project, jobpack, type,
    area, unit, and revision references. Validates all foreign key references and ensures document
    name uniqueness.

    Args:
        payload: Document update data including doc_id and at least one field to update.

    Returns:
        Updated document with complete metadata.

    Raises:
        HTTPException: 400 if no fields provided, required field is null, or
        document name not unique.
        HTTPException: 404 if document or any referenced entity not found.
    """
    updates = payload.model_dump(exclude_unset=True)
    updates.pop("doc_id", None)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    doc = db.get(Doc, payload.doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    T = TypeVar("T")

    def require_not_null(field_name: str, value: T | None) -> T:
        if value is None:
            raise HTTPException(status_code=400, detail=f"{field_name} cannot be null")
        return value

    if "doc_name_unique" in updates:
        doc.doc_name_unique = require_not_null("doc_name_unique", payload.doc_name_unique)

    if "title" in updates:
        doc.title = require_not_null("title", payload.title)

    project: Project | None = doc.project
    if "project_id" in updates:
        project_id = payload.project_id
        if project_id is not None:
            project = db.get(Project, project_id)
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
        else:
            project = None
        doc.project_id = project_id
        doc.project = project

    jobpack: Jobpack | None = doc.jobpack
    if "jobpack_id" in updates:
        jobpack_id = payload.jobpack_id
        if jobpack_id is not None:
            jobpack = db.get(Jobpack, jobpack_id)
            if not jobpack:
                raise HTTPException(status_code=404, detail="Jobpack not found")
        else:
            jobpack = None
        doc.jobpack_id = jobpack_id
        doc.jobpack = jobpack

    doc_type: DocType | None = doc.doc_type
    if "type_id" in updates:
        type_id = require_not_null("type_id", payload.type_id)
        doc_type = db.get(DocType, type_id)
        if not doc_type:
            raise HTTPException(status_code=404, detail="Doc type not found")
        doc.type_id = type_id
        doc.doc_type = doc_type

    area: Area | None = doc.area
    if "area_id" in updates:
        area_id = require_not_null("area_id", payload.area_id)
        area = db.get(Area, area_id)
        if not area:
            raise HTTPException(status_code=404, detail="Area not found")
        doc.area_id = area_id
        doc.area = area

    unit: Unit | None = doc.unit
    if "unit_id" in updates:
        unit_id = require_not_null("unit_id", payload.unit_id)
        unit = db.get(Unit, unit_id)
        if not unit:
            raise HTTPException(status_code=404, detail="Unit not found")
        doc.unit_id = unit_id
        doc.unit = unit

    if "rev_actual_id" in updates:
        rev_actual_id = payload.rev_actual_id
        if rev_actual_id is None:
            doc.rev_actual_id = None
            doc.actual_revision = None
        else:
            rev_actual = db.get(DocRevision, rev_actual_id)
            if not rev_actual:
                raise HTTPException(status_code=404, detail="Actual revision not found")
            if rev_actual.doc_id != doc.doc_id:
                raise HTTPException(
                    status_code=400,
                    detail="Actual revision does not belong to the document",
                )
            doc.rev_actual_id = rev_actual_id
            doc.actual_revision = rev_actual

    if "rev_current_id" in updates:
        rev_current_id = payload.rev_current_id
        if rev_current_id is None:
            doc.rev_current_id = None
            doc.current_revision = None
        else:
            rev_current_row = db.get(DocRevision, rev_current_id)
            if not rev_current_row:
                raise HTTPException(status_code=404, detail="Current revision not found")
            if rev_current_row.doc_id != doc.doc_id:
                raise HTTPException(
                    status_code=400,
                    detail="Current revision does not belong to the document",
                )
            doc.rev_current_id = rev_current_id
            doc.current_revision = rev_current_row

    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Document name must be unique", err, "update_document")

    doc_row = (
        db.query(Doc)
        .options(
            joinedload(Doc.doc_type).joinedload(DocType.discipline),
            joinedload(Doc.project),
            joinedload(Doc.jobpack),
            joinedload(Doc.area),
            joinedload(Doc.unit),
            joinedload(Doc.current_revision).joinedload(DocRevision.revision_overview),
        )
        .filter(Doc.doc_id == doc.doc_id)
        .one_or_none()
    )
    if not doc_row:
        raise HTTPException(status_code=404, detail="Document not found after update")

    doc_type = doc_row.doc_type
    discipline = doc_type.discipline if doc_type else None
    project = doc_row.project
    jobpack = doc_row.jobpack
    area = doc_row.area
    unit = doc_row.unit
    rev_current_row = doc_row.current_revision
    revision_overview = rev_current_row.revision_overview if rev_current_row else None

    return DocOut(
        doc_id=doc_row.doc_id,
        doc_name_unique=doc_row.doc_name_unique,
        title=doc_row.title,
        project_id=doc_row.project_id,
        project_name=project.project_name if project else None,
        jobpack_id=doc_row.jobpack_id,
        jobpack_name=jobpack.jobpack_name if jobpack else None,
        type_id=doc_row.type_id,
        doc_type_name=doc_type.doc_type_name if doc_type else None,
        doc_type_acronym=doc_type.doc_type_acronym if doc_type else None,
        area_id=doc_row.area_id,
        area_name=area.area_name if area else None,
        area_acronym=area.area_acronym if area else None,
        unit_id=doc_row.unit_id,
        unit_name=unit.unit_name if unit else None,
        rev_actual_id=doc_row.rev_actual_id,
        rev_current_id=doc_row.rev_current_id,
        rev_seq_num=rev_current_row.seq_num if rev_current_row else None,
        discipline_id=discipline.discipline_id if discipline else None,
        discipline_name=discipline.discipline_name if discipline else None,
        discipline_acronym=discipline.discipline_acronym if discipline else None,
        rev_code_name=revision_overview.rev_code_name if revision_overview else None,
        rev_code_acronym=revision_overview.rev_code_acronym if revision_overview else None,
        percentage=revision_overview.percentage if revision_overview else None,
    )


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
def list_doc_rev_milestones(db: Session = Depends(get_db)) -> list[DocRevMilestoneOut]:
    """
    List all document revision milestones.

    Returns a list of all document revision milestones sorted by milestone name.

    Returns:
        List of milestones with id, name, and progress percentage.

    Raises:
        HTTPException: 404 if no milestones are found.
    """
    milestones = db.query(DocRevMilestone).order_by(DocRevMilestone.milestone_name).all()
    if not milestones:
        raise HTTPException(status_code=404, detail="No milestones found")
    return _model_list(DocRevMilestoneOut, milestones)


def update_doc_rev_milestone(
    payload: DocRevMilestoneUpdate = Body(
        ..., openapi_examples=_example_for(DocRevMilestoneUpdate)
    ),
    db: Session = Depends(get_db),
) -> DocRevMilestoneOut:
    """
    Update an existing document revision milestone.

    Updates the name and/or progress percentage of an existing milestone.

    Args:
        payload: Milestone update data including milestone_id and at least one field to update.

    Returns:
        Updated milestone object.

    Raises:
        HTTPException: 400 if no fields provided or milestone name already exists.
        HTTPException: 404 if milestone not found.
    """
    if payload.milestone_name is None and payload.progress is None:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    milestone = db.get(DocRevMilestone, payload.milestone_id)
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


def delete_doc_rev_milestone(
    payload: DocRevMilestoneDelete = Body(
        ..., openapi_examples=_example_for(DocRevMilestoneDelete)
    ),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a document revision milestone.

    Removes a milestone from the database by its ID.

    Args:
        payload: Milestone deletion data including milestone_id.

    Raises:
        HTTPException: 404 if milestone not found.
    """
    milestone = db.get(DocRevMilestone, payload.milestone_id)
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    db.delete(milestone)
    db.commit()


@router.get(
    "/revision_overview",
    summary="List all revision overview entries.",
    description="Returns a list of all revision overview entries sorted by revision code name.",
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
def list_revision_overview(db: Session = Depends(get_db)) -> list[RevisionOverviewOut]:
    """
    List all revision overview entries.

    Returns a list of all revision overview entries sorted by revision code name.

    Returns:
        List of revision codes with id, name, acronym, description, and percentage.

    Raises:
        HTTPException: 404 if no revision overview entries are found.
    """
    revisions = db.query(RevisionOverview).order_by(RevisionOverview.rev_code_name).all()
    if not revisions:
        raise HTTPException(status_code=404, detail="No revision overview entries found")
    return _model_list(RevisionOverviewOut, revisions)


def update_revision_overview(
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
        payload: Revision overview update data including rev_code_id and at least
        one field to update.

    Returns:
        Updated revision overview object.

    Raises:
        HTTPException: 400 if no fields provided or revision overview already exists.
        HTTPException: 404 if revision overview entry not found.
    """
    if (
        payload.rev_code_name is None
        and payload.rev_code_acronym is None
        and payload.rev_description is None
        and payload.percentage is None
    ):
        raise HTTPException(status_code=400, detail="No fields provided for update")

    revision = db.get(RevisionOverview, payload.rev_code_id)
    if not revision:
        raise HTTPException(status_code=404, detail="Revision overview entry not found")

    if payload.rev_code_name is not None:
        revision.rev_code_name = payload.rev_code_name
    if payload.rev_code_acronym is not None:
        revision.rev_code_acronym = payload.rev_code_acronym
    if payload.rev_description is not None:
        revision.rev_description = payload.rev_description
    if payload.percentage is not None:
        revision.percentage = payload.percentage

    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error(
            "Revision overview entry already exists", err, "update_revision_overview"
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
        percentage=payload.percentage,
    )
    db.add(revision)
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error(
            "Revision overview entry already exists", err, "insert_revision_overview"
        )
    db.refresh(revision)
    return _model_out(RevisionOverviewOut, revision)


def delete_revision_overview(
    payload: RevisionOverviewDelete = Body(
        ..., openapi_examples=_example_for(RevisionOverviewDelete)
    ),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a revision overview entry.

    Removes a revision overview entry from the database by its ID.

    Args:
        payload: Revision overview deletion data including rev_code_id.

    Raises:
        HTTPException: 404 if revision overview entry not found.
    """
    revision = db.get(RevisionOverview, payload.rev_code_id)
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


@router.post(
    "/doc_types",
    summary="Create a new document type (REST).",
    description="Creates a new document type with the specified name and acronym.",
    response_model=DocTypeOut,
    status_code=201,
    tags=["documents"],
    responses=_REST_RESPONSES,
)
def create_doc_type_rest(
    payload: DocTypeCreate = Body(..., openapi_examples=_example_for(DocTypeCreate)),
    db: Session = Depends(get_db),
) -> DocTypeOut:
    return insert_doc_type(payload, db)


@router.put(
    "/doc_types/{type_id}",
    summary="Update an existing document type (REST).",
    description="Updates the name and/or acronym of an existing document type.",
    response_model=DocTypeOut,
    tags=["documents"],
    responses=_REST_RESPONSES,
)
def update_doc_type_rest(
    type_id: int,
    payload: DocTypeUpdate = Body(..., openapi_examples=_example_for(DocTypeUpdate)),
    db: Session = Depends(get_db),
) -> DocTypeOut:
    if payload.type_id != type_id:
        raise HTTPException(status_code=400, detail="type_id mismatch")
    return update_doc_type(payload, db)


@router.delete(
    "/doc_types/{type_id}",
    summary="Delete a document type (REST).",
    description="Removes a document type from the database by its ID.",
    status_code=204,
    tags=["documents"],
    responses=_REST_RESPONSES,
)
def delete_doc_type_rest(type_id: int, db: Session = Depends(get_db)) -> None:
    return delete_doc_type(DocTypeDelete(type_id=type_id), db)


@router.post(
    "/doc_rev_milestones",
    summary="Create a new document revision milestone (REST).",
    description="Creates a new document revision milestone with the specified name.",
    response_model=DocRevMilestoneOut,
    status_code=201,
    tags=["documents"],
    responses=_REST_RESPONSES,
)
def create_doc_rev_milestone_rest(
    payload: DocRevMilestoneCreate = Body(
        ..., openapi_examples=_example_for(DocRevMilestoneCreate)
    ),
    db: Session = Depends(get_db),
) -> DocRevMilestoneOut:
    return insert_doc_rev_milestone(payload, db)


@router.put(
    "/doc_rev_milestones/{milestone_id}",
    summary="Update an existing document revision milestone (REST).",
    description="Updates the name and/or progress of an existing milestone.",
    response_model=DocRevMilestoneOut,
    responses=_REST_RESPONSES,
)
def update_doc_rev_milestone_rest(
    milestone_id: int,
    payload: DocRevMilestoneUpdate = Body(
        ..., openapi_examples=_example_for(DocRevMilestoneUpdate)
    ),
    db: Session = Depends(get_db),
) -> DocRevMilestoneOut:
    if payload.milestone_id != milestone_id:
        raise HTTPException(status_code=400, detail="milestone_id mismatch")
    return update_doc_rev_milestone(payload, db)


@router.delete(
    "/doc_rev_milestones/{milestone_id}",
    summary="Delete a document revision milestone (REST).",
    description="Removes a document revision milestone by its ID.",
    status_code=204,
    responses=_REST_RESPONSES,
)
def delete_doc_rev_milestone_rest(milestone_id: int, db: Session = Depends(get_db)) -> None:
    return delete_doc_rev_milestone(DocRevMilestoneDelete(milestone_id=milestone_id), db)


@router.post(
    "/revision_overview",
    summary="Create a new revision overview entry (REST).",
    description="Creates a new revision overview entry with the specified details.",
    response_model=RevisionOverviewOut,
    status_code=201,
    tags=["documents"],
    responses=_REST_RESPONSES,
)
def create_revision_overview_rest(
    payload: RevisionOverviewCreate = Body(
        ..., openapi_examples=_example_for(RevisionOverviewCreate)
    ),
    db: Session = Depends(get_db),
) -> RevisionOverviewOut:
    return insert_revision_overview(payload, db)


@router.put(
    "/revision_overview/{rev_code_id}",
    summary="Update an existing revision overview entry (REST).",
    description="Updates the fields of an existing revision overview entry.",
    response_model=RevisionOverviewOut,
    responses=_REST_RESPONSES,
)
def update_revision_overview_rest(
    rev_code_id: int,
    payload: RevisionOverviewUpdate = Body(
        ..., openapi_examples=_example_for(RevisionOverviewUpdate)
    ),
    db: Session = Depends(get_db),
) -> RevisionOverviewOut:
    if payload.rev_code_id != rev_code_id:
        raise HTTPException(status_code=400, detail="rev_code_id mismatch")
    return update_revision_overview(payload, db)


@router.delete(
    "/revision_overview/{rev_code_id}",
    summary="Delete a revision overview entry (REST).",
    description="Removes a revision overview entry by its ID.",
    status_code=204,
    responses=_REST_RESPONSES,
)
def delete_revision_overview_rest(rev_code_id: int, db: Session = Depends(get_db)) -> None:
    return delete_revision_overview(RevisionOverviewDelete(rev_code_id=rev_code_id), db)


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
    if payload.doc_id != doc_id:
        raise HTTPException(status_code=400, detail="doc_id mismatch")
    return update_document(payload, db)
