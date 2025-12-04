import os
from typing import Iterable

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Area


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://flow_user:flow_pass@postgres:5432/flow_db",
)

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


app = FastAPI(title="Flow Backend", version="0.1.0")


class AreaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    area_id: int
    area_name: str
    area_acronym: str


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
