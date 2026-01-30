"""Lookups endpoints for areas, disciplines, projects, units, jobpacks, roles, and doc types."""

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.db.models import (
    Area,
    Discipline,
    DocRevStatus,
    DocRevStatusUiBehavior,
    Jobpack,
    Project,
    Unit,
)
from api.schemas.documents import (
    DocRevStatusCreate,
    DocRevStatusOut,
    DocRevStatusUiBehaviorCreate,
    DocRevStatusUiBehaviorOut,
    DocRevStatusUiBehaviorUpdate,
    DocRevStatusUpdate,
)
from api.schemas.lookups import (
    AreaCreate,
    AreaOut,
    AreaUpdate,
    DisciplineCreate,
    DisciplineOut,
    DisciplineUpdate,
    JobpackCreate,
    JobpackOut,
    JobpackUpdate,
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
    UnitCreate,
    UnitOut,
    UnitUpdate,
)
from api.utils.database import get_db
from api.utils.helpers import _example_for, _handle_integrity_error, _model_list, _model_out

router = APIRouter(prefix="/api/v1/lookups", tags=["lookups"])


@router.get(
    "/areas",
    summary="List all areas.",
    description="Returns a list of all areas sorted by area name.",
    operation_id="list_areas",
    tags=["lookups"],
    response_model=list[AreaOut],
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
def list_areas(db: Session = Depends(get_db)) -> list[AreaOut]:
    """
    List all areas.

    Returns a list of all areas sorted by area name.

    Returns:
        List of areas with id, name, and acronym.

    """
    rows = db.execute(
        text(
            """
            SELECT area_id, area_name, area_acronym
            FROM workflow.areas
            ORDER BY area_name
            """
        )
    ).mappings()
    return _model_list(AreaOut, rows.all())


def update_area(
    area_id: int,
    payload: AreaUpdate = Body(..., openapi_examples=_example_for(AreaUpdate)),
    db: Session = Depends(get_db),
) -> AreaOut:
    """
    Update an existing area.

    Updates the name and/or acronym of an existing area.

    Args:
        area_id: Area ID to update.
        payload: Area update data including at least one field to update.

    Returns:
        Updated area object.

    Raises:
        HTTPException: 400 if no fields provided or name/acronym already exists.
        HTTPException: 404 if area not found.
    """
    if payload.area_name is None and payload.area_acronym is None:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    area = db.get(Area, area_id)
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")

    if payload.area_name is not None:
        area.area_name = payload.area_name
    if payload.area_acronym is not None:
        area.area_acronym = payload.area_acronym

    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Area name or acronym already exists", err, "update_area")

    db.refresh(area)
    return _model_out(AreaOut, area)


def insert_area(
    payload: AreaCreate = Body(..., openapi_examples=_example_for(AreaCreate)),
    db: Session = Depends(get_db),
) -> AreaOut:
    """
    Create a new area.

    Inserts a new area with the specified name and acronym.

    Args:
        payload: Area creation data including name and acronym.

    Returns:
        Newly created area object.

    Raises:
        HTTPException: 400 if area name or acronym already exists.
    """
    area = Area(area_name=payload.area_name, area_acronym=payload.area_acronym)
    db.add(area)
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Area name or acronym already exists", err, "insert_area")
    db.refresh(area)
    return _model_out(AreaOut, area)


def delete_area(area_id: int, db: Session = Depends(get_db)) -> None:
    """
    Delete an area.

    Removes an area from the database by its ID.

    Args:
        area_id: Area ID to delete.

    Raises:
        HTTPException: 404 if area not found.
    """
    area = db.get(Area, area_id)
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")
    db.delete(area)
    db.commit()


@router.get(
    "/disciplines",
    summary="List all disciplines.",
    description="Returns a list of all disciplines sorted by discipline name.",
    operation_id="list_disciplines",
    tags=["lookups"],
    response_model=list[DisciplineOut],
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
def list_disciplines(db: Session = Depends(get_db)) -> list[DisciplineOut]:
    """
    List all disciplines.

    Returns a list of all disciplines sorted by discipline name.

    Returns:
        List of disciplines with id, name, and acronym.
    """
    rows = db.execute(
        text(
            """
            SELECT discipline_id, discipline_name, discipline_acronym
            FROM workflow.disciplines
            ORDER BY discipline_name
            """
        )
    ).mappings()
    return _model_list(DisciplineOut, rows.all())


def update_discipline(
    discipline_id: int,
    payload: DisciplineUpdate = Body(..., openapi_examples=_example_for(DisciplineUpdate)),
    db: Session = Depends(get_db),
) -> DisciplineOut:
    """
    Update an existing discipline.

    Updates the name and/or acronym of an existing discipline.

    Args:
        discipline_id: Discipline ID to update.
        payload: Discipline update data including at least one field to update.

    Returns:
        Updated discipline object.

    Raises:
        HTTPException: 400 if no fields provided or name/acronym already exists.
        HTTPException: 404 if discipline not found.
    """
    if payload.discipline_name is None and payload.discipline_acronym is None:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    discipline = db.get(Discipline, discipline_id)
    if not discipline:
        raise HTTPException(status_code=404, detail="Discipline not found")

    if payload.discipline_name is not None:
        discipline.discipline_name = payload.discipline_name
    if payload.discipline_acronym is not None:
        discipline.discipline_acronym = payload.discipline_acronym

    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error(
            "Discipline name or acronym already exists",
            err,
            "update_discipline",
        )

    db.refresh(discipline)
    return _model_out(DisciplineOut, discipline)


def insert_discipline(
    payload: DisciplineCreate = Body(..., openapi_examples=_example_for(DisciplineCreate)),
    db: Session = Depends(get_db),
) -> DisciplineOut:
    """
    Create a new discipline.

    Inserts a new discipline with the specified name and acronym.

    Args:
        payload: Discipline creation data including name and acronym.

    Returns:
        Newly created discipline object.

    Raises:
        HTTPException: 400 if discipline name or acronym already exists.
    """
    discipline = Discipline(
        discipline_name=payload.discipline_name,
        discipline_acronym=payload.discipline_acronym,
    )
    db.add(discipline)
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error(
            "Discipline name or acronym already exists",
            err,
            "insert_discipline",
        )
    db.refresh(discipline)
    return _model_out(DisciplineOut, discipline)


def delete_discipline(discipline_id: int, db: Session = Depends(get_db)) -> None:
    """
    Delete a discipline.

    Removes a discipline from the database by its ID.

    Args:
        discipline_id: Discipline ID to delete.

    Raises:
        HTTPException: 404 if discipline not found.
    """
    discipline = db.get(Discipline, discipline_id)
    if not discipline:
        raise HTTPException(status_code=404, detail="Discipline not found")
    db.delete(discipline)
    db.commit()


@router.get(
    "/projects",
    summary="List all projects.",
    description="Returns a list of all projects sorted by project name.",
    operation_id="list_projects",
    tags=["lookups"],
    response_model=list[ProjectOut],
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
def list_projects(db: Session = Depends(get_db)) -> list[ProjectOut]:
    """
    List all projects.

    Returns a list of all projects sorted by project name.

    Returns:
        List of projects with id and name.
    """
    rows = db.execute(
        text(
            """
            SELECT project_id, project_name
            FROM workflow.projects
            ORDER BY project_name
            """
        )
    ).mappings()
    return _model_list(ProjectOut, rows.all())


def update_project(
    project_id: int,
    payload: ProjectUpdate = Body(..., openapi_examples=_example_for(ProjectUpdate)),
    db: Session = Depends(get_db),
) -> ProjectOut:
    """
    Update an existing project.

    Updates the name of an existing project.

    Args:
        project_id: Project ID to update.
        payload: Project update data including new project_name.

    Returns:
        Updated project object.

    Raises:
        HTTPException: 400 if no fields provided or project name already exists.
        HTTPException: 404 if project not found.
    """
    if payload.project_name is None:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if payload.project_name is not None:
        project.project_name = payload.project_name

    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Project name already exists", err, "update_project")

    db.refresh(project)
    return _model_out(ProjectOut, project)


def insert_project(
    payload: ProjectCreate = Body(..., openapi_examples=_example_for(ProjectCreate)),
    db: Session = Depends(get_db),
) -> ProjectOut:
    """
    Create a new project.

    Inserts a new project with the specified name.

    Args:
        payload: Project creation data including project_name.

    Returns:
        Newly created project object.

    Raises:
        HTTPException: 400 if project name already exists.
    """
    project = Project(project_name=payload.project_name)
    db.add(project)
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Project name already exists", err, "insert_project")
    db.refresh(project)
    return _model_out(ProjectOut, project)


def delete_project(project_id: int, db: Session = Depends(get_db)) -> None:
    """
    Delete a project.

    Removes a project from the database by its ID.

    Args:
        project_id: Project ID to delete.

    Raises:
        HTTPException: 404 if project not found.
    """
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()


@router.get(
    "/units",
    summary="List all units.",
    description="Returns a list of all units sorted by unit name.",
    operation_id="list_units",
    tags=["lookups"],
    response_model=list[UnitOut],
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
def list_units(db: Session = Depends(get_db)) -> list[UnitOut]:
    """
    List all units.

    Returns a list of all units sorted by unit name.

    Returns:
        List of units with id and name.
    """
    rows = db.execute(
        text(
            """
            SELECT unit_id, unit_name
            FROM workflow.units
            ORDER BY unit_name
            """
        )
    ).mappings()
    return _model_list(UnitOut, rows.all())


def update_unit(
    unit_id: int,
    payload: UnitUpdate = Body(..., openapi_examples=_example_for(UnitUpdate)),
    db: Session = Depends(get_db),
) -> UnitOut:
    """
    Update an existing unit.

    Updates the name of an existing unit.

    Args:
        unit_id: Unit ID to update.
        payload: Unit update data including new unit_name.

    Returns:
        Updated unit object.

    Raises:
        HTTPException: 400 if no fields provided or unit name already exists.
        HTTPException: 404 if unit not found.
    """
    if payload.unit_name is None:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    unit = db.get(Unit, unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    if payload.unit_name is not None:
        unit.unit_name = payload.unit_name

    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Unit name already exists", err, "update_unit")

    db.refresh(unit)
    return _model_out(UnitOut, unit)


def insert_unit(
    payload: UnitCreate = Body(..., openapi_examples=_example_for(UnitCreate)),
    db: Session = Depends(get_db),
) -> UnitOut:
    """
    Create a new unit.

    Inserts a new unit with the specified name.

    Args:
        payload: Unit creation data including unit_name.

    Returns:
        Newly created unit object.

    Raises:
        HTTPException: 400 if unit name already exists.
    """
    unit = Unit(unit_name=payload.unit_name)
    db.add(unit)
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Unit name already exists", err, "insert_unit")
    db.refresh(unit)
    return _model_out(UnitOut, unit)


def delete_unit(unit_id: int, db: Session = Depends(get_db)) -> None:
    """
    Delete a unit.

    Removes a unit from the database by its ID.

    Args:
        unit_id: Unit ID to delete.

    Raises:
        HTTPException: 404 if unit not found.
    """
    unit = db.get(Unit, unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    db.delete(unit)
    db.commit()


@router.get(
    "/jobpacks",
    summary="List all jobpacks.",
    description="Returns a list of all jobpacks sorted by jobpack name.",
    operation_id="list_jobpacks",
    tags=["lookups"],
    response_model=list[JobpackOut],
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
def list_jobpacks(db: Session = Depends(get_db)) -> list[JobpackOut]:
    """
    List all jobpacks.

    Returns a list of all jobpacks sorted by jobpack name.

    Returns:
        List of jobpacks with id and name.
    """
    rows = db.execute(
        text(
            """
            SELECT jobpack_id, jobpack_name
            FROM workflow.jobpacks
            ORDER BY jobpack_name
            """
        )
    ).mappings()
    return _model_list(JobpackOut, rows.all())


def update_jobpack(
    jobpack_id: int,
    payload: JobpackUpdate = Body(..., openapi_examples=_example_for(JobpackUpdate)),
    db: Session = Depends(get_db),
) -> JobpackOut:
    """
    Update an existing jobpack.

    Updates the name of an existing jobpack.

    Args:
        jobpack_id: Jobpack ID to update.
        payload: Jobpack update data including new jobpack_name.

    Returns:
        Updated jobpack object.

    Raises:
        HTTPException: 400 if no fields provided or jobpack name already exists.
        HTTPException: 404 if jobpack not found.
    """
    if payload.jobpack_name is None:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    jobpack = db.get(Jobpack, jobpack_id)
    if not jobpack:
        raise HTTPException(status_code=404, detail="Jobpack not found")

    jobpack.jobpack_name = payload.jobpack_name or jobpack.jobpack_name

    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Jobpack name already exists", err, "update_jobpack")

    db.refresh(jobpack)
    return _model_out(JobpackOut, jobpack)


def insert_jobpack(
    payload: JobpackCreate = Body(..., openapi_examples=_example_for(JobpackCreate)),
    db: Session = Depends(get_db),
) -> JobpackOut:
    """
    Create a new jobpack.

    Inserts a new jobpack with the specified name.

    Args:
        payload: Jobpack creation data including jobpack_name.

    Returns:
        Newly created jobpack object.

    Raises:
        HTTPException: 400 if jobpack name already exists.
    """
    jobpack = Jobpack(jobpack_name=payload.jobpack_name)
    db.add(jobpack)
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Jobpack name already exists", err, "insert_jobpack")
    db.refresh(jobpack)
    return _model_out(JobpackOut, jobpack)


def delete_jobpack(jobpack_id: int, db: Session = Depends(get_db)) -> None:
    """
    Delete a jobpack.

    Removes a jobpack from the database by its ID.

    Args:
        jobpack_id: Jobpack ID to delete.

    Raises:
        HTTPException: 404 if jobpack not found.
    """
    jobpack = db.get(Jobpack, jobpack_id)
    if not jobpack:
        raise HTTPException(status_code=404, detail="Jobpack not found")
    db.delete(jobpack)
    db.commit()


@router.get(
    "/doc_rev_status_ui_behaviors",
    summary="List all document revision status UI behaviors.",
    description="Returns a list of all document revision status UI behaviors sorted by name.",
    operation_id="list_doc_rev_status_ui_behaviors",
    tags=["lookups"],
    response_model=list[DocRevStatusUiBehaviorOut],
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
def list_doc_rev_status_ui_behaviors(
    db: Session = Depends(get_db),
) -> list[DocRevStatusUiBehaviorOut]:
    """
    List all document revision status UI behaviors.

    Returns:
        List of document revision status UI behaviors with id and name.
    """
    rows = db.execute(
        text(
            """
            SELECT ui_behavior_id, ui_behavior_name, ui_behavior_file
            FROM workflow.doc_rev_status_ui_behaviors
            ORDER BY ui_behavior_name
            """
        )
    ).mappings()
    return _model_list(DocRevStatusUiBehaviorOut, rows.all())


def insert_doc_rev_status_ui_behavior(
    payload: DocRevStatusUiBehaviorCreate = Body(
        ..., openapi_examples=_example_for(DocRevStatusUiBehaviorCreate)
    ),
    db: Session = Depends(get_db),
) -> DocRevStatusUiBehaviorOut:
    """
    Create a new document revision status UI behavior.

    Args:
        payload: UI behavior creation data including name.

    Returns:
        Newly created UI behavior object.

    Raises:
        HTTPException: 400 on creation failure.
    """
    behavior = DocRevStatusUiBehavior(
        ui_behavior_name=payload.ui_behavior_name,
        ui_behavior_file=payload.ui_behavior_file,
    )
    db.add(behavior)
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error(
            "Revision status UI behavior already exists", err, "insert_doc_rev_status_ui_behavior"
        )

    db.refresh(behavior)
    return _model_out(DocRevStatusUiBehaviorOut, behavior)


def update_doc_rev_status_ui_behavior(
    ui_behavior_id: int,
    payload: DocRevStatusUiBehaviorUpdate = Body(
        ..., openapi_examples=_example_for(DocRevStatusUiBehaviorUpdate)
    ),
    db: Session = Depends(get_db),
) -> DocRevStatusUiBehaviorOut:
    """
    Update an existing document revision status UI behavior.

    Args:
        ui_behavior_id: UI behavior ID to update.
        payload: UI behavior update data including name.

    Returns:
        Updated UI behavior object.

    Raises:
        HTTPException: 400 if no fields provided.
        HTTPException: 404 if UI behavior not found.
    """
    if payload.ui_behavior_name is None and payload.ui_behavior_file is None:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    behavior = db.get(DocRevStatusUiBehavior, ui_behavior_id)
    if not behavior:
        raise HTTPException(status_code=404, detail="Revision status UI behavior not found")

    if payload.ui_behavior_name is not None:
        behavior.ui_behavior_name = payload.ui_behavior_name
    if payload.ui_behavior_file is not None:
        behavior.ui_behavior_file = payload.ui_behavior_file
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error(
            "Revision status UI behavior already exists", err, "update_doc_rev_status_ui_behavior"
        )

    db.refresh(behavior)
    return _model_out(DocRevStatusUiBehaviorOut, behavior)


def delete_doc_rev_status_ui_behavior(ui_behavior_id: int, db: Session = Depends(get_db)) -> None:
    """
    Delete a document revision status UI behavior.

    Args:
        ui_behavior_id: UI behavior ID to delete.

    Raises:
        HTTPException: 404 if UI behavior not found.
    """
    behavior = db.get(DocRevStatusUiBehavior, ui_behavior_id)
    if not behavior:
        raise HTTPException(status_code=404, detail="Revision status UI behavior not found")
    db.delete(behavior)
    db.commit()


@router.get(
    "/doc_rev_statuses",
    summary="List all document revision statuses.",
    description="Returns a list of all document revision statuses sorted by name.",
    operation_id="list_doc_rev_statuses",
    tags=["lookups"],
    response_model=list[DocRevStatusOut],
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
def list_doc_rev_statuses(db: Session = Depends(get_db)) -> list[DocRevStatusOut]:
    """
    List all document revision statuses.

    Returns a list of all document revision statuses sorted by name.

    Returns:
        List of document revision statuses with id and name.
    """
    rows = db.execute(
        text(
            """
            SELECT rev_status_id,
                   rev_status_name,
                   ui_behavior_id,
                   next_rev_status_id,
                   revertible,
                   editable,
                   final,
                   start
            FROM workflow.doc_rev_statuses
            ORDER BY rev_status_name
            """
        )
    ).mappings()
    return _model_list(DocRevStatusOut, rows.all())


def insert_doc_rev_status(
    payload: DocRevStatusCreate = Body(..., openapi_examples=_example_for(DocRevStatusCreate)),
    db: Session = Depends(get_db),
) -> DocRevStatusOut:
    """
    Create a new document revision status.

    Inserts a new document revision status with the specified name.

    Args:
        payload: Document revision status creation data including name.

    Returns:
        Newly created document revision status object.

    Raises:
        HTTPException: 400 on creation failure.
    """
    if payload.final and payload.next_rev_status_id is not None:
        raise HTTPException(status_code=400, detail="Final status cannot have next status")
    if not payload.final and payload.next_rev_status_id is None:
        raise HTTPException(status_code=400, detail="Non-final status must have next status")
    if payload.final and ((payload.editable is True) or (payload.revertible is True)):
        raise HTTPException(
            status_code=400,
            detail="Final status cannot be editable or revertible",
        )
    if payload.start:
        existing_start = db.query(DocRevStatus).filter(DocRevStatus.start.is_(True)).first()
        if existing_start is not None:
            raise HTTPException(status_code=400, detail="Start status already exists")
    if payload.final:
        existing_final = db.query(DocRevStatus).filter(DocRevStatus.final.is_(True)).first()
        if existing_final is not None:
            raise HTTPException(status_code=400, detail="Final status already exists")

    status_fields = {
        "rev_status_name": payload.rev_status_name,
        "ui_behavior_id": payload.ui_behavior_id,
        "next_rev_status_id": payload.next_rev_status_id,
        "final": payload.final,
    }
    if payload.revertible is not None:
        status_fields["revertible"] = payload.revertible
    if payload.editable is not None:
        status_fields["editable"] = payload.editable
    if payload.start is not None:
        status_fields["start"] = payload.start

    status = DocRevStatus(**status_fields)
    db.add(status)
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Revision status already exists", err, "insert_doc_rev_status")

    db.refresh(status)
    return _model_out(DocRevStatusOut, status)


def update_doc_rev_status(
    rev_status_id: int,
    payload: DocRevStatusUpdate = Body(..., openapi_examples=_example_for(DocRevStatusUpdate)),
    db: Session = Depends(get_db),
) -> DocRevStatusOut:
    """
    Update an existing document revision status.

    Updates the name of an existing document revision status.

    Args:
        rev_status_id: Revision status ID to update.
        payload: Document revision status update data including rev_status_name.

    Returns:
        Updated document revision status object.

    Raises:
        HTTPException: 400 if no fields provided.
        HTTPException: 404 if status not found.
    """
    update_fields = {
        "rev_status_name",
        "ui_behavior_id",
        "next_rev_status_id",
        "revertible",
        "editable",
        "final",
        "start",
    }
    if not update_fields.intersection(payload.model_fields_set):
        raise HTTPException(status_code=400, detail="No fields provided for update")

    status = db.get(DocRevStatus, rev_status_id)
    if not status:
        raise HTTPException(status_code=404, detail="Revision status not found")

    if "rev_status_name" in payload.model_fields_set and payload.rev_status_name is None:
        raise HTTPException(status_code=400, detail="Revision status name cannot be null")
    if "ui_behavior_id" in payload.model_fields_set and payload.ui_behavior_id is None:
        raise HTTPException(status_code=400, detail="UI behavior ID cannot be null")
    if "revertible" in payload.model_fields_set and payload.revertible is None:
        raise HTTPException(status_code=400, detail="Revertible flag cannot be null")
    if "editable" in payload.model_fields_set and payload.editable is None:
        raise HTTPException(status_code=400, detail="Editable flag cannot be null")
    if "final" in payload.model_fields_set and payload.final is None:
        raise HTTPException(status_code=400, detail="Final flag cannot be null")
    if "start" in payload.model_fields_set and payload.start is None:
        raise HTTPException(status_code=400, detail="Start flag cannot be null")

    next_final = status.final
    next_next_id = status.next_rev_status_id
    next_editable = status.editable
    next_revertible = status.revertible
    next_start = status.start
    if "final" in payload.model_fields_set:
        assert payload.final is not None
        next_final = payload.final
    if "next_rev_status_id" in payload.model_fields_set:
        next_next_id = payload.next_rev_status_id
    if "editable" in payload.model_fields_set:
        assert payload.editable is not None
        next_editable = payload.editable
    if "revertible" in payload.model_fields_set:
        assert payload.revertible is not None
        next_revertible = payload.revertible
    if "start" in payload.model_fields_set:
        assert payload.start is not None
        next_start = payload.start

    if next_final and next_next_id is not None:
        raise HTTPException(status_code=400, detail="Final status cannot have next status")
    if not next_final and next_next_id is None:
        raise HTTPException(status_code=400, detail="Non-final status must have next status")
    if next_final and (next_editable or next_revertible):
        raise HTTPException(
            status_code=400, detail="Final status must not be editable or revertible"
        )
    if next_start:
        existing_start = (
            db.query(DocRevStatus)
            .filter(
                DocRevStatus.start.is_(True),
                DocRevStatus.rev_status_id != status.rev_status_id,
            )
            .first()
        )
        if existing_start is not None:
            raise HTTPException(status_code=400, detail="Start status already exists")
    if next_start:
        existing_start = (
            db.query(DocRevStatus)
            .filter(
                DocRevStatus.start.is_(True),
                DocRevStatus.rev_status_id != status.rev_status_id,
            )
            .first()
        )
        if existing_start is not None:
            raise HTTPException(status_code=400, detail="Start status already exists")
    if next_final:
        existing_final = (
            db.query(DocRevStatus)
            .filter(
                DocRevStatus.final.is_(True),
                DocRevStatus.rev_status_id != status.rev_status_id,
            )
            .first()
        )
        if existing_final is not None:
            raise HTTPException(status_code=400, detail="Final status already exists")

    if "rev_status_name" in payload.model_fields_set:
        assert payload.rev_status_name is not None
        status.rev_status_name = payload.rev_status_name
    if "ui_behavior_id" in payload.model_fields_set:
        assert payload.ui_behavior_id is not None
        status.ui_behavior_id = payload.ui_behavior_id
    if "next_rev_status_id" in payload.model_fields_set:
        status.next_rev_status_id = payload.next_rev_status_id
    if "revertible" in payload.model_fields_set:
        assert payload.revertible is not None
        status.revertible = payload.revertible
    if "editable" in payload.model_fields_set:
        assert payload.editable is not None
        status.editable = payload.editable
    if "final" in payload.model_fields_set:
        assert payload.final is not None
        status.final = payload.final
    if "start" in payload.model_fields_set:
        assert payload.start is not None
        status.start = payload.start
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Revision status already exists", err, "update_doc_rev_status")

    db.refresh(status)
    return _model_out(DocRevStatusOut, status)


def delete_doc_rev_status(rev_status_id: int, db: Session = Depends(get_db)) -> None:
    """
    Delete a document revision status.

    Removes a document revision status from the database by its ID.

    Args:
        rev_status_id: Revision status ID to delete.

    Raises:
        HTTPException: 404 if status not found.
    """
    status = db.get(DocRevStatus, rev_status_id)
    if not status:
        raise HTTPException(status_code=404, detail="Revision status not found")
    db.delete(status)
    db.commit()
