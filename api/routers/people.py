"""People and security endpoints for persons, users, and permissions."""

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query, Session

from api.db.models import Discipline, Permission, Person, PersonDuty, Project, Role, User
from api.schemas.lookups import RoleCreate, RoleOut, RoleUpdate
from api.schemas.people import (
    PermissionCreate,
    PermissionOut,
    PermissionUpdate,
    PersonCreate,
    PersonOut,
    PersonUpdate,
    UserCreate,
    UserOut,
    UserUpdate,
)
from api.utils.database import get_db
from api.utils.helpers import (
    _example_for,
    _handle_integrity_error,
    _model_list,
    _model_out,
    _require_non_null_fields,
)

router = APIRouter(prefix="/api/v1/people", tags=["people"])


def _build_user_out(user: User) -> UserOut:
    duty = user.person.duty if user.person else None
    return UserOut(
        user_id=user.user_id,
        person_id=user.person_id,
        user_acronym=user.user_acronym,
        role_id=user.role_id,
        person_name=user.person.person_name if user.person else None,
        role_name=user.role.role_name if user.role else None,
        duty_id=user.person.duty_id if user.person else None,
        duty_name=duty.duty_name if duty else None,
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


def _permission_filter(query: Query[Permission], payload) -> Query[Permission]:
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
    """
    rows = (
        db.execute(
            text(
                """
                SELECT role_id, role_name
                FROM workflow.roles
                ORDER BY role_name
                """
            )
        )
        .mappings()
        .all()
    )
    return _model_list(RoleOut, rows)


def insert_role(
    payload: RoleCreate = Body(..., openapi_examples=_example_for(RoleCreate)),
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


def update_role(
    role_id: int,
    payload: RoleUpdate = Body(..., openapi_examples=_example_for(RoleUpdate)),
    db: Session = Depends(get_db),
) -> RoleOut:
    """
    Update an existing role.

    Updates the name of an existing role.

    Args:
        role_id: Role ID to update.
        payload: Role update data including role_name.

    Returns:
        Updated role object.

    Raises:
        HTTPException: 400 if no fields provided.
        HTTPException: 404 if role not found.
    """
    if "role_name" not in payload.model_fields_set:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    _require_non_null_fields(payload, ("role_name",))

    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    assert payload.role_name is not None
    role.role_name = payload.role_name
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Failed to update role", err, "update_role")
    db.refresh(role)
    return _model_out(RoleOut, role)


def delete_role(role_id: int, db: Session = Depends(get_db)) -> None:
    """
    Delete a role.

    Removes a role from the database by its ID.

    Args:
        role_id: Role ID to delete.

    Raises:
        HTTPException: 404 if role not found.
    """
    role = db.get(Role, role_id)
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
    """
    rows = (
        db.execute(
            text(
                """
                SELECT
                    p.person_id,
                    p.person_name,
                    p.photo_s3_uid,
                    p.duty_id,
                    pd.duty_name
                FROM workflow.person AS p
                LEFT JOIN workflow.person_duty AS pd ON pd.duty_id = p.duty_id
                ORDER BY person_name
                """
            )
        )
        .mappings()
        .all()
    )
    return _model_list(PersonOut, rows)


def update_person(
    person_id: int,
    payload: PersonUpdate = Body(..., openapi_examples=_example_for(PersonUpdate)),
    db: Session = Depends(get_db),
) -> PersonOut:
    """
    Update an existing person.

    Updates the name and/or photo S3 UID of an existing person.

    Args:
        person_id: Person ID to update.
        payload: Person update data including at least one field to update.

    Returns:
        Updated person object.

    Raises:
        HTTPException: 400 if no fields provided.
        HTTPException: 404 if person not found.
    """
    if not {"person_name", "photo_s3_uid", "duty_id"}.intersection(payload.model_fields_set):
        raise HTTPException(status_code=400, detail="No fields provided for update")
    _require_non_null_fields(payload, ("person_name",))

    person = db.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    if payload.person_name is not None:
        person.person_name = payload.person_name
    if payload.photo_s3_uid is not None:
        person.photo_s3_uid = payload.photo_s3_uid
    if "duty_id" in payload.model_fields_set:
        if payload.duty_id is not None and not db.get(PersonDuty, payload.duty_id):
            raise HTTPException(status_code=404, detail="Person duty not found")
        person.duty_id = payload.duty_id

    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Failed to update person", err, "update_person")

    db.refresh(person)
    return _model_out(PersonOut, person)


def insert_person(
    payload: PersonCreate = Body(..., openapi_examples=_example_for(PersonCreate)),
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
    if payload.duty_id is not None and not db.get(PersonDuty, payload.duty_id):
        raise HTTPException(status_code=404, detail="Person duty not found")

    person = Person(
        person_name=payload.person_name,
        photo_s3_uid=payload.photo_s3_uid,
        duty_id=payload.duty_id,
    )
    db.add(person)
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Failed to create person", err, "insert_person")
    db.refresh(person)
    return _model_out(PersonOut, person)


def delete_person(person_id: int, db: Session = Depends(get_db)) -> None:
    """
    Delete a person.

    Removes a person from the database by their ID.

    Args:
        person_id: Person ID to delete.

    Raises:
        HTTPException: 404 if person not found.
    """
    person = db.get(Person, person_id)
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
    """
    rows = (
        db.execute(
            text(
                """
                SELECT
                    u.user_id,
                    u.person_id,
                    u.user_acronym,
                    u.role_id,
                    p.person_name,
                    r.role_name,
                    p.duty_id,
                    pd.duty_name
                FROM workflow.users AS u
                JOIN workflow.person AS p ON p.person_id = u.person_id
                JOIN workflow.roles AS r ON r.role_id = u.role_id
                LEFT JOIN workflow.person_duty AS pd ON pd.duty_id = p.duty_id
                ORDER BY u.user_acronym
                """
            )
        )
        .mappings()
        .all()
    )
    return _model_list(UserOut, rows)


@router.get(
    "/users/current_user",
    summary="Get current user.",
    description="Returns the current user and person info (currently hardcoded to user_id=2).",
    operation_id="get_current_user",
    tags=["people"],
    response_model=UserOut,
    responses={
        404: {
            "description": "Not Found",
            "content": {"application/json": {"example": {"detail": "User not found"}}},
        },
    },
)
def get_current_user(db: Session = Depends(get_db)) -> UserOut:
    """
    Get current user.

    Returns the current user and person info. Currently hardcoded to user_id=2.
    """
    row = (
        db.execute(
            text(
                """
                SELECT
                    u.user_id,
                    u.person_id,
                    u.user_acronym,
                    u.role_id,
                    p.person_name,
                    r.role_name,
                    p.duty_id,
                    pd.duty_name
                FROM workflow.users AS u
                JOIN workflow.person AS p ON p.person_id = u.person_id
                JOIN workflow.roles AS r ON r.role_id = u.role_id
                LEFT JOIN workflow.person_duty AS pd ON pd.duty_id = p.duty_id
                WHERE u.user_id = 2
                """
            )
        )
        .mappings()
        .one_or_none()
    )
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return _model_out(UserOut, row)


def update_user(
    user_id: int,
    payload: UserUpdate = Body(..., openapi_examples=_example_for(UserUpdate)),
    db: Session = Depends(get_db),
) -> UserOut:
    """
    Update an existing user.

    Updates the person reference, acronym, and/or role of an existing user.

    Args:
        user_id: User ID to update.
        payload: User update data including at least one field to update.

    Returns:
        Updated user object with person and role information.

    Raises:
        HTTPException: 400 if no fields provided or update fails.
        HTTPException: 404 if user, person, or role not found.
    """
    if not {"person_id", "user_acronym", "role_id"}.intersection(payload.model_fields_set):
        raise HTTPException(status_code=400, detail="No fields provided for update")
    _require_non_null_fields(payload, ("person_id", "user_acronym", "role_id"))

    user = db.get(User, user_id)
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


def insert_user(
    payload: UserCreate = Body(..., openapi_examples=_example_for(UserCreate)),
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


def delete_user(user_id: int, db: Session = Depends(get_db)) -> None:
    """
    Delete a user.

    Removes a user from the database by their ID.

    Args:
        user_id: User ID to delete.

    Raises:
        HTTPException: 404 if user not found.
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()


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
    """
    rows = (
        db.execute(
            text(
                """
                SELECT
                    perm.permission_id,
                    perm.user_id,
                    perm.project_id,
                    perm.discipline_id,
                    u.user_acronym,
                    p.person_name,
                    proj.project_name,
                    d.discipline_name
                FROM workflow.permissions AS perm
                JOIN workflow.users AS u ON u.user_id = perm.user_id
                JOIN workflow.person AS p ON p.person_id = u.person_id
                LEFT JOIN workflow.projects AS proj ON proj.project_id = perm.project_id
                LEFT JOIN workflow.disciplines AS d ON d.discipline_id = perm.discipline_id
                ORDER BY perm.user_id
                """
            )
        )
        .mappings()
        .all()
    )
    return _model_list(PermissionOut, rows)


def insert_permission(
    payload: PermissionCreate = Body(..., openapi_examples=_example_for(PermissionCreate)),
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


def update_permission(
    permission_id: int,
    payload: PermissionUpdate = Body(..., openapi_examples=_example_for(PermissionUpdate)),
    db: Session = Depends(get_db),
) -> PermissionOut:
    """
    Update an existing permission.

    Updates the project and/or discipline scope of an existing permission.

    Args:
        permission_id: Permission ID to update.
        payload: Permission update data including current scope (optional) and new scope values.

    Returns:
        Updated permission object with metadata.

    Raises:
        HTTPException: 400 if current scope missing, no new scope provided, or
        permission already exists.
        HTTPException: 404 if permission, project, or discipline not found.
    """
    existing = db.get(Permission, permission_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Permission not found")

    if payload.user_id != existing.user_id:
        raise HTTPException(status_code=400, detail="User ID mismatch for permission")
    if payload.project_id is not None and payload.project_id != existing.project_id:
        raise HTTPException(status_code=400, detail="Project ID mismatch for permission")
    if payload.discipline_id is not None and payload.discipline_id != existing.discipline_id:
        raise HTTPException(status_code=400, detail="Discipline ID mismatch for permission")

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


def delete_permission(permission_id: int, db: Session = Depends(get_db)) -> None:
    """
    Delete a permission.

    Removes a permission from the database by its ID.

    Args:
        permission_id: Permission ID to delete.

    Raises:
        HTTPException: 404 if permission not found.
    """
    permission = db.get(Permission, permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    db.delete(permission)
    db.commit()
