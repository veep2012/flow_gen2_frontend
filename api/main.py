import os
from typing import Iterable

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from db.models import Area, Discipline


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
