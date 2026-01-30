"""Distribution Lists endpoints for managing distribution lists and recipients."""

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from api.db.models import DistributionList, DistributionListContent, Doc, Project
from api.schemas.distribution_lists import SendForReviewRequest
from api.utils.database import get_db
from api.utils.helpers import _example_for

router = APIRouter(prefix="/api/v1/documents", tags=["distribution-lists"])


def _get_doc_and_project(doc_id: int, db: Session) -> tuple[Doc, Project]:
    """Helper to get document and its associated project."""
    doc = db.get(Doc, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not doc.project_id:
        raise HTTPException(status_code=404, detail="Document is not associated with a project")
    project = db.get(Project, doc.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return doc, project


@router.get(
    "/{doc_id}/distribution-lists",
    summary="Get all distribution lists for a document",
    description="Returns all distribution lists associated with the document's project",
    response_model=list[dict],
    responses={
        404: {"description": "Document or project not found"},
        500: {"description": "Internal Server Error"},
    },
)
def get_distribution_lists(doc_id: int, db: Session = Depends(get_db)):
    """Get all distribution lists for a document."""
    doc, project = _get_doc_and_project(doc_id, db)

    lists = (
        db.query(DistributionList).filter(DistributionList.project_id == project.project_id).all()
    )

    return [
        {
            "dist_id": lst.dist_id,
            "dist_list_id": lst.dist_id,
            "distribution_list_name": lst.distribution_list_name,
            "list_name": lst.distribution_list_name,
            "project_id": lst.project_id,
        }
        for lst in (lists or [])
    ]


@router.get(
    "/{doc_id}/distribution-lists/{list_id}/recipients",
    summary="Get all recipients in a distribution list",
    description="Returns all recipients in the specified distribution list",
    response_model=list[dict],
    responses={
        404: {"description": "Document, project, or list not found"},
        500: {"description": "Internal Server Error"},
    },
)
def get_distribution_list_recipients(doc_id: int, list_id: int, db: Session = Depends(get_db)):
    """Get all recipients in a distribution list."""
    doc, project = _get_doc_and_project(doc_id, db)

    dist_list = db.get(DistributionList, list_id)
    if not dist_list or dist_list.project_id != project.project_id:
        raise HTTPException(status_code=404, detail="Distribution list not found")

    content = (
        db.query(DistributionListContent)
        .filter(DistributionListContent.dist_id == list_id)
        .options(joinedload(DistributionListContent.person))
        .all()
    )

    return [
        {
            "person_id": c.person_id,
            "person_name": c.person.person_name,
        }
        for c in content
    ]


@router.post(
    "/{doc_id}/distribution-lists/{list_id}/send-for-review",
    summary="Send document for review",
    description="Sends document to recipients in the distribution list for review",
    response_model=dict,
    status_code=201,
    responses={
        400: {"description": "Bad Request"},
        404: {"description": "Document, project, or list not found"},
        500: {"description": "Internal Server Error"},
    },
)
def send_for_review(
    doc_id: int,
    list_id: int,
    payload: SendForReviewRequest = Body(..., openapi_examples=_example_for(SendForReviewRequest)),
    db: Session = Depends(get_db),
):
    """Send document for review to distribution list recipients."""
    doc, project = _get_doc_and_project(doc_id, db)

    dist_list = db.get(DistributionList, list_id)
    if not dist_list or dist_list.project_id != project.project_id:
        raise HTTPException(status_code=404, detail="Distribution list not found")

    # Validate that recipients are provided
    if not payload.recipients:
        raise HTTPException(status_code=400, detail="At least one recipient must be specified")

    # Validate that all requested recipients belong to this distribution list
    requested_recipient_ids = set(payload.recipients)
    contents = (
        db.query(DistributionListContent)
        .filter(
            DistributionListContent.dist_id == list_id,
            DistributionListContent.person_id.in_(requested_recipient_ids),
        )
        .all()
    )

    valid_recipient_ids = {content.person_id for content in contents}

    if not valid_recipient_ids:
        raise HTTPException(
            status_code=400,
            detail="No valid recipients found for the specified distribution list",
        )

    if valid_recipient_ids != requested_recipient_ids:
        raise HTTPException(
            status_code=400,
            detail="One or more recipients are not part of the specified distribution list",
        )

    # TODO: Implement actual email sending logic for validated recipients
    # For now, just return success with validated recipients
    return {
        "message": "Document sent for review",
        "doc_id": doc_id,
        "list_id": list_id,
        "recipients": list(valid_recipient_ids),
    }
