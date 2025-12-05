import os
from typing import Iterable

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from db.models import Area, Discipline, Project, Unit


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
