"""Lookups endpoints for areas, disciplines, projects, units, jobpacks, roles, and doc types."""

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.db.models import Area, Discipline, DocRevStatus, Jobpack, Project, Unit
from api.schemas.documents import (
    DocRevStatusCreate,
    DocRevStatusDelete,
    DocRevStatusOut,
    DocRevStatusUpdate,
)
from api.schemas.lookups import (
    AreaCreate,
    AreaDelete,
    AreaOut,
    AreaUpdate,
    DisciplineCreate,
    DisciplineDelete,
    DisciplineOut,
    DisciplineUpdate,
    JobpackCreate,
    JobpackDelete,
    JobpackOut,
    JobpackUpdate,
    ProjectCreate,
    ProjectDelete,
    ProjectOut,
    ProjectUpdate,
    UnitCreate,
    UnitDelete,
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
def list_areas(db: Session = Depends(get_db)) -> list[AreaOut]:
    """
    List all areas.

    Returns a list of all areas sorted by area name.

    Returns:
        List of areas with id, name, and acronym.

    Notes:
        Unlike some other list endpoints, this endpoint intentionally returns an empty list
        with HTTP 200 when no areas exist, rather than raising a 404. This behavior is
        preserved for lookup consistency and backward compatibility.
    """
    areas = db.query(Area).order_by(Area.area_name).all()
    return _model_list(AreaOut, areas)


@router.put(
    "/areas/update",
    summary="Update an existing area.",
    description="Updates the name and/or acronym of an existing area.",
    operation_id="update_area",
    tags=["lookups"],
    response_model=AreaOut,
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
def update_area(
    payload: AreaUpdate = Body(..., examples=_example_for(AreaUpdate)),
    db: Session = Depends(get_db),
) -> AreaOut:
    """
    Update an existing area.

    Updates the name and/or acronym of an existing area.

    Args:
        payload: Area update data including area_id and at least one field to update.

    Returns:
        Updated area object.

    Raises:
        HTTPException: 400 if no fields provided or name/acronym already exists.
        HTTPException: 404 if area not found.
    """
    if payload.area_name is None and payload.area_acronym is None:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    area = db.get(Area, payload.area_id)
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


@router.post(
    "/areas/insert",
    summary="Create a new area.",
    description="Inserts a new area with the specified name and acronym.",
    operation_id="insert_area",
    tags=["lookups"],
    response_model=AreaOut,
    status_code=201,
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
def insert_area(
    payload: AreaCreate = Body(..., examples=_example_for(AreaCreate)),
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


@router.delete(
    "/areas/delete",
    summary="Delete an area.",
    description="Removes an area from the database by its ID.",
    operation_id="delete_area",
    tags=["lookups"],
    status_code=204,
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
def delete_area(
    payload: AreaDelete = Body(..., examples=_example_for(AreaDelete)),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete an area.

    Removes an area from the database by its ID.

    Args:
        payload: Area deletion data including area_id.

    Raises:
        HTTPException: 404 if area not found.
    """
    area = db.get(Area, payload.area_id)
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
def list_disciplines(db: Session = Depends(get_db)) -> list[DisciplineOut]:
    """
    List all disciplines.

    Returns a list of all disciplines sorted by discipline name.

    Returns:
        List of disciplines with id, name, and acronym.

    Raises:
        HTTPException: 404 if no disciplines are found.
    """
    disciplines = db.query(Discipline).order_by(Discipline.discipline_name).all()
    if not disciplines:
        raise HTTPException(status_code=404, detail="No disciplines found")
    return _model_list(DisciplineOut, disciplines)


@router.put(
    "/disciplines/update",
    summary="Update an existing discipline.",
    description="Updates the name and/or acronym of an existing discipline.",
    operation_id="update_discipline",
    tags=["lookups"],
    response_model=DisciplineOut,
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
def update_discipline(
    payload: DisciplineUpdate = Body(..., examples=_example_for(DisciplineUpdate)),
    db: Session = Depends(get_db),
) -> DisciplineOut:
    """
    Update an existing discipline.

    Updates the name and/or acronym of an existing discipline.

    Args:
        payload: Discipline update data including discipline_id and at least one field to update.

    Returns:
        Updated discipline object.

    Raises:
        HTTPException: 400 if no fields provided or name/acronym already exists.
        HTTPException: 404 if discipline not found.
    """
    if payload.discipline_name is None and payload.discipline_acronym is None:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    discipline = db.get(Discipline, payload.discipline_id)
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


@router.post(
    "/disciplines/insert",
    summary="Create a new discipline.",
    description="Inserts a new discipline with the specified name and acronym.",
    operation_id="insert_discipline",
    tags=["lookups"],
    response_model=DisciplineOut,
    status_code=201,
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
def insert_discipline(
    payload: DisciplineCreate = Body(..., examples=_example_for(DisciplineCreate)),
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


@router.delete(
    "/disciplines/delete",
    summary="Delete a discipline.",
    description="Removes a discipline from the database by its ID.",
    operation_id="delete_discipline",
    tags=["lookups"],
    status_code=204,
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
def delete_discipline(
    payload: DisciplineDelete = Body(..., examples=_example_for(DisciplineDelete)),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a discipline.

    Removes a discipline from the database by its ID.

    Args:
        payload: Discipline deletion data including discipline_id.

    Raises:
        HTTPException: 404 if discipline not found.
    """
    discipline = db.get(Discipline, payload.discipline_id)
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
def list_projects(db: Session = Depends(get_db)) -> list[ProjectOut]:
    """
    List all projects.

    Returns a list of all projects sorted by project name.

    Returns:
        List of projects with id and name.

    Raises:
        HTTPException: 404 if no projects are found.
    """
    projects = db.query(Project).order_by(Project.project_name).all()
    if not projects:
        raise HTTPException(status_code=404, detail="No projects found")
    return _model_list(ProjectOut, projects)


@router.put(
    "/projects/update",
    summary="Update an existing project.",
    description="Updates the name of an existing project.",
    operation_id="update_project",
    tags=["lookups"],
    response_model=ProjectOut,
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
def update_project(
    payload: ProjectUpdate = Body(..., examples=_example_for(ProjectUpdate)),
    db: Session = Depends(get_db),
) -> ProjectOut:
    """
    Update an existing project.

    Updates the name of an existing project.

    Args:
        payload: Project update data including project_id and new project_name.

    Returns:
        Updated project object.

    Raises:
        HTTPException: 400 if no fields provided or project name already exists.
        HTTPException: 404 if project not found.
    """
    if payload.project_name is None:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    project = db.get(Project, payload.project_id)
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


@router.post(
    "/projects/insert",
    summary="Create a new project.",
    description="Inserts a new project with the specified name.",
    operation_id="insert_project",
    tags=["lookups"],
    response_model=ProjectOut,
    status_code=201,
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
def insert_project(
    payload: ProjectCreate = Body(..., examples=_example_for(ProjectCreate)),
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


@router.delete(
    "/projects/delete",
    summary="Delete a project.",
    description="Removes a project from the database by its ID.",
    operation_id="delete_project",
    tags=["lookups"],
    status_code=204,
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
def delete_project(
    payload: ProjectDelete = Body(..., examples=_example_for(ProjectDelete)),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a project.

    Removes a project from the database by its ID.

    Args:
        payload: Project deletion data including project_id.

    Raises:
        HTTPException: 404 if project not found.
    """
    project = db.get(Project, payload.project_id)
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
def list_units(db: Session = Depends(get_db)) -> list[UnitOut]:
    """
    List all units.

    Returns a list of all units sorted by unit name.

    Returns:
        List of units with id and name.

    Raises:
        HTTPException: 404 if no units are found.
    """
    units = db.query(Unit).order_by(Unit.unit_name).all()
    if not units:
        raise HTTPException(status_code=404, detail="No units found")
    return _model_list(UnitOut, units)


@router.put(
    "/units/update",
    summary="Update an existing unit.",
    description="Updates the name of an existing unit.",
    operation_id="update_unit",
    tags=["lookups"],
    response_model=UnitOut,
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
def update_unit(
    payload: UnitUpdate = Body(..., examples=_example_for(UnitUpdate)),
    db: Session = Depends(get_db),
) -> UnitOut:
    """
    Update an existing unit.

    Updates the name of an existing unit.

    Args:
        payload: Unit update data including unit_id and new unit_name.

    Returns:
        Updated unit object.

    Raises:
        HTTPException: 400 if no fields provided or unit name already exists.
        HTTPException: 404 if unit not found.
    """
    if payload.unit_name is None:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    unit = db.get(Unit, payload.unit_id)
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


@router.post(
    "/units/insert",
    summary="Create a new unit.",
    description="Inserts a new unit with the specified name.",
    operation_id="insert_unit",
    tags=["lookups"],
    response_model=UnitOut,
    status_code=201,
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
def insert_unit(
    payload: UnitCreate = Body(..., examples=_example_for(UnitCreate)),
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


@router.delete(
    "/units/delete",
    summary="Delete a unit.",
    description="Removes a unit from the database by its ID.",
    operation_id="delete_unit",
    tags=["lookups"],
    status_code=204,
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
def delete_unit(
    payload: UnitDelete = Body(..., examples=_example_for(UnitDelete)),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a unit.

    Removes a unit from the database by its ID.

    Args:
        payload: Unit deletion data including unit_id.

    Raises:
        HTTPException: 404 if unit not found.
    """
    unit = db.get(Unit, payload.unit_id)
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
def list_jobpacks(db: Session = Depends(get_db)) -> list[JobpackOut]:
    """
    List all jobpacks.

    Returns a list of all jobpacks sorted by jobpack name.

    Returns:
        List of jobpacks with id and name.

    Raises:
        HTTPException: 404 if no jobpacks are found.
    """
    jobpacks = db.query(Jobpack).order_by(Jobpack.jobpack_name).all()
    if not jobpacks:
        raise HTTPException(status_code=404, detail="No jobpacks found")
    return _model_list(JobpackOut, jobpacks)


@router.put(
    "/jobpacks/update",
    summary="Update an existing jobpack.",
    description="Updates the name of an existing jobpack.",
    operation_id="update_jobpack",
    tags=["lookups"],
    response_model=JobpackOut,
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
def update_jobpack(
    payload: JobpackUpdate = Body(..., examples=_example_for(JobpackUpdate)),
    db: Session = Depends(get_db),
) -> JobpackOut:
    """
    Update an existing jobpack.

    Updates the name of an existing jobpack.

    Args:
        payload: Jobpack update data including jobpack_id and new jobpack_name.

    Returns:
        Updated jobpack object.

    Raises:
        HTTPException: 400 if no fields provided or jobpack name already exists.
        HTTPException: 404 if jobpack not found.
    """
    if payload.jobpack_name is None:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    jobpack = db.get(Jobpack, payload.jobpack_id)
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


@router.post(
    "/jobpacks/insert",
    summary="Create a new jobpack.",
    description="Inserts a new jobpack with the specified name.",
    operation_id="insert_jobpack",
    tags=["lookups"],
    response_model=JobpackOut,
    status_code=201,
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
def insert_jobpack(
    payload: JobpackCreate = Body(..., examples=_example_for(JobpackCreate)),
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


@router.delete(
    "/jobpacks/delete",
    summary="Delete a jobpack.",
    description="Removes a jobpack from the database by its ID.",
    operation_id="delete_jobpack",
    tags=["lookups"],
    status_code=204,
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
def delete_jobpack(
    payload: JobpackDelete = Body(..., examples=_example_for(JobpackDelete)),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a jobpack.

    Removes a jobpack from the database by its ID.

    Args:
        payload: Jobpack deletion data including jobpack_id.

    Raises:
        HTTPException: 404 if jobpack not found.
    """
    jobpack = db.get(Jobpack, payload.jobpack_id)
    if not jobpack:
        raise HTTPException(status_code=404, detail="Jobpack not found")
    db.delete(jobpack)
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
def list_doc_rev_statuses(db: Session = Depends(get_db)) -> list[DocRevStatusOut]:
    """
    List all document revision statuses.

    Returns a list of all document revision statuses sorted by name.

    Returns:
        List of document revision statuses with id and name.

    Raises:
        HTTPException: 404 if no statuses are found.
    """
    statuses = db.query(DocRevStatus).order_by(DocRevStatus.rev_status_name).all()
    if not statuses:
        raise HTTPException(status_code=404, detail="No doc revision statuses found")
    return _model_list(DocRevStatusOut, statuses)


@router.post(
    "/doc_rev_statuses/insert",
    summary="Create a new document revision status.",
    description="Inserts a new document revision status with the specified name.",
    operation_id="insert_doc_rev_status",
    tags=["lookups"],
    response_model=DocRevStatusOut,
    status_code=201,
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
def insert_doc_rev_status(
    payload: DocRevStatusCreate = Body(..., examples=_example_for(DocRevStatusCreate)),
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
    status = DocRevStatus(rev_status_name=payload.rev_status_name)
    db.add(status)
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Revision status already exists", err, "insert_doc_rev_status")

    db.refresh(status)
    return _model_out(DocRevStatusOut, status)


@router.put(
    "/doc_rev_statuses/update",
    summary="Update an existing document revision status.",
    description="Updates the name of an existing document revision status.",
    operation_id="update_doc_rev_status",
    tags=["lookups"],
    response_model=DocRevStatusOut,
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
def update_doc_rev_status(
    payload: DocRevStatusUpdate = Body(..., examples=_example_for(DocRevStatusUpdate)),
    db: Session = Depends(get_db),
) -> DocRevStatusOut:
    """
    Update an existing document revision status.

    Updates the name of an existing document revision status.

    Args:
        payload: Document revision status update data including rev_status_id and rev_status_name.

    Returns:
        Updated document revision status object.

    Raises:
        HTTPException: 400 if no fields provided.
        HTTPException: 404 if status not found.
    """
    if payload.rev_status_name is None:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    status = db.get(DocRevStatus, payload.rev_status_id)
    if not status:
        raise HTTPException(status_code=404, detail="Revision status not found")

    status.rev_status_name = payload.rev_status_name
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Revision status already exists", err, "update_doc_rev_status")

    db.refresh(status)
    return _model_out(DocRevStatusOut, status)


@router.delete(
    "/doc_rev_statuses/delete",
    summary="Delete a document revision status.",
    description="Removes a document revision status from the database by its ID.",
    operation_id="delete_doc_rev_status",
    tags=["lookups"],
    status_code=204,
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
def delete_doc_rev_status(
    payload: DocRevStatusDelete = Body(..., examples=_example_for(DocRevStatusDelete)),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a document revision status.

    Removes a document revision status from the database by its ID.

    Args:
        payload: Document revision status deletion data including rev_status_id.

    Raises:
        HTTPException: 404 if status not found.
    """
    status = db.get(DocRevStatus, payload.rev_status_id)
    if not status:
        raise HTTPException(status_code=404, detail="Revision status not found")
    db.delete(status)
    db.commit()
