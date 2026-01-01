"""People and security endpoints for persons, users, and permissions."""

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.db.models import Discipline, Permission, Person, Project, Role, User
from api.schemas.lookups import RoleCreate, RoleDelete, RoleOut, RoleUpdate
from api.schemas.people import (
    PermissionCreate,
    PermissionDelete,
    PermissionOut,
    PermissionUpdate,
    PersonCreate,
    PersonDelete,
    PersonOut,
    PersonUpdate,
    UserCreate,
    UserDelete,
    UserOut,
    UserUpdate,
)
from api.utils.database import get_db
from api.utils.helpers import _example_for, _handle_integrity_error, _model_list, _model_out

router = APIRouter(prefix="/api/v1/people", tags=["people"])


def _build_user_out(user: User) -> UserOut:
    return UserOut(
        user_id=user.user_id,
        person_id=user.person_id,
        user_acronym=user.user_acronym,
        role_id=user.role_id,
        person_name=user.person.person_name if user.person else None,
        role_name=user.role.role_name if user.role else None,
    )


def _build_permission_out(permission: Permission) -> PermissionOut:
    user = permission.user
    person = user.person if user else None
    project = permission.project
    discipline = permission.discipline
    return PermissionOut(
        permission_id=permission.permission_id,
        user_id=permission.user_id,
        project_id=permission.project_id,
        discipline_id=permission.discipline_id,
        user_acronym=user.user_acronym if user else None,
        person_name=person.person_name if person else None,
        project_name=project.project_name if project else None,
        discipline_name=discipline.discipline_name if discipline else None,
    )


def _permission_filter(query, payload) -> Session:
    if getattr(payload, "permission_id", None) is not None:
        return query.filter(Permission.permission_id == payload.permission_id)

    query = query.filter(Permission.user_id == payload.user_id)
    if payload.project_id is None:
        query = query.filter(Permission.project_id.is_(None))
    else:
        query = query.filter(Permission.project_id == payload.project_id)
    if payload.discipline_id is None:
        query = query.filter(Permission.discipline_id.is_(None))
    else:
        query = query.filter(Permission.discipline_id == payload.discipline_id)
    return query


@router.get(
    "/roles",
    summary="List all roles.",
    description="Returns a list of all roles sorted by role name.",
    operation_id="list_roles",
    tags=["people"],
    response_model=list[RoleOut],
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
def list_roles(db: Session = Depends(get_db)) -> list[RoleOut]:
    """
    List all roles.

    Returns a list of all roles sorted by role name.

    Returns:
        List of roles with id and name.

    Raises:
        HTTPException: 404 if no roles are found.
    """
    roles = db.query(Role).order_by(Role.role_name).all()
    if not roles:
        raise HTTPException(status_code=404, detail="No roles found")
    return _model_list(RoleOut, roles)


@router.post(
    "/roles/insert",
    summary="Create a new role.",
    description="Inserts a new role with the specified name.",
    operation_id="insert_role",
    tags=["people"],
    response_model=RoleOut,
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
def insert_role(
    payload: RoleCreate = Body(..., examples=_example_for(RoleCreate)),
    db: Session = Depends(get_db),
) -> RoleOut:
    """
    Create a new role.

    Inserts a new role with the specified name.

    Args:
        payload: Role creation data including name.

    Returns:
        Newly created role object.

    Raises:
        HTTPException: 400 on creation failure.
    """
    role = Role(role_name=payload.role_name)
    db.add(role)
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Failed to create role", err, "insert_role")
    db.refresh(role)
    return _model_out(RoleOut, role)


@router.put(
    "/roles/update",
    summary="Update an existing role.",
    description="Updates the name of an existing role.",
    operation_id="update_role",
    tags=["people"],
    response_model=RoleOut,
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
def update_role(
    payload: RoleUpdate = Body(..., examples=_example_for(RoleUpdate)),
    db: Session = Depends(get_db),
) -> RoleOut:
    """
    Update an existing role.

    Updates the name of an existing role.

    Args:
        payload: Role update data including role_id and role_name.

    Returns:
        Updated role object.

    Raises:
        HTTPException: 400 if no fields provided.
        HTTPException: 404 if role not found.
    """
    if payload.role_name is None:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    role = db.get(Role, payload.role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    role.role_name = payload.role_name
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Failed to update role", err, "update_role")
    db.refresh(role)
    return _model_out(RoleOut, role)


@router.delete(
    "/roles/delete",
    summary="Delete a role.",
    description="Removes a role from the database by its ID.",
    operation_id="delete_role",
    tags=["people"],
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
def delete_role(
    payload: RoleDelete = Body(..., examples=_example_for(RoleDelete)),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a role.

    Removes a role from the database by its ID.

    Args:
        payload: Role deletion data including role_id.

    Raises:
        HTTPException: 404 if role not found.
    """
    role = db.get(Role, payload.role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    db.delete(role)
    db.commit()


@router.get(
    "/persons",
    summary="List all persons.",
    description="Returns a list of all persons sorted by person name.",
    operation_id="list_persons",
    tags=["people"],
    response_model=list[PersonOut],
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
def list_persons(db: Session = Depends(get_db)) -> list[PersonOut]:
    """
    List all persons.

    Returns a list of all persons sorted by person name.

    Returns:
        List of persons with id, name, and photo S3 UID.

    Raises:
        HTTPException: 404 if no persons are found.
    """
    persons = db.query(Person).order_by(Person.person_name).all()
    if not persons:
        raise HTTPException(status_code=404, detail="No persons found")
    return _model_list(PersonOut, persons)


@router.put(
    "/persons/update",
    summary="Update an existing person.",
    description="Updates the name and/or photo S3 UID of an existing person.",
    operation_id="update_person",
    tags=["people"],
    response_model=PersonOut,
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
def update_person(
    payload: PersonUpdate = Body(..., examples=_example_for(PersonUpdate)),
    db: Session = Depends(get_db),
) -> PersonOut:
    """
    Update an existing person.

    Updates the name and/or photo S3 UID of an existing person.

    Args:
        payload: Person update data including person_id and at least one field to update.

    Returns:
        Updated person object.

    Raises:
        HTTPException: 400 if no fields provided.
        HTTPException: 404 if person not found.
    """
    if payload.person_name is None and payload.photo_s3_uid is None:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    person = db.get(Person, payload.person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    if payload.person_name is not None:
        person.person_name = payload.person_name
    if payload.photo_s3_uid is not None:
        person.photo_s3_uid = payload.photo_s3_uid

    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Failed to update person", err, "update_person")

    db.refresh(person)
    return _model_out(PersonOut, person)


@router.post(
    "/persons/insert",
    summary="Create a new person.",
    description="Inserts a new person with the specified name and optional photo S3 UID.",
    operation_id="insert_person",
    tags=["people"],
    response_model=PersonOut,
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
def insert_person(
    payload: PersonCreate = Body(..., examples=_example_for(PersonCreate)),
    db: Session = Depends(get_db),
) -> PersonOut:
    """
    Create a new person.

    Inserts a new person with the specified name and optional photo S3 UID.

    Args:
        payload: Person creation data including name and optional photo S3 UID.

    Returns:
        Newly created person object.

    Raises:
        HTTPException: 400 on creation failure.
    """
    person = Person(person_name=payload.person_name, photo_s3_uid=payload.photo_s3_uid)
    db.add(person)
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Failed to create person", err, "insert_person")
    db.refresh(person)
    return _model_out(PersonOut, person)


@router.delete(
    "/persons/delete",
    summary="Delete a person.",
    description="Removes a person from the database by their ID.",
    operation_id="delete_person",
    tags=["people"],
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
def delete_person(
    payload: PersonDelete = Body(..., examples=_example_for(PersonDelete)),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a person.

    Removes a person from the database by their ID.

    Args:
        payload: Person deletion data including person_id.

    Raises:
        HTTPException: 404 if person not found.
    """
    person = db.get(Person, payload.person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    db.delete(person)
    db.commit()


@router.get(
    "/users",
    summary="List all users.",
    description=(
        "Returns a list of all users sorted by user acronym, including person and role "
        "information."
    ),
    operation_id="list_users",
    tags=["people"],
    response_model=list[UserOut],
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
def list_users(db: Session = Depends(get_db)) -> list[UserOut]:
    """
    List all users.

    Returns a list of all users sorted by user acronym, including person and role information.

    Returns:
        List of users with id, person details, acronym, and role information.

    Raises:
        HTTPException: 404 if no users are found.
    """
    users = (
        db.query(User)
        .join(Person, User.person_id == Person.person_id)
        .join(Role, User.role_id == Role.role_id)
        .order_by(User.user_acronym)
        .all()
    )
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    return [_build_user_out(user) for user in users]


@router.put(
    "/users/update",
    summary="Update an existing user.",
    description="Updates the person reference, acronym, and/or role of an existing user.",
    operation_id="update_user",
    tags=["people"],
    response_model=UserOut,
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
def update_user(
    payload: UserUpdate = Body(..., examples=_example_for(UserUpdate)),
    db: Session = Depends(get_db),
) -> UserOut:
    """
    Update an existing user.

    Updates the person reference, acronym, and/or role of an existing user.

    Args:
        payload: User update data including user_id and at least one field to update.

    Returns:
        Updated user object with person and role information.

    Raises:
        HTTPException: 400 if no fields provided or update fails.
        HTTPException: 404 if user, person, or role not found.
    """
    if payload.person_id is None and payload.user_acronym is None and payload.role_id is None:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.person_id is not None:
        person = db.get(Person, payload.person_id)
        if not person:
            raise HTTPException(status_code=404, detail="Person not found")
        user.person_id = payload.person_id
    if payload.user_acronym is not None:
        user.user_acronym = payload.user_acronym
    if payload.role_id is not None:
        role = db.get(Role, payload.role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        user.role_id = payload.role_id

    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Failed to update user", err, "update_user")

    db.refresh(user)
    return _build_user_out(user)


@router.post(
    "/users/insert",
    summary="Create a new user.",
    description="Creates a new user with the specified person reference, acronym, and role.",
    operation_id="insert_user",
    tags=["people"],
    response_model=UserOut,
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
def insert_user(
    payload: UserCreate = Body(..., examples=_example_for(UserCreate)),
    db: Session = Depends(get_db),
) -> UserOut:
    """
    Create a new user.

    Creates a new user with the specified person reference, acronym, and role.

    Args:
        payload: User creation data including person_id, user_acronym, and role_id.

    Returns:
        Newly created user object with person and role information.

    Raises:
        HTTPException: 400 on creation failure.
        HTTPException: 404 if person or role not found.
    """
    person = db.get(Person, payload.person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    role = db.get(Role, payload.role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    user = User(
        person_id=payload.person_id, user_acronym=payload.user_acronym, role_id=payload.role_id
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Failed to create user", err, "insert_user")
    db.refresh(user)
    return _build_user_out(user)


@router.delete(
    "/users/delete",
    summary="Delete a user.",
    description="Removes a user from the database by their ID.",
    operation_id="delete_user",
    tags=["people"],
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
def delete_user(
    payload: UserDelete = Body(..., examples=_example_for(UserDelete)),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a user.

    Removes a user from the database by their ID.

    Args:
        payload: User deletion data including user_id.

    Raises:
        HTTPException: 404 if user not found.
    """
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()


def _permission_filter(
    query,
    payload,
) -> Session:
    if getattr(payload, "permission_id", None) is not None:
        return query.filter(Permission.permission_id == payload.permission_id)

    query = query.filter(Permission.user_id == payload.user_id)
    if payload.project_id is None:
        query = query.filter(Permission.project_id.is_(None))
    else:
        query = query.filter(Permission.project_id == payload.project_id)
    if payload.discipline_id is None:
        query = query.filter(Permission.discipline_id.is_(None))
    else:
        query = query.filter(Permission.discipline_id == payload.discipline_id)
    return query


@router.get(
    "/permissions",
    summary="List all permissions.",
    description=(
        "Returns a list of all permissions sorted by user ID, including user, person, project, and "
        "discipline information."
    ),
    operation_id="list_permissions",
    tags=["people"],
    response_model=list[PermissionOut],
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
def list_permissions(db: Session = Depends(get_db)) -> list[PermissionOut]:
    """
    List all permissions.

    Returns a list of all permissions sorted by user ID, including user, person, project, and
    discipline information.

    Returns:
        List of permissions with comprehensive metadata.

    Raises:
        HTTPException: 404 if no permissions are found.
    """
    permissions = db.query(Permission).order_by(Permission.user_id).all()
    if not permissions:
        raise HTTPException(status_code=404, detail="No permissions found")
    return [_build_permission_out(p) for p in permissions]


@router.post(
    "/permissions/insert",
    summary="Create a new permission.",
    description=(
        "Creates a new permission for a user with project and/or discipline scope. At least one of "
        "project_id or discipline_id must be provided."
    ),
    operation_id="insert_permission",
    tags=["people"],
    response_model=PermissionOut,
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
def insert_permission(
    payload: PermissionCreate = Body(..., examples=_example_for(PermissionCreate)),
    db: Session = Depends(get_db),
) -> PermissionOut:
    """
    Create a new permission.

    Creates a new permission for a user with project and/or discipline scope. At least one of
    project_id or discipline_id must be provided.

    Args:
        payload: Permission creation data including user_id and at least one of
        project_id or discipline_id.

    Returns:
        Newly created permission object with metadata.

    Raises:
        HTTPException: 400 if scope is missing or permission already exists.
        HTTPException: 404 if user, project, or discipline not found.
    """
    payload.validate_scope()

    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.project_id is not None and not db.get(Project, payload.project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    if payload.discipline_id is not None and not db.get(Discipline, payload.discipline_id):
        raise HTTPException(status_code=404, detail="Discipline not found")

    existing = _permission_filter(db.query(Permission), payload).first()
    if existing:
        raise HTTPException(status_code=400, detail="Permission already exists")

    permission = Permission(
        user_id=payload.user_id,
        project_id=payload.project_id,
        discipline_id=payload.discipline_id,
    )
    db.add(permission)
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Failed to create permission", err, "insert_permission")
    db.refresh(permission)
    return _build_permission_out(permission)


@router.put(
    "/permissions/update",
    summary="Update an existing permission.",
    description="Updates the project and/or discipline scope of an existing permission.",
    operation_id="update_permission",
    tags=["people"],
    response_model=PermissionOut,
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
def update_permission(
    payload: PermissionUpdate = Body(..., examples=_example_for(PermissionUpdate)),
    db: Session = Depends(get_db),
) -> PermissionOut:
    """
    Update an existing permission.

    Updates the project and/or discipline scope of an existing permission.

    Args:
        payload: Permission update data including current scope and new scope values.

    Returns:
        Updated permission object with metadata.

    Raises:
        HTTPException: 400 if current scope missing, no new scope provided, or
        permission already exists.
        HTTPException: 404 if permission, project, or discipline not found.
    """
    payload.validate_current()

    existing = _permission_filter(db.query(Permission), payload).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Permission not found")

    provided_project = "new_project_id" in payload.model_fields_set
    provided_discipline = "new_discipline_id" in payload.model_fields_set
    if not provided_project and not provided_discipline:
        raise HTTPException(status_code=400, detail="Provide new_project_id or new_discipline_id")

    # Resolve target scope (fallback to current if not provided, allow explicit null)
    target_project_id = existing.project_id if not provided_project else payload.new_project_id
    target_discipline_id = (
        existing.discipline_id if not provided_discipline else payload.new_discipline_id
    )

    # Validate references
    if target_project_id is not None and not db.get(Project, target_project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    if target_discipline_id is not None and not db.get(Discipline, target_discipline_id):
        raise HTTPException(status_code=404, detail="Discipline not found")

    # Check for duplicate with new scope
    if target_project_id != existing.project_id or target_discipline_id != existing.discipline_id:
        dup_payload = PermissionCreate(
            user_id=existing.user_id,
            project_id=target_project_id,
            discipline_id=target_discipline_id,
        )
        if _permission_filter(db.query(Permission), dup_payload).first():
            raise HTTPException(status_code=400, detail="Permission already exists")

    existing.project_id = target_project_id
    existing.discipline_id = target_discipline_id

    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Failed to update permission", err, "update_permission")

    db.refresh(existing)
    return _build_permission_out(existing)


@router.delete(
    "/permissions/delete",
    summary="Delete a permission.",
    description=(
        "Removes a permission from the database. Can be identified by permission_id or by user_id "
        "with project_id and/or discipline_id."
    ),
    operation_id="delete_permission",
    tags=["people"],
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
def delete_permission(
    payload: PermissionDelete = Body(..., examples=_example_for(PermissionDelete)),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a permission.

    Removes a permission from the database. Can be identified by permission_id or by user_id with
    project_id and/or discipline_id.

    Args:
        payload: Permission deletion data including permission_id or user scope.

    Raises:
        HTTPException: 400 if scope information is missing.
        HTTPException: 404 if permission not found.
    """
    payload.validate_scope()

    permission = _permission_filter(db.query(Permission), payload).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    db.delete(permission)
    db.commit()
