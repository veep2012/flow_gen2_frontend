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
    Project,
    RevisionOverview,
    Role,
    Unit,
)


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://flow_user:flow_pass@postgres:5432/flow_db",
)

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


app = FastAPI(title="Flow Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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


@app.get("/api/v1/lookups/roles", response_model=list[RoleOut])
def list_roles(db: Session = Depends(get_db)) -> list[Role]:
    roles = db.query(Role).order_by(Role.role_name).all()
    if not roles:
        raise HTTPException(status_code=404, detail="No roles found")
    return roles


@app.post("/api/v1/lookups/roles/update", response_model=RoleOut)
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


@app.post("/api/v1/lookups/roles/insert", response_model=RoleOut, status_code=201)
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


@app.post("/api/v1/lookups/roles/delete", status_code=204)
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
