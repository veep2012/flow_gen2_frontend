"""Pydantic schemas for lookup entities (areas, disciplines, projects, etc.)."""

from pydantic import BaseModel, ConfigDict, Field


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
