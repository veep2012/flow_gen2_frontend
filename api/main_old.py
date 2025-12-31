import inspect
import logging
import os
import re
import time
import uuid
from email.utils import formatdate
from typing import Any, Callable, Iterable, TypeVar
from urllib.parse import quote, urlparse

from fastapi import Body, Depends, FastAPI, Form, HTTPException, Query, Request, UploadFile
from fastapi import File as UploadFileField
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import StreamingResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased, joinedload, sessionmaker
from starlette.background import BackgroundTask

from api.db.models import (
    Area,
    Discipline,
    Doc,
    DocRevision,
    DocRevMilestone,
    DocRevStatus,
    DocType,
    File,
    Jobpack,
    Permission,
    Person,
    Project,
    RevisionOverview,
    Role,
    Unit,
    User,
)


def _build_database_url() -> str:
    explicit = os.getenv("DATABASE_URL")
    if explicit:
        return os.path.expandvars(explicit)

    user = os.getenv("POSTGRES_USER", "flow_user")
    password = os.getenv("POSTGRES_PASSWORD", "flow_pass")
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "flow_db")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db_name}"


DATABASE_URL = _build_database_url()


def _build_minio_client() -> tuple[object, str]:
    try:
        from minio import Minio
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail="MinIO client library not installed; install dependencies.",
        ) from exc
    endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    bucket = os.getenv("MINIO_BUCKET", "flow-default")
    access_key = os.getenv("MINIO_ROOT_USER", "flow_minio")
    secret_key = os.getenv("MINIO_ROOT_PASSWORD", "change_me_now")
    secure = os.getenv("MINIO_SECURE", "").lower() in {"1", "true", "yes", "on"}

    if endpoint.startswith(("http://", "https://")):
        parsed = urlparse(endpoint)
        endpoint = parsed.netloc
        secure = parsed.scheme == "https"

    if not endpoint:
        raise HTTPException(status_code=500, detail="MinIO endpoint is not configured")

    return Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure), bucket


T = TypeVar("T")
ModelT = TypeVar("ModelT", bound=BaseModel)


def _minio_with_retry(action: str, endpoint: str, func: Callable[[], T]) -> T:
    retries = int(os.getenv("MINIO_RETRIES", "3"))
    delay = float(os.getenv("MINIO_RETRY_DELAY_SEC", "1"))
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return func()
        except Exception as err:
            last_err = err
            if attempt < retries:
                time.sleep(delay)
                continue
            logger.exception("MinIO %s failed after %s attempts: %s", action, retries, err)
            raise HTTPException(
                status_code=502,
                detail=f"MinIO {action} failed; check MINIO_ENDPOINT ({endpoint})",
            ) from last_err


def _s3_safe_segment(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9.\-\s]", "_", value.strip()).replace("/", "_")[:128]


def _build_file_object_key(
    project_name: str | None,
    doc_name_unique: str,
    transmittal_current_revision: str,
    unique_id: str,
    filename: str,
) -> str:
    project_segment = _s3_safe_segment(project_name) if project_name else "unassigned"
    doc_segment = _s3_safe_segment(doc_name_unique) if doc_name_unique else "doc_unknown"
    rev_segment = _s3_safe_segment(transmittal_current_revision)
    safe_filename = os.path.basename(filename)
    return f"{project_segment}/{doc_segment}/{rev_segment}/{unique_id}_{safe_filename}"


def _example_for(model_cls: type[ModelT]) -> dict[str, dict[str, object]]:
    schema = model_cls.model_json_schema()
    props = schema.get("properties", {}) if isinstance(schema, dict) else {}
    example: dict[str, object] = {}
    for name, prop in props.items():
        if not isinstance(prop, dict):
            continue
        if prop.get("examples"):
            example[name] = prop["examples"][0]
        elif "example" in prop:
            example[name] = prop["example"]
    if not example:
        return {}
    return {"default": {"summary": f"{model_cls.__name__} example", "value": example}}


def _model_out(model_cls: type[ModelT], obj: object) -> ModelT:
    return model_cls.model_validate(obj)


def _model_list(model_cls: type[ModelT], items: Iterable[object]) -> list[ModelT]:
    return [model_cls.model_validate(item) for item in items]


def _close_minio_response(response) -> None:
    response.close()
    response.release_conn()


engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

logger = logging.getLogger(__name__)
DEBUG_MODE = os.getenv("DEBUG", "").lower() in {"1", "true", "yes", "on", "debug"}


def _handle_integrity_error(detail: str, err: IntegrityError, context: str | None = None) -> None:
    ctx = f" during {context}" if context else ""
    logger.exception("IntegrityError%s: %s", ctx, err)
    message = detail if not DEBUG_MODE else f"{detail} ({err})"
    raise HTTPException(status_code=400, detail=message)


app = FastAPI(title="Flow Backend", version="0.1.0")

allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

# Wildcard cannot be used with credentials. Disable credentials when "*" is present
# to stay spec-compliant.
allow_credentials = "*" not in allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AreaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    area_id: int = Field(
        ...,
        description="Area ID.",
        examples=[1],
        gt=0,
    )
    area_name: str = Field(
        ...,
        description="Area name.",
        examples=["Area A"],
        min_length=1,
    )
    area_acronym: str = Field(
        ...,
        description="Area acronym.",
        examples=["ABC"],
        min_length=1,
    )


class AreaUpdate(BaseModel):
    area_id: int = Field(
        ...,
        description="Area ID.",
        examples=[1],
        gt=0,
    )
    area_name: str | None = Field(
        None,
        description="Area name.",
        examples=["Area A"],
        min_length=1,
    )
    area_acronym: str | None = Field(
        None,
        description="Area acronym.",
        examples=["ABC"],
        min_length=1,
    )


class AreaCreate(BaseModel):
    area_name: str = Field(
        ...,
        description="Area name.",
        examples=["Area A"],
        min_length=1,
    )
    area_acronym: str = Field(
        ...,
        description="Area acronym.",
        examples=["ABC"],
        min_length=1,
    )


class AreaDelete(BaseModel):
    area_id: int = Field(
        ...,
        description="Area ID.",
        examples=[1],
        gt=0,
    )


class DisciplineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    discipline_id: int = Field(
        ...,
        description="Discipline ID.",
        examples=[1],
        gt=0,
    )
    discipline_name: str = Field(
        ...,
        description="Discipline name.",
        examples=["Discipline A"],
        min_length=1,
    )
    discipline_acronym: str = Field(
        ...,
        description="Discipline acronym.",
        examples=["ABC"],
        min_length=1,
    )


class DisciplineUpdate(BaseModel):
    discipline_id: int = Field(
        ...,
        description="Discipline ID.",
        examples=[1],
        gt=0,
    )
    discipline_name: str | None = Field(
        None,
        description="Discipline name.",
        examples=["Discipline A"],
        min_length=1,
    )
    discipline_acronym: str | None = Field(
        None,
        description="Discipline acronym.",
        examples=["ABC"],
        min_length=1,
    )


class DisciplineCreate(BaseModel):
    discipline_name: str = Field(
        ...,
        description="Discipline name.",
        examples=["Discipline A"],
        min_length=1,
    )
    discipline_acronym: str = Field(
        ...,
        description="Discipline acronym.",
        examples=["ABC"],
        min_length=1,
    )


class DisciplineDelete(BaseModel):
    discipline_id: int = Field(
        ...,
        description="Discipline ID.",
        examples=[1],
        gt=0,
    )


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_id: int = Field(
        ...,
        description="Project ID.",
        examples=[1],
        gt=0,
    )
    project_name: str = Field(
        ...,
        description="Project name.",
        examples=["Project A"],
        min_length=1,
    )


class ProjectUpdate(BaseModel):
    project_id: int = Field(
        ...,
        description="Project ID.",
        examples=[1],
        gt=0,
    )
    project_name: str | None = Field(
        None,
        description="Project name.",
        examples=["Project A"],
        min_length=1,
    )


class ProjectCreate(BaseModel):
    project_name: str = Field(
        ...,
        description="Project name.",
        examples=["Project A"],
        min_length=1,
    )


class ProjectDelete(BaseModel):
    project_id: int = Field(
        ...,
        description="Project ID.",
        examples=[1],
        gt=0,
    )


class UnitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    unit_id: int = Field(
        ...,
        description="Unit ID.",
        examples=[1],
        gt=0,
    )
    unit_name: str = Field(
        ...,
        description="Unit name.",
        examples=["Unit A"],
        min_length=1,
    )


class UnitUpdate(BaseModel):
    unit_id: int = Field(
        ...,
        description="Unit ID.",
        examples=[1],
        gt=0,
    )
    unit_name: str | None = Field(
        None,
        description="Unit name.",
        examples=["Unit A"],
        min_length=1,
    )


class UnitCreate(BaseModel):
    unit_name: str = Field(
        ...,
        description="Unit name.",
        examples=["Unit A"],
        min_length=1,
    )


class UnitDelete(BaseModel):
    unit_id: int = Field(
        ...,
        description="Unit ID.",
        examples=[1],
        gt=0,
    )


class JobpackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    jobpack_id: int = Field(
        ...,
        description="Jobpack ID.",
        examples=[1],
        gt=0,
    )
    jobpack_name: str = Field(
        ...,
        description="Jobpack name.",
        examples=["Jobpack A"],
        min_length=1,
    )


class JobpackUpdate(BaseModel):
    jobpack_id: int = Field(
        ...,
        description="Jobpack ID.",
        examples=[1],
        gt=0,
    )
    jobpack_name: str | None = Field(
        None,
        description="Jobpack name.",
        examples=["Jobpack A"],
        min_length=1,
    )


class JobpackCreate(BaseModel):
    jobpack_name: str = Field(
        ...,
        description="Jobpack name.",
        examples=["Jobpack A"],
        min_length=1,
    )


class JobpackDelete(BaseModel):
    jobpack_id: int = Field(
        ...,
        description="Jobpack ID.",
        examples=[1],
        gt=0,
    )


class DocTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    type_id: int = Field(
        ...,
        description="Type ID.",
        examples=[1],
        gt=0,
    )
    doc_type_name: str = Field(
        ...,
        description="Document type name.",
        examples=["Doc Type A"],
        min_length=1,
    )
    ref_discipline_id: int = Field(
        ...,
        description="Ref Discipline ID.",
        examples=[1],
        gt=0,
    )
    doc_type_acronym: str = Field(
        ...,
        description="Document type acronym.",
        examples=["ABC"],
        min_length=1,
    )
    discipline_name: str | None = Field(
        None,
        description="Discipline name.",
        examples=["Discipline A"],
        min_length=1,
    )
    discipline_acronym: str | None = Field(
        None,
        description="Discipline acronym.",
        examples=["ABC"],
        min_length=1,
    )


class DocTypeCreate(BaseModel):
    doc_type_name: str = Field(
        ...,
        description="Document type name.",
        examples=["Doc Type A"],
        min_length=1,
    )
    ref_discipline_id: int = Field(
        ...,
        description="Ref Discipline ID.",
        examples=[1],
        gt=0,
    )
    doc_type_acronym: str = Field(
        ...,
        description="Document type acronym.",
        examples=["ABC"],
        min_length=1,
    )


class DocTypeUpdate(BaseModel):
    type_id: int = Field(
        ...,
        description="Type ID.",
        examples=[1],
        gt=0,
    )
    doc_type_name: str | None = Field(
        None,
        description="Document type name.",
        examples=["Doc Type A"],
        min_length=1,
    )
    ref_discipline_id: int | None = Field(
        None,
        description="Ref Discipline ID.",
        examples=[1],
        gt=0,
    )
    doc_type_acronym: str | None = Field(
        None,
        description="Document type acronym.",
        examples=["ABC"],
        min_length=1,
    )


class DocTypeDelete(BaseModel):
    type_id: int = Field(
        ...,
        description="Type ID.",
        examples=[1],
        gt=0,
    )


class DocOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    doc_id: int = Field(
        ...,
        description="Doc ID.",
        examples=[1],
        gt=0,
    )
    doc_name_unique: str = Field(
        ...,
        description="Document unique name.",
        examples=["DOC-001"],
        min_length=1,
    )
    title: str = Field(
        ...,
        description="Document title.",
        examples=["Document Title"],
        min_length=1,
    )
    project_id: int | None = Field(
        None,
        description="Project ID.",
        examples=[1],
        gt=0,
    )
    project_name: str | None = Field(
        None,
        description="Project name.",
        examples=["Project A"],
        min_length=1,
    )
    jobpack_id: int | None = Field(
        None,
        description="Jobpack ID.",
        examples=[1],
        gt=0,
    )
    jobpack_name: str | None = Field(
        None,
        description="Jobpack name.",
        examples=["Jobpack A"],
        min_length=1,
    )
    type_id: int = Field(
        ...,
        description="Type ID.",
        examples=[1],
        gt=0,
    )
    doc_type_name: str | None = Field(
        None,
        description="Document type name.",
        examples=["Doc Type A"],
        min_length=1,
    )
    doc_type_acronym: str | None = Field(
        None,
        description="Document type acronym.",
        examples=["ABC"],
        min_length=1,
    )
    area_id: int = Field(
        ...,
        description="Area ID.",
        examples=[1],
        gt=0,
    )
    area_name: str | None = Field(
        None,
        description="Area name.",
        examples=["Area A"],
        min_length=1,
    )
    area_acronym: str | None = Field(
        None,
        description="Area acronym.",
        examples=["ABC"],
        min_length=1,
    )
    unit_id: int = Field(
        ...,
        description="Unit ID.",
        examples=[1],
        gt=0,
    )
    unit_name: str | None = Field(
        None,
        description="Unit name.",
        examples=["Unit A"],
        min_length=1,
    )
    rev_actual_id: int | None = Field(
        None,
        description="Rev Actual ID.",
        examples=[1],
        gt=0,
    )
    rev_current_id: int | None = Field(
        None,
        description="Rev Current ID.",
        examples=[1],
        gt=0,
    )
    rev_seq_num: int | None = Field(
        None,
        description="Revision sequence number.",
        examples=[1],
        gt=0,
    )
    discipline_id: int | None = Field(
        None,
        description="Discipline ID.",
        examples=[1],
        gt=0,
    )
    discipline_name: str | None = Field(
        None,
        description="Discipline name.",
        examples=["Discipline A"],
        min_length=1,
    )
    discipline_acronym: str | None = Field(
        None,
        description="Discipline acronym.",
        examples=["ABC"],
        min_length=1,
    )
    rev_code_name: str | None = Field(
        None,
        description="Revision code name.",
        examples=["Rev Code A"],
        min_length=1,
    )
    rev_code_acronym: str | None = Field(
        None,
        description="Revision code acronym.",
        examples=["ABC"],
        min_length=1,
    )
    percentage: int | None = Field(
        None,
        description="Completion percentage.",
        examples=[50],
        ge=0,
        le=100,
    )


class DocUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_id: int = Field(
        ...,
        description="Doc ID.",
        examples=[1],
        gt=0,
    )
    doc_name_unique: str | None = Field(
        None,
        description="Document unique name.",
        examples=["DOC-001"],
        min_length=1,
    )
    title: str | None = Field(
        None,
        description="Document title.",
        examples=["Document Title"],
        min_length=1,
    )
    project_id: int | None = Field(
        None,
        description="Project ID.",
        examples=[1],
        gt=0,
    )
    jobpack_id: int | None = Field(
        None,
        description="Jobpack ID.",
        examples=[1],
        gt=0,
    )
    type_id: int | None = Field(
        None,
        description="Type ID.",
        examples=[1],
        gt=0,
    )
    area_id: int | None = Field(
        None,
        description="Area ID.",
        examples=[1],
        gt=0,
    )
    unit_id: int | None = Field(
        None,
        description="Unit ID.",
        examples=[1],
        gt=0,
    )
    rev_actual_id: int | None = Field(
        None,
        description="Rev Actual ID.",
        examples=[1],
        gt=0,
    )
    rev_current_id: int | None = Field(
        None,
        description="Rev Current ID.",
        examples=[1],
        gt=0,
    )


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role_id: int = Field(
        ...,
        description="Role ID.",
        examples=[1],
        gt=0,
    )
    role_name: str = Field(
        ...,
        description="Role name.",
        examples=["Role A"],
        min_length=1,
    )


class RoleUpdate(BaseModel):
    role_id: int = Field(
        ...,
        description="Role ID.",
        examples=[1],
        gt=0,
    )
    role_name: str | None = Field(
        None,
        description="Role name.",
        examples=["Role A"],
        min_length=1,
    )


class RoleCreate(BaseModel):
    role_name: str = Field(
        ...,
        description="Role name.",
        examples=["Role A"],
        min_length=1,
    )


class RoleDelete(BaseModel):
    role_id: int = Field(
        ...,
        description="Role ID.",
        examples=[1],
        gt=0,
    )


class DocRevMilestoneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    milestone_id: int = Field(
        ...,
        description="Milestone ID.",
        examples=[1],
        gt=0,
    )
    milestone_name: str = Field(
        ...,
        description="Milestone name.",
        examples=["Milestone A"],
        min_length=1,
    )
    progress: int | None = Field(
        None,
        description="Progress percentage.",
        examples=[50],
        ge=0,
        le=100,
    )


class DocRevMilestoneUpdate(BaseModel):
    milestone_id: int = Field(
        ...,
        description="Milestone ID.",
        examples=[1],
        gt=0,
    )
    milestone_name: str | None = Field(
        None,
        description="Milestone name.",
        examples=["Milestone A"],
        min_length=1,
    )
    progress: int | None = Field(
        None,
        description="Progress percentage.",
        examples=[50],
        ge=0,
        le=100,
    )


class DocRevMilestoneCreate(BaseModel):
    milestone_name: str = Field(
        ...,
        description="Milestone name.",
        examples=["Milestone A"],
        min_length=1,
    )
    progress: int | None = Field(
        None,
        description="Progress percentage.",
        examples=[50],
        ge=0,
        le=100,
    )


class DocRevMilestoneDelete(BaseModel):
    milestone_id: int = Field(
        ...,
        description="Milestone ID.",
        examples=[1],
        gt=0,
    )


class RevisionOverviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rev_code_id: int = Field(
        ...,
        description="Rev Code ID.",
        examples=[1],
        gt=0,
    )
    rev_code_name: str = Field(
        ...,
        description="Revision code name.",
        examples=["Rev Code A"],
        min_length=1,
    )
    rev_code_acronym: str = Field(
        ...,
        description="Revision code acronym.",
        examples=["ABC"],
        min_length=1,
    )
    rev_description: str = Field(
        ...,
        description="Revision description.",
        examples=["Initial issue."],
        min_length=1,
    )
    percentage: int | None = Field(
        None,
        description="Completion percentage.",
        examples=[50],
        ge=0,
        le=100,
    )


class RevisionOverviewUpdate(BaseModel):
    rev_code_id: int = Field(
        ...,
        description="Rev Code ID.",
        examples=[1],
        gt=0,
    )
    rev_code_name: str | None = Field(
        None,
        description="Revision code name.",
        examples=["Rev Code A"],
        min_length=1,
    )
    rev_code_acronym: str | None = Field(
        None,
        description="Revision code acronym.",
        examples=["ABC"],
        min_length=1,
    )
    rev_description: str | None = Field(
        None,
        description="Revision description.",
        examples=["Initial issue."],
        min_length=1,
    )
    percentage: int | None = Field(
        None,
        description="Completion percentage.",
        examples=[50],
        ge=0,
        le=100,
    )


class RevisionOverviewCreate(BaseModel):
    rev_code_name: str = Field(
        ...,
        description="Revision code name.",
        examples=["Rev Code A"],
        min_length=1,
    )
    rev_code_acronym: str = Field(
        ...,
        description="Revision code acronym.",
        examples=["ABC"],
        min_length=1,
    )
    rev_description: str = Field(
        ...,
        description="Revision description.",
        examples=["Initial issue."],
        min_length=1,
    )
    percentage: int | None = Field(
        None,
        description="Completion percentage.",
        examples=[50],
        ge=0,
        le=100,
    )


class RevisionOverviewDelete(BaseModel):
    rev_code_id: int = Field(
        ...,
        description="Rev Code ID.",
        examples=[1],
        gt=0,
    )


class DocRevStatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rev_status_id: int = Field(
        ...,
        description="Rev Status ID.",
        examples=[1],
        gt=0,
    )
    rev_status_name: str = Field(
        ...,
        description="Revision status name.",
        examples=["Rev Status A"],
        min_length=1,
    )


class DocRevStatusUpdate(BaseModel):
    rev_status_id: int = Field(
        ...,
        description="Rev Status ID.",
        examples=[1],
        gt=0,
    )
    rev_status_name: str | None = Field(
        None,
        description="Revision status name.",
        examples=["Rev Status A"],
        min_length=1,
    )


class DocRevStatusCreate(BaseModel):
    rev_status_name: str = Field(
        ...,
        description="Revision status name.",
        examples=["Rev Status A"],
        min_length=1,
    )


class DocRevStatusDelete(BaseModel):
    rev_status_id: int = Field(
        ...,
        description="Rev Status ID.",
        examples=[1],
        gt=0,
    )


class FileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(
        ...,
        description="Id.",
        examples=[1],
        gt=0,
    )
    filename: str = Field(
        ...,
        description="Filename.",
        examples=["Example"],
        min_length=1,
    )
    s3_uid: str = Field(
        ...,
        description="S3 object key.",
        examples=["bucket/path/file.pdf"],
        min_length=1,
    )
    mimetype: str = Field(
        ...,
        description="File MIME type.",
        examples=["application/pdf"],
        min_length=1,
    )
    rev_id: int = Field(
        ...,
        description="Rev ID.",
        examples=[1],
        gt=0,
    )


class FileUpdate(BaseModel):
    id: int = Field(
        ...,
        description="Id.",
        examples=[1],
        gt=0,
    )
    filename: str = Field(
        ...,
        description="Filename.",
        examples=["Example"],
        min_length=1,
    )


class FileDelete(BaseModel):
    id: int = Field(
        ...,
        description="Id.",
        examples=[1],
        gt=0,
    )


class PersonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    person_id: int = Field(
        ...,
        description="Person ID.",
        examples=[1],
        gt=0,
    )
    person_name: str = Field(
        ...,
        description="Person name.",
        examples=["Person A"],
        min_length=1,
    )
    photo_s3_uid: str | None = Field(
        None,
        description="Photo S3 object key.",
        examples=["bucket/photos/person.jpg"],
        min_length=1,
    )


class PersonUpdate(BaseModel):
    person_id: int = Field(
        ...,
        description="Person ID.",
        examples=[1],
        gt=0,
    )
    person_name: str | None = Field(
        None,
        description="Person name.",
        examples=["Person A"],
        min_length=1,
    )
    photo_s3_uid: str | None = Field(
        None,
        description="Photo S3 object key.",
        examples=["bucket/photos/person.jpg"],
        min_length=1,
    )


class PersonCreate(BaseModel):
    person_name: str = Field(
        ...,
        description="Person name.",
        examples=["Person A"],
        min_length=1,
    )
    photo_s3_uid: str | None = Field(
        None,
        description="Photo S3 object key.",
        examples=["bucket/photos/person.jpg"],
        min_length=1,
    )


class PersonDelete(BaseModel):
    person_id: int = Field(
        ...,
        description="Person ID.",
        examples=[1],
        gt=0,
    )


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int = Field(
        ...,
        description="User ID.",
        examples=[1],
        gt=0,
    )
    person_id: int = Field(
        ...,
        description="Person ID.",
        examples=[1],
        gt=0,
    )
    user_acronym: str = Field(
        ...,
        description="User acronym.",
        examples=["ABC"],
        min_length=1,
    )
    role_id: int = Field(
        ...,
        description="Role ID.",
        examples=[1],
        gt=0,
    )
    person_name: str | None = Field(
        None,
        description="Person name.",
        examples=["Person A"],
        min_length=1,
    )
    role_name: str | None = Field(
        None,
        description="Role name.",
        examples=["Role A"],
        min_length=1,
    )


class UserUpdate(BaseModel):
    user_id: int = Field(
        ...,
        description="User ID.",
        examples=[1],
        gt=0,
    )
    person_id: int | None = Field(
        None,
        description="Person ID.",
        examples=[1],
        gt=0,
    )
    user_acronym: str | None = Field(
        None,
        description="User acronym.",
        examples=["ABC"],
        min_length=1,
    )
    role_id: int | None = Field(
        None,
        description="Role ID.",
        examples=[1],
        gt=0,
    )


class UserCreate(BaseModel):
    person_id: int = Field(
        ...,
        description="Person ID.",
        examples=[1],
        gt=0,
    )
    user_acronym: str = Field(
        ...,
        description="User acronym.",
        examples=["ABC"],
        min_length=1,
    )
    role_id: int = Field(
        ...,
        description="Role ID.",
        examples=[1],
        gt=0,
    )


class UserDelete(BaseModel):
    user_id: int = Field(
        ...,
        description="User ID.",
        examples=[1],
        gt=0,
    )


class PermissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    permission_id: int = Field(
        ...,
        description="Permission ID.",
        examples=[1],
        gt=0,
    )
    user_id: int = Field(
        ...,
        description="User ID.",
        examples=[1],
        gt=0,
    )
    project_id: int | None = Field(
        None,
        description="Project ID.",
        examples=[1],
        gt=0,
    )
    discipline_id: int | None = Field(
        None,
        description="Discipline ID.",
        examples=[1],
        gt=0,
    )
    user_acronym: str | None = Field(
        None,
        description="User acronym.",
        examples=["ABC"],
        min_length=1,
    )
    person_name: str | None = Field(
        None,
        description="Person name.",
        examples=["Person A"],
        min_length=1,
    )
    project_name: str | None = Field(
        None,
        description="Project name.",
        examples=["Project A"],
        min_length=1,
    )
    discipline_name: str | None = Field(
        None,
        description="Discipline name.",
        examples=["Discipline A"],
        min_length=1,
    )


class PermissionCreate(BaseModel):
    user_id: int = Field(
        ...,
        description="User ID.",
        examples=[1],
        gt=0,
    )
    project_id: int | None = Field(
        None,
        description="Project ID.",
        examples=[1],
        gt=0,
    )
    discipline_id: int | None = Field(
        None,
        description="Discipline ID.",
        examples=[1],
        gt=0,
    )

    def validate_scope(self) -> None:
        if self.project_id is None and self.discipline_id is None:
            raise HTTPException(status_code=400, detail="Provide project_id or discipline_id")


class PermissionDelete(BaseModel):
    permission_id: int | None = Field(
        None,
        description="Permission ID.",
        examples=[1],
        gt=0,
    )
    user_id: int = Field(
        ...,
        description="User ID.",
        examples=[1],
        gt=0,
    )
    project_id: int | None = Field(
        None,
        description="Project ID.",
        examples=[1],
        gt=0,
    )
    discipline_id: int | None = Field(
        None,
        description="Discipline ID.",
        examples=[1],
        gt=0,
    )

    def validate_scope(self) -> None:
        if self.permission_id is None and self.project_id is None and self.discipline_id is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Provide permission_id or project_id/discipline_id to identify the permission"
                ),
            )


class PermissionUpdate(BaseModel):
    permission_id: int | None = Field(
        None,
        description="Permission ID.",
        examples=[1],
        gt=0,
    )
    user_id: int = Field(
        ...,
        description="User ID.",
        examples=[1],
        gt=0,
    )
    project_id: int | None = Field(
        None,
        description="Project ID.",
        examples=[1],
        gt=0,
    )
    discipline_id: int | None = Field(
        None,
        description="Discipline ID.",
        examples=[1],
        gt=0,
    )
    new_project_id: int | None = Field(
        None,
        description="New Project ID.",
        examples=[1],
        gt=0,
    )
    new_discipline_id: int | None = Field(
        None,
        description="New Discipline ID.",
        examples=[1],
        gt=0,
    )

    def validate_current(self) -> None:
        if self.project_id is None and self.discipline_id is None:
            raise HTTPException(
                status_code=400, detail="Provide current project_id or discipline_id"
            )


def get_db() -> Iterable[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get(
    "/",
    summary="Root endpoint returning a welcome message.",
    description="Returns a simple message indicating the Flow backend is operational.",
    operation_id="read_root",
    tags=["system"],
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
def read_root() -> dict[str, str]:
    """
    Root endpoint returning a welcome message.

    Returns a simple message indicating the Flow backend is operational.

    Returns:
        dict[str, str]: A message confirming the Flow backend is running.
    """
    return {"message": "Flow backend is running"}


@app.get(
    "/health",
    summary="Health check endpoint.",
    description="Returns the health status of the API service.",
    operation_id="health",
    tags=["system"],
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
def health() -> dict[str, str]:
    """
    Health check endpoint.

    Returns the health status of the API service.

    Returns:
        dict[str, str]: A status message indicating that the API service is healthy.
    """
    return {"status": "ok"}


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


@app.get(
    "/api/v1/lookups/areas",
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


@app.put(
    "/api/v1/lookups/areas/update",
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


@app.post(
    "/api/v1/lookups/areas/insert",
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


@app.delete(
    "/api/v1/lookups/areas/delete",
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


@app.get(
    "/api/v1/lookups/disciplines",
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


@app.put(
    "/api/v1/lookups/disciplines/update",
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


@app.post(
    "/api/v1/lookups/disciplines/insert",
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


@app.delete(
    "/api/v1/lookups/disciplines/delete",
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


@app.get(
    "/api/v1/lookups/projects",
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


@app.put(
    "/api/v1/lookups/projects/update",
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


@app.post(
    "/api/v1/lookups/projects/insert",
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


@app.delete(
    "/api/v1/lookups/projects/delete",
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


@app.get(
    "/api/v1/lookups/units",
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


@app.put(
    "/api/v1/lookups/units/update",
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


@app.post(
    "/api/v1/lookups/units/insert",
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


@app.delete(
    "/api/v1/lookups/units/delete",
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


@app.get(
    "/api/v1/lookups/jobpacks",
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


@app.put(
    "/api/v1/lookups/jobpacks/update",
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


@app.post(
    "/api/v1/lookups/jobpacks/insert",
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


@app.delete(
    "/api/v1/lookups/jobpacks/delete",
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


@app.get(
    "/api/v1/documents/doc_types",
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


@app.post(
    "/api/v1/documents/doc_types/insert",
    summary="Create a new document type.",
    description=(
        "Inserts a new document type with the specified name, acronym, and discipline reference."
    ),
    operation_id="insert_doc_type",
    tags=["documents"],
    response_model=DocTypeOut,
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
def insert_doc_type(
    payload: DocTypeCreate = Body(..., examples=_example_for(DocTypeCreate)),
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


@app.put(
    "/api/v1/documents/doc_types/update",
    summary="Update an existing document type.",
    description=(
        "Updates the name, acronym, and/or discipline reference of an existing document type."
    ),
    operation_id="update_doc_type",
    tags=["documents"],
    response_model=DocTypeOut,
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
def update_doc_type(
    payload: DocTypeUpdate = Body(..., examples=_example_for(DocTypeUpdate)),
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


@app.delete(
    "/api/v1/documents/doc_types/delete",
    summary="Delete a document type.",
    description="Removes a document type from the database by its ID.",
    operation_id="delete_doc_type",
    tags=["documents"],
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
def delete_doc_type(
    payload: DocTypeDelete = Body(..., examples=_example_for(DocTypeDelete)),
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


@app.get(
    "/api/v1/documents/list",
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


@app.get(
    "/api/v1/files/list",
    summary="List all files for a specific revision.",
    description="Returns a list of all files associated with the specified document revision.",
    operation_id="list_files_for_revision",
    tags=["files"],
    response_model=list[FileOut],
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
def list_files_for_revision(
    rev_id: int = Query(..., description="Revision ID to filter files by"),
    db: Session = Depends(get_db),
) -> list[FileOut]:
    """
    List all files for a specific revision.

    Returns a list of all files associated with the specified document revision.

    Args:
        rev_id: The revision ID to filter files by.

    Returns:
        List of files with metadata. If no files exist for the specified revision, an empty list is
        returned.
    """
    files = db.query(File).filter(File.rev_id == rev_id).order_by(File.filename, File.id).all()
    return _model_list(FileOut, files)


@app.post(
    "/api/v1/files/insert",
    summary="Upload a file and attach it to a document revision.",
    description=(
        "Uploads a file to MinIO object storage and creates a database record linking it to the "
        "specified document revision."
    ),
    operation_id="insert_file",
    tags=["files"],
    response_model=FileOut,
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
def insert_file(
    request: Request,
    rev_id: int = Form(..., description="Revision ID to attach the file to"),
    file: UploadFile = UploadFileField(...),
    db: Session = Depends(get_db),
) -> FileOut:
    """
    Upload a file and attach it to a document revision.

    Uploads a file to MinIO object storage and creates a database record linking it to the specified
    document revision.

    Args:
        request: Incoming request used for logging the client host.
        rev_id: The revision ID to attach the file to.
        file: The uploaded file (multipart form data).

    Returns:
        Newly created file record with metadata.

    Raises:
        HTTPException: 400 if filename is missing, too long, or file is empty.
        HTTPException: 404 if revision not found.
        HTTPException: 413 if file exceeds size limit.
    """
    revision = db.get(DocRevision, rev_id)
    if not revision:
        raise HTTPException(status_code=404, detail="Revision not found")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    filename = os.path.basename(file.filename)
    if len(filename) > 90:
        raise HTTPException(status_code=400, detail="Filename too long (max 90 chars)")

    content_type = file.content_type or "application/octet-stream"
    stream = file.file
    size = None
    if hasattr(stream, "seekable") and stream.seekable():
        stream.seek(0, os.SEEK_END)
        size = stream.tell()
        stream.seek(0)
        if size <= 0:
            raise HTTPException(status_code=400, detail="File is empty")
        max_size_mb = int(os.getenv("MAX_UPLOAD_SIZE_MB", "128"))
        max_size_bytes = max_size_mb * 1024 * 1024
        if max_size_mb > 0 and size > max_size_bytes:
            raise HTTPException(status_code=413, detail="File exceeds upload size limit")

    doc = revision.doc
    project_name = doc.project.project_name if doc and doc.project else None
    doc_name = doc.doc_name_unique if doc else f"doc_{revision.doc_id}"
    object_key = _build_file_object_key(
        project_name=project_name,
        doc_name_unique=doc_name,
        transmittal_current_revision=revision.transmittal_current_revision,
        unique_id=uuid.uuid4().hex,
        filename=filename,
    )
    client, bucket = _build_minio_client()
    endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    if not _minio_with_retry("bucket_exists", endpoint, lambda: client.bucket_exists(bucket)):
        _minio_with_retry("make_bucket", endpoint, lambda: client.make_bucket(bucket))
    if size is None:
        _minio_with_retry(
            "put_object",
            endpoint,
            lambda: client.put_object(
                bucket,
                object_key,
                stream,
                length=-1,
                part_size=10 * 1024 * 1024,
                content_type=content_type,
            ),
        )
    else:
        _minio_with_retry(
            "put_object",
            endpoint,
            lambda: client.put_object(
                bucket, object_key, stream, length=size, content_type=content_type
            ),
        )

    new_file = File(
        filename=filename,
        s3_uid=object_key,
        mimetype=content_type,
        rev_id=rev_id,
    )
    db.add(new_file)
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        try:
            _minio_with_retry(
                "remove_object",
                endpoint,
                lambda: client.remove_object(bucket, object_key),
            )
        except HTTPException:
            logger.exception("Failed to cleanup MinIO object after DB error")
        _handle_integrity_error("Failed to create file record", err, "insert_file")

    db.refresh(new_file)
    client_host = request.client.host if request.client else "unknown"
    logger.info(
        "File uploaded rev_id=%s file_id=%s filename=%s client=%s",
        rev_id,
        new_file.id,
        filename,
        client_host,
    )
    return _model_out(FileOut, new_file)


@app.put(
    "/api/v1/files/update",
    summary="Update file metadata.",
    description=(
        "Updates the filename of an existing file record (does not update the actual file "
        "content)."
    ),
    operation_id="update_file",
    tags=["files"],
    response_model=FileOut,
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
def update_file(
    payload: FileUpdate = Body(..., examples=_example_for(FileUpdate)),
    db: Session = Depends(get_db),
) -> FileOut:
    """
    Update file metadata.

    Updates the filename of an existing file record (does not update the actual file content).

    Args:
        payload: File update data including file id and new filename.

    Returns:
        Updated file record.

    Raises:
        HTTPException: 400 if filename is empty or too long.
        HTTPException: 404 if file not found.
    """
    filename = payload.filename.strip()
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    if len(filename) > 90:
        raise HTTPException(status_code=400, detail="Filename too long (max 90 chars)")

    file_row = db.get(File, payload.id)
    if not file_row:
        raise HTTPException(status_code=404, detail="File not found")

    file_row.filename = filename
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Failed to update file", err, "update_file")

    db.refresh(file_row)
    return _model_out(FileOut, file_row)


@app.delete(
    "/api/v1/files/delete",
    summary="Delete a file.",
    description="Removes a file from both the MinIO object storage and the database.",
    operation_id="delete_file",
    tags=["files"],
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
def delete_file(
    request: Request,
    payload: FileDelete = Body(..., examples=_example_for(FileDelete)),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a file.

    Removes a file from both the MinIO object storage and the database.

    Args:
        payload: File deletion data including file id.
        request: Incoming request used for logging the client host.

    Raises:
        HTTPException: 404 if file not found.
    """
    file_row = db.get(File, payload.id)
    if not file_row:
        raise HTTPException(status_code=404, detail="File not found")

    client, bucket = _build_minio_client()
    endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    _minio_with_retry(
        "remove_object",
        endpoint,
        lambda: client.remove_object(bucket, file_row.s3_uid),
    )

    db.delete(file_row)
    db.commit()
    client_host = request.client.host if request.client else "unknown"
    logger.info(
        "File deleted file_id=%s s3_uid=%s client=%s",
        payload.id,
        file_row.s3_uid,
        client_host,
    )


@app.get(
    "/api/v1/files/download",
    summary="Download a file.",
    description=(
        "Streams a file from MinIO object storage to the client with proper headers for download "
        "(Content-Disposition, ETag, Last-Modified)."
    ),
    operation_id="download_file",
    tags=["files"],
    responses={
        200: {
            "description": "File content.",
            "content": {
                "application/octet-stream": {
                    "schema": {"type": "string", "format": "binary"},
                },
            },
        },
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
def download_file(
    request: Request,
    file_id: int = Query(..., description="File ID to download"),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    Download a file.

    Streams a file from MinIO object storage to the client with proper headers for download
    (Content-Disposition, ETag, Last-Modified).

    Args:
        request: Incoming request used for logging the client host.
        file_id: The ID of the file to download.

    Returns:
        Streaming response with the file content.

    Raises:
        HTTPException: 404 if file not found.
    """
    file_row = db.get(File, file_id)
    if not file_row:
        raise HTTPException(status_code=404, detail="File not found")

    client, bucket = _build_minio_client()
    endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    response = _minio_with_retry(
        "get_object",
        endpoint,
        lambda: client.get_object(bucket, file_row.s3_uid),
    )
    stat = _minio_with_retry(
        "stat_object",
        endpoint,
        lambda: client.stat_object(bucket, file_row.s3_uid),
    )

    safe_name = (
        file_row.filename.replace('"', "'")
        .replace("\r", "")
        .replace("\n", "")
        .encode("latin-1", "ignore")
        .decode("latin-1")
    )
    quoted_name = quote(file_row.filename)
    headers = {
        "Content-Disposition": (
            "attachment; filename=\"{}\"; filename*=UTF-8''{}".format(
                safe_name,
                quoted_name,
            )
        )
    }
    if stat.etag:
        etag = stat.etag.strip('"')
        headers["ETag"] = f'"{etag}"'
    if stat.last_modified:
        headers["Last-Modified"] = formatdate(stat.last_modified.timestamp(), usegmt=True)
    client_host = request.client.host if request.client else "unknown"
    logger.info(
        "File download file_id=%s s3_uid=%s client=%s",
        file_row.id,
        file_row.s3_uid,
        client_host,
    )
    return StreamingResponse(
        response,
        media_type=file_row.mimetype or "application/octet-stream",
        headers=headers,
        background=BackgroundTask(_close_minio_response, response),
    )


@app.put(
    "/api/v1/documents/update",
    summary="Update an existing document.",
    description=(
        "Updates various fields of an existing document including name, title, project, jobpack, "
        "type, area, unit, and revision references. Validates all foreign key references and "
        "ensures document name uniqueness."
    ),
    operation_id="update_document",
    tags=["documents"],
    response_model=DocOut,
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
def update_document(
    payload: DocUpdate = Body(..., examples=_example_for(DocUpdate)),
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

    def require_not_null(field_name: str, value: object) -> None:
        if value is None:
            raise HTTPException(status_code=400, detail=f"{field_name} cannot be null")

    if "doc_name_unique" in updates:
        require_not_null("doc_name_unique", payload.doc_name_unique)
        doc.doc_name_unique = payload.doc_name_unique

    if "title" in updates:
        require_not_null("title", payload.title)
        doc.title = payload.title

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
    discipline: Discipline | None = doc_type.discipline if doc_type else None
    if "type_id" in updates:
        type_id = payload.type_id
        require_not_null("type_id", type_id)
        doc_type = db.get(DocType, type_id)
        if not doc_type:
            raise HTTPException(status_code=404, detail="Doc type not found")
        discipline = doc_type.discipline
        doc.type_id = type_id
        doc.doc_type = doc_type

    area: Area | None = doc.area
    if "area_id" in updates:
        area_id = payload.area_id
        require_not_null("area_id", area_id)
        area = db.get(Area, area_id)
        if not area:
            raise HTTPException(status_code=404, detail="Area not found")
        doc.area_id = area_id
        doc.area = area

    unit: Unit | None = doc.unit
    if "unit_id" in updates:
        unit_id = payload.unit_id
        require_not_null("unit_id", unit_id)
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


@app.get(
    "/api/v1/people/roles",
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


@app.put(
    "/api/v1/people/roles/update",
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
        payload: Role update data including role_id and new role_name.

    Returns:
        Updated role object.

    Raises:
        HTTPException: 400 if no fields provided or role name already exists.
        HTTPException: 404 if role not found.
    """
    if payload.role_name is None:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    role = db.get(Role, payload.role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    role.role_name = payload.role_name or role.role_name

    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Role name already exists", err, "update_role")

    db.refresh(role)
    return _model_out(RoleOut, role)


@app.post(
    "/api/v1/people/roles/insert",
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
        payload: Role creation data including role_name.

    Returns:
        Newly created role object.

    Raises:
        HTTPException: 400 if role name already exists.
    """
    role = Role(role_name=payload.role_name)
    db.add(role)
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Role name already exists", err, "insert_role")
    db.refresh(role)
    return _model_out(RoleOut, role)


@app.delete(
    "/api/v1/people/roles/delete",
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


@app.get(
    "/api/v1/documents/doc_rev_milestones",
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


@app.put(
    "/api/v1/documents/doc_rev_milestones/update",
    summary="Update an existing document revision milestone.",
    description="Updates the name and/or progress percentage of an existing milestone.",
    operation_id="update_doc_rev_milestone",
    tags=["documents"],
    response_model=DocRevMilestoneOut,
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
def update_doc_rev_milestone(
    payload: DocRevMilestoneUpdate = Body(..., examples=_example_for(DocRevMilestoneUpdate)),
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


@app.post(
    "/api/v1/documents/doc_rev_milestones/insert",
    summary="Create a new document revision milestone.",
    description="Inserts a new milestone with the specified name and optional progress percentage.",
    operation_id="insert_doc_rev_milestone",
    tags=["documents"],
    response_model=DocRevMilestoneOut,
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
def insert_doc_rev_milestone(
    payload: DocRevMilestoneCreate = Body(..., examples=_example_for(DocRevMilestoneCreate)),
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


@app.delete(
    "/api/v1/documents/doc_rev_milestones/delete",
    summary="Delete a document revision milestone.",
    description="Removes a milestone from the database by its ID.",
    operation_id="delete_doc_rev_milestone",
    tags=["documents"],
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
def delete_doc_rev_milestone(
    payload: DocRevMilestoneDelete = Body(..., examples=_example_for(DocRevMilestoneDelete)),
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


@app.get(
    "/api/v1/documents/revision_overview",
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


@app.put(
    "/api/v1/documents/revision_overview/update",
    summary="Update an existing revision overview entry.",
    description=(
        "Updates the name, acronym, description, and/or percentage of an existing revision "
        "overview entry."
    ),
    operation_id="update_revision_overview",
    tags=["documents"],
    response_model=RevisionOverviewOut,
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
def update_revision_overview(
    payload: RevisionOverviewUpdate = Body(..., examples=_example_for(RevisionOverviewUpdate)),
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


@app.post(
    "/api/v1/documents/revision_overview/insert",
    summary="Create a new revision overview entry.",
    description=(
        "Inserts a new revision overview entry with the specified code, acronym, description, and "
        "percentage."
    ),
    operation_id="insert_revision_overview",
    tags=["documents"],
    response_model=RevisionOverviewOut,
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
def insert_revision_overview(
    payload: RevisionOverviewCreate = Body(..., examples=_example_for(RevisionOverviewCreate)),
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


@app.delete(
    "/api/v1/documents/revision_overview/delete",
    summary="Delete a revision overview entry.",
    description="Removes a revision overview entry from the database by its ID.",
    operation_id="delete_revision_overview",
    tags=["documents"],
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
def delete_revision_overview(
    payload: RevisionOverviewDelete = Body(..., examples=_example_for(RevisionOverviewDelete)),
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


@app.get(
    "/api/v1/lookups/doc_rev_statuses",
    summary="List all document revision statuses.",
    description="Returns a list of all document revision statuses sorted by status name.",
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

    Returns a list of all document revision statuses sorted by status name.

    Returns:
        List of statuses with id and name.

    Raises:
        HTTPException: 404 if no document revision statuses are found.
    """
    statuses = db.query(DocRevStatus).order_by(DocRevStatus.rev_status_name).all()
    if not statuses:
        raise HTTPException(status_code=404, detail="No doc revision statuses found")
    return _model_list(DocRevStatusOut, statuses)


@app.put(
    "/api/v1/lookups/doc_rev_statuses/update",
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
        payload: Status update data including rev_status_id and new rev_status_name.

    Returns:
        Updated status object.

    Raises:
        HTTPException: 400 if no fields provided or status already exists.
        HTTPException: 404 if status not found.
    """
    if payload.rev_status_name is None:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    status = db.get(DocRevStatus, payload.rev_status_id)
    if not status:
        raise HTTPException(status_code=404, detail="Doc revision status not found")

    if payload.rev_status_name is not None:
        status.rev_status_name = payload.rev_status_name

    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Doc revision status already exists", err, "update_doc_rev_status")

    db.refresh(status)
    return _model_out(DocRevStatusOut, status)


@app.post(
    "/api/v1/lookups/doc_rev_statuses/insert",
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
        payload: Status creation data including rev_status_name.

    Returns:
        Newly created status object.

    Raises:
        HTTPException: 400 if status already exists.
    """
    status = DocRevStatus(rev_status_name=payload.rev_status_name)
    db.add(status)
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Doc revision status already exists", err, "insert_doc_rev_status")
    db.refresh(status)
    return _model_out(DocRevStatusOut, status)


@app.delete(
    "/api/v1/lookups/doc_rev_statuses/delete",
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
        payload: Status deletion data including rev_status_id.

    Raises:
        HTTPException: 404 if status not found.
    """
    status = db.get(DocRevStatus, payload.rev_status_id)
    if not status:
        raise HTTPException(status_code=404, detail="Doc revision status not found")
    db.delete(status)
    db.commit()


@app.get(
    "/api/v1/people/persons",
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


@app.put(
    "/api/v1/people/persons/update",
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


@app.post(
    "/api/v1/people/persons/insert",
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


@app.delete(
    "/api/v1/people/persons/delete",
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


@app.get(
    "/api/v1/people/users",
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


@app.put(
    "/api/v1/people/users/update",
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


@app.post(
    "/api/v1/people/users/insert",
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


@app.delete(
    "/api/v1/people/users/delete",
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


@app.get(
    "/api/v1/people/permissions",
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


@app.post(
    "/api/v1/people/permissions/insert",
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


@app.put(
    "/api/v1/people/permissions/update",
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


@app.delete(
    "/api/v1/people/permissions/delete",
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


def _sync_route_descriptions() -> None:
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        doc = inspect.getdoc(route.endpoint)
        if doc:
            route.description = doc


def _custom_openapi() -> dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema

    _sync_route_descriptions()
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = _custom_openapi
