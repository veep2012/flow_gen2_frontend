import os
from typing import Iterable

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from db.models import (
    Area,
    Discipline,
    DocRevMilestone,
    DocRevStatus,
    Jobpack,
    Permission,
    Person,
    Project,
    RevisionOverview,
    Role,
    Unit,
    User,
)


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://flow_user:flow_pass@postgres:5432/flow_db",
)

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


app = FastAPI(title="Flow Backend", version="0.1.0")

allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

# Wildcard cannot be used with credentials. Disable credentials when "*" is present to stay spec-compliant.
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

    area_id: int
    area_name: str
    area_acronym: str


class AreaUpdate(BaseModel):
    area_id: int
    area_name: str | None = None
    area_acronym: str | None = None


class AreaCreate(BaseModel):
    area_name: str
    area_acronym: str


class AreaDelete(BaseModel):
    area_id: int


class DisciplineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    discipline_id: int
    discipline_name: str
    discipline_acronym: str


class DisciplineUpdate(BaseModel):
    discipline_id: int
    discipline_name: str | None = None
    discipline_acronym: str | None = None


class DisciplineCreate(BaseModel):
    discipline_name: str
    discipline_acronym: str


class DisciplineDelete(BaseModel):
    discipline_id: int


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_id: int
    project_name: str


class ProjectUpdate(BaseModel):
    project_id: int
    project_name: str | None = None


class ProjectCreate(BaseModel):
    project_name: str


class ProjectDelete(BaseModel):
    project_id: int


class UnitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    unit_id: int
    unit_name: str


class UnitUpdate(BaseModel):
    unit_id: int
    unit_name: str | None = None


class UnitCreate(BaseModel):
    unit_name: str


class UnitDelete(BaseModel):
    unit_id: int


class JobpackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    jobpack_id: int
    jobpack_name: str


class JobpackUpdate(BaseModel):
    jobpack_id: int
    jobpack_name: str | None = None


class JobpackCreate(BaseModel):
    jobpack_name: str


class JobpackDelete(BaseModel):
    jobpack_id: int


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role_id: int
    role_name: str


class RoleUpdate(BaseModel):
    role_id: int
    role_name: str | None = None


class RoleCreate(BaseModel):
    role_name: str


class RoleDelete(BaseModel):
    role_id: int


class DocRevMilestoneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    milestone_id: int
    milestone_name: str
    progress: int | None = None


class DocRevMilestoneUpdate(BaseModel):
    milestone_id: int
    milestone_name: str | None = None
    progress: int | None = None


class DocRevMilestoneCreate(BaseModel):
    milestone_name: str
    progress: int | None = None


class DocRevMilestoneDelete(BaseModel):
    milestone_id: int


class RevisionOverviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rev_code_id: int
    rev_code_name: str
    rev_code_acronym: str
    rev_description: str
    percentage: int | None = None


class RevisionOverviewUpdate(BaseModel):
    rev_code_id: int
    rev_code_name: str | None = None
    rev_code_acronym: str | None = None
    rev_description: str | None = None
    percentage: int | None = None


class RevisionOverviewCreate(BaseModel):
    rev_code_name: str
    rev_code_acronym: str
    rev_description: str
    percentage: int | None = None


class RevisionOverviewDelete(BaseModel):
    rev_code_id: int


class DocRevStatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rev_status_id: int
    rev_status_name: str


class DocRevStatusUpdate(BaseModel):
    rev_status_id: int
    rev_status_name: str | None = None


class DocRevStatusCreate(BaseModel):
    rev_status_name: str


class DocRevStatusDelete(BaseModel):
    rev_status_id: int


class PersonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    person_id: int
    person_name: str
    photo_s3_uid: str | None = None


class PersonUpdate(BaseModel):
    person_id: int
    person_name: str | None = None
    photo_s3_uid: str | None = None


class PersonCreate(BaseModel):
    person_name: str
    photo_s3_uid: str | None = None


class PersonDelete(BaseModel):
    person_id: int


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    person_id: int
    user_acronym: str
    role_id: int


class UserUpdate(BaseModel):
    user_id: int
    person_id: int | None = None
    user_acronym: str | None = None
    role_id: int | None = None


class UserCreate(BaseModel):
    person_id: int
    user_acronym: str
    role_id: int


class UserDelete(BaseModel):
    user_id: int


class PermissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    permission_id: int
    user_id: int
    project_id: int | None = None
    discipline_id: int | None = None


class PermissionCreate(BaseModel):
    user_id: int
    project_id: int | None = None
    discipline_id: int | None = None

    def validate_scope(self) -> None:
        if self.project_id is None and self.discipline_id is None:
            raise HTTPException(status_code=400, detail="Provide project_id or discipline_id")


class PermissionDelete(BaseModel):
    permission_id: int | None = None
    user_id: int
    project_id: int | None = None
    discipline_id: int | None = None

    def validate_scope(self) -> None:
        if self.permission_id is None and self.project_id is None and self.discipline_id is None:
            raise HTTPException(
                status_code=400,
                detail="Provide permission_id or project_id/discipline_id to identify the permission",
            )


class PermissionUpdate(BaseModel):
    permission_id: int | None = None
    user_id: int
    project_id: int | None = None
    discipline_id: int | None = None
    new_project_id: int | None = None
    new_discipline_id: int | None = None

    def validate_current(self) -> None:
        if self.project_id is None and self.discipline_id is None:
            raise HTTPException(status_code=400, detail="Provide current project_id or discipline_id")


def get_db() -> Iterable[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Flow backend is running"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/lookups/areas", response_model=list[AreaOut])
def list_areas(db: Session = Depends(get_db)) -> list[Area]:
    areas = db.query(Area).order_by(Area.area_name).all()
    if not areas:
        raise HTTPException(status_code=404, detail="No areas found")
    return areas


@app.post("/api/v1/lookups/areas/update", response_model=AreaOut)
def update_area(payload: AreaUpdate, db: Session = Depends(get_db)) -> Area:
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
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Area name or acronym already exists")

    db.refresh(area)
    return area


@app.post("/api/v1/lookups/areas/insert", response_model=AreaOut, status_code=201)
def insert_area(payload: AreaCreate, db: Session = Depends(get_db)) -> Area:
    area = Area(area_name=payload.area_name, area_acronym=payload.area_acronym)
    db.add(area)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Area name or acronym already exists")
    db.refresh(area)
    return area


@app.post("/api/v1/lookups/areas/delete", status_code=204)
def delete_area(payload: AreaDelete, db: Session = Depends(get_db)) -> None:
    area = db.get(Area, payload.area_id)
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")
    db.delete(area)
    db.commit()


@app.get("/api/v1/lookups/disciplines", response_model=list[DisciplineOut])
def list_disciplines(db: Session = Depends(get_db)) -> list[Discipline]:
    disciplines = db.query(Discipline).order_by(Discipline.discipline_name).all()
    if not disciplines:
        raise HTTPException(status_code=404, detail="No disciplines found")
    return disciplines


@app.post("/api/v1/lookups/disciplines/update", response_model=DisciplineOut)
def update_discipline(payload: DisciplineUpdate, db: Session = Depends(get_db)) -> Discipline:
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
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Discipline name or acronym already exists",
        )

    db.refresh(discipline)
    return discipline


@app.post("/api/v1/lookups/disciplines/insert", response_model=DisciplineOut, status_code=201)
def insert_discipline(payload: DisciplineCreate, db: Session = Depends(get_db)) -> Discipline:
    discipline = Discipline(
        discipline_name=payload.discipline_name,
        discipline_acronym=payload.discipline_acronym,
    )
    db.add(discipline)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Discipline name or acronym already exists",
        )
    db.refresh(discipline)
    return discipline


@app.post("/api/v1/lookups/disciplines/delete", status_code=204)
def delete_discipline(payload: DisciplineDelete, db: Session = Depends(get_db)) -> None:
    discipline = db.get(Discipline, payload.discipline_id)
    if not discipline:
        raise HTTPException(status_code=404, detail="Discipline not found")
    db.delete(discipline)
    db.commit()


@app.get("/api/v1/lookups/projects", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)) -> list[Project]:
    projects = db.query(Project).order_by(Project.project_name).all()
    if not projects:
        raise HTTPException(status_code=404, detail="No projects found")
    return projects


@app.post("/api/v1/lookups/projects/update", response_model=ProjectOut)
def update_project(payload: ProjectUpdate, db: Session = Depends(get_db)) -> Project:
    if payload.project_name is None:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    project = db.get(Project, payload.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if payload.project_name is not None:
        project.project_name = payload.project_name

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Project name already exists")

    db.refresh(project)
    return project


@app.post("/api/v1/lookups/projects/insert", response_model=ProjectOut, status_code=201)
def insert_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> Project:
    project = Project(project_name=payload.project_name)
    db.add(project)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Project name already exists")
    db.refresh(project)
    return project


@app.post("/api/v1/lookups/projects/delete", status_code=204)
def delete_project(payload: ProjectDelete, db: Session = Depends(get_db)) -> None:
    project = db.get(Project, payload.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()


@app.get("/api/v1/lookups/units", response_model=list[UnitOut])
def list_units(db: Session = Depends(get_db)) -> list[Unit]:
    units = db.query(Unit).order_by(Unit.unit_name).all()
    if not units:
        raise HTTPException(status_code=404, detail="No units found")
    return units


@app.post("/api/v1/lookups/units/update", response_model=UnitOut)
def update_unit(payload: UnitUpdate, db: Session = Depends(get_db)) -> Unit:
    if payload.unit_name is None:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    unit = db.get(Unit, payload.unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    if payload.unit_name is not None:
        unit.unit_name = payload.unit_name

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Unit name already exists")

    db.refresh(unit)
    return unit


@app.post("/api/v1/lookups/units/insert", response_model=UnitOut, status_code=201)
def insert_unit(payload: UnitCreate, db: Session = Depends(get_db)) -> Unit:
    unit = Unit(unit_name=payload.unit_name)
    db.add(unit)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Unit name already exists")
    db.refresh(unit)
    return unit


@app.post("/api/v1/lookups/units/delete", status_code=204)
def delete_unit(payload: UnitDelete, db: Session = Depends(get_db)) -> None:
    unit = db.get(Unit, payload.unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    db.delete(unit)
    db.commit()


@app.get("/api/v1/lookups/jobpacks", response_model=list[JobpackOut])
def list_jobpacks(db: Session = Depends(get_db)) -> list[Jobpack]:
    jobpacks = db.query(Jobpack).order_by(Jobpack.jobpack_name).all()
    if not jobpacks:
        raise HTTPException(status_code=404, detail="No jobpacks found")
    return jobpacks


@app.post("/api/v1/lookups/jobpacks/update", response_model=JobpackOut)
def update_jobpack(payload: JobpackUpdate, db: Session = Depends(get_db)) -> Jobpack:
    if payload.jobpack_name is None:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    jobpack = db.get(Jobpack, payload.jobpack_id)
    if not jobpack:
        raise HTTPException(status_code=404, detail="Jobpack not found")

    jobpack.jobpack_name = payload.jobpack_name or jobpack.jobpack_name

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Jobpack name already exists")

    db.refresh(jobpack)
    return jobpack


@app.post("/api/v1/lookups/jobpacks/insert", response_model=JobpackOut, status_code=201)
def insert_jobpack(payload: JobpackCreate, db: Session = Depends(get_db)) -> Jobpack:
    jobpack = Jobpack(jobpack_name=payload.jobpack_name)
    db.add(jobpack)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Jobpack name already exists")
    db.refresh(jobpack)
    return jobpack


@app.post("/api/v1/lookups/jobpacks/delete", status_code=204)
def delete_jobpack(payload: JobpackDelete, db: Session = Depends(get_db)) -> None:
    jobpack = db.get(Jobpack, payload.jobpack_id)
    if not jobpack:
        raise HTTPException(status_code=404, detail="Jobpack not found")
    db.delete(jobpack)
    db.commit()


@app.get("/api/v1/people/roles", response_model=list[RoleOut])
def list_roles(db: Session = Depends(get_db)) -> list[Role]:
    roles = db.query(Role).order_by(Role.role_name).all()
    if not roles:
        raise HTTPException(status_code=404, detail="No roles found")
    return roles


@app.post("/api/v1/people/roles/update", response_model=RoleOut)
def update_role(payload: RoleUpdate, db: Session = Depends(get_db)) -> Role:
    if payload.role_name is None:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    role = db.get(Role, payload.role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    role.role_name = payload.role_name or role.role_name

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Role name already exists")

    db.refresh(role)
    return role


@app.post("/api/v1/people/roles/insert", response_model=RoleOut, status_code=201)
def insert_role(payload: RoleCreate, db: Session = Depends(get_db)) -> Role:
    role = Role(role_name=payload.role_name)
    db.add(role)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Role name already exists")
    db.refresh(role)
    return role


@app.post("/api/v1/people/roles/delete", status_code=204)
def delete_role(payload: RoleDelete, db: Session = Depends(get_db)) -> None:
    role = db.get(Role, payload.role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    db.delete(role)
    db.commit()


@app.get("/api/v1/lookups/doc_rev_milestones", response_model=list[DocRevMilestoneOut])
def list_doc_rev_milestones(db: Session = Depends(get_db)) -> list[DocRevMilestone]:
    milestones = db.query(DocRevMilestone).order_by(DocRevMilestone.milestone_name).all()
    if not milestones:
        raise HTTPException(status_code=404, detail="No milestones found")
    return milestones


@app.post(
    "/api/v1/lookups/doc_rev_milestones/update",
    response_model=DocRevMilestoneOut,
)
def update_doc_rev_milestone(
    payload: DocRevMilestoneUpdate, db: Session = Depends(get_db)
) -> DocRevMilestone:
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
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Milestone name already exists")

    db.refresh(milestone)
    return milestone


@app.post(
    "/api/v1/lookups/doc_rev_milestones/insert",
    response_model=DocRevMilestoneOut,
    status_code=201,
)
def insert_doc_rev_milestone(
    payload: DocRevMilestoneCreate, db: Session = Depends(get_db)
) -> DocRevMilestone:
    milestone = DocRevMilestone(milestone_name=payload.milestone_name, progress=payload.progress)
    db.add(milestone)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Milestone name already exists")
    db.refresh(milestone)
    return milestone


@app.post("/api/v1/lookups/doc_rev_milestones/delete", status_code=204)
def delete_doc_rev_milestone(payload: DocRevMilestoneDelete, db: Session = Depends(get_db)) -> None:
    milestone = db.get(DocRevMilestone, payload.milestone_id)
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    db.delete(milestone)
    db.commit()


@app.get("/api/v1/lookups/revision_overview", response_model=list[RevisionOverviewOut])
def list_revision_overview(db: Session = Depends(get_db)) -> list[RevisionOverview]:
    revisions = db.query(RevisionOverview).order_by(RevisionOverview.rev_code_name).all()
    if not revisions:
        raise HTTPException(status_code=404, detail="No revision overview entries found")
    return revisions


@app.post("/api/v1/lookups/revision_overview/update", response_model=RevisionOverviewOut)
def update_revision_overview(
    payload: RevisionOverviewUpdate, db: Session = Depends(get_db)
) -> RevisionOverview:
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
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Revision overview entry already exists")

    db.refresh(revision)
    return revision


@app.post(
    "/api/v1/lookups/revision_overview/insert",
    response_model=RevisionOverviewOut,
    status_code=201,
)
def insert_revision_overview(
    payload: RevisionOverviewCreate, db: Session = Depends(get_db)
) -> RevisionOverview:
    revision = RevisionOverview(
        rev_code_name=payload.rev_code_name,
        rev_code_acronym=payload.rev_code_acronym,
        rev_description=payload.rev_description,
        percentage=payload.percentage,
    )
    db.add(revision)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Revision overview entry already exists")
    db.refresh(revision)
    return revision


@app.post("/api/v1/lookups/revision_overview/delete", status_code=204)
def delete_revision_overview(
    payload: RevisionOverviewDelete, db: Session = Depends(get_db)
) -> None:
    revision = db.get(RevisionOverview, payload.rev_code_id)
    if not revision:
        raise HTTPException(status_code=404, detail="Revision overview entry not found")
    db.delete(revision)
    db.commit()


@app.get("/api/v1/lookups/doc_rev_statuses", response_model=list[DocRevStatusOut])
def list_doc_rev_statuses(db: Session = Depends(get_db)) -> list[DocRevStatus]:
    statuses = db.query(DocRevStatus).order_by(DocRevStatus.rev_status_name).all()
    if not statuses:
        raise HTTPException(status_code=404, detail="No doc revision statuses found")
    return statuses


@app.post("/api/v1/lookups/doc_rev_statuses/update", response_model=DocRevStatusOut)
def update_doc_rev_status(
    payload: DocRevStatusUpdate, db: Session = Depends(get_db)
) -> DocRevStatus:
    if payload.rev_status_name is None:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    status = db.get(DocRevStatus, payload.rev_status_id)
    if not status:
        raise HTTPException(status_code=404, detail="Doc revision status not found")

    if payload.rev_status_name is not None:
        status.rev_status_name = payload.rev_status_name

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Doc revision status already exists")

    db.refresh(status)
    return status


@app.post(
    "/api/v1/lookups/doc_rev_statuses/insert",
    response_model=DocRevStatusOut,
    status_code=201,
)
def insert_doc_rev_status(
    payload: DocRevStatusCreate, db: Session = Depends(get_db)
) -> DocRevStatus:
    status = DocRevStatus(rev_status_name=payload.rev_status_name)
    db.add(status)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Doc revision status already exists")
    db.refresh(status)
    return status


@app.post("/api/v1/lookups/doc_rev_statuses/delete", status_code=204)
def delete_doc_rev_status(payload: DocRevStatusDelete, db: Session = Depends(get_db)) -> None:
    status = db.get(DocRevStatus, payload.rev_status_id)
    if not status:
        raise HTTPException(status_code=404, detail="Doc revision status not found")
    db.delete(status)
    db.commit()


@app.get("/api/v1/people/persons", response_model=list[PersonOut])
def list_persons(db: Session = Depends(get_db)) -> list[Person]:
    persons = db.query(Person).order_by(Person.person_name).all()
    if not persons:
        raise HTTPException(status_code=404, detail="No persons found")
    return persons


@app.post("/api/v1/people/persons/update", response_model=PersonOut)
def update_person(payload: PersonUpdate, db: Session = Depends(get_db)) -> Person:
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
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Failed to update person")

    db.refresh(person)
    return person


@app.post("/api/v1/people/persons/insert", response_model=PersonOut, status_code=201)
def insert_person(payload: PersonCreate, db: Session = Depends(get_db)) -> Person:
    person = Person(person_name=payload.person_name, photo_s3_uid=payload.photo_s3_uid)
    db.add(person)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Failed to create person")
    db.refresh(person)
    return person


@app.post("/api/v1/people/persons/delete", status_code=204)
def delete_person(payload: PersonDelete, db: Session = Depends(get_db)) -> None:
    person = db.get(Person, payload.person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    db.delete(person)
    db.commit()


@app.get("/api/v1/people/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)) -> list[User]:
    users = db.query(User).order_by(User.user_acronym).all()
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    return users


@app.post("/api/v1/people/users/update", response_model=UserOut)
def update_user(payload: UserUpdate, db: Session = Depends(get_db)) -> User:
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
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Failed to update user")

    db.refresh(user)
    return user


@app.post("/api/v1/people/users/insert", response_model=UserOut, status_code=201)
def insert_user(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    person = db.get(Person, payload.person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    role = db.get(Role, payload.role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    user = User(person_id=payload.person_id, user_acronym=payload.user_acronym, role_id=payload.role_id)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Failed to create user")
    db.refresh(user)
    return user


@app.post("/api/v1/people/users/delete", status_code=204)
def delete_user(payload: UserDelete, db: Session = Depends(get_db)) -> None:
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()


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


@app.get("/api/v1/people/permissions", response_model=list[PermissionOut])
def list_permissions(db: Session = Depends(get_db)) -> list[Permission]:
    permissions = db.query(Permission).order_by(Permission.user_id).all()
    if not permissions:
        raise HTTPException(status_code=404, detail="No permissions found")
    return permissions


@app.post("/api/v1/people/permissions/insert", response_model=PermissionOut, status_code=201)
def insert_permission(payload: PermissionCreate, db: Session = Depends(get_db)) -> Permission:
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
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Failed to create permission")
    db.refresh(permission)
    return permission


@app.post("/api/v1/people/permissions/update", response_model=PermissionOut)
def update_permission(payload: PermissionUpdate, db: Session = Depends(get_db)) -> Permission:
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
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Failed to update permission")

    db.refresh(existing)
    return existing


@app.post("/api/v1/people/permissions/delete", status_code=204)
def delete_permission(payload: PermissionDelete, db: Session = Depends(get_db)) -> None:
    payload.validate_scope()

    permission = _permission_filter(db.query(Permission), payload).first()
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    db.delete(permission)
    db.commit()
