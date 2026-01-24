"""Pydantic schemas for people and security (users, permissions) entities."""

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field


class PersonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    person_id: int = Field(..., description="Person ID.", examples=[1], gt=0)
    person_name: str = Field(..., description="Person name.", examples=["Person A"], min_length=1)
    photo_s3_uid: str | None = Field(
        None,
        description="Photo S3 object key.",
        examples=["bucket/photos/person.jpg"],
        min_length=1,
    )


class PersonUpdate(BaseModel):
    person_name: str | None = Field(
        None, description="Person name.", examples=["Person A"], min_length=1
    )
    photo_s3_uid: str | None = Field(
        None,
        description="Photo S3 object key.",
        examples=["bucket/photos/person.jpg"],
        min_length=1,
    )


class PersonCreate(BaseModel):
    person_name: str = Field(..., description="Person name.", examples=["Person A"], min_length=1)
    photo_s3_uid: str | None = Field(
        None,
        description="Photo S3 object key.",
        examples=["bucket/photos/person.jpg"],
        min_length=1,
    )


class PersonDelete(BaseModel):
    person_id: int = Field(..., description="Person ID.", examples=[1], gt=0)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int = Field(..., description="User ID.", examples=[1], gt=0)
    person_id: int = Field(..., description="Person ID.", examples=[1], gt=0)
    user_acronym: str = Field(..., description="User acronym.", examples=["ABC"], min_length=1)
    role_id: int = Field(..., description="Role ID.", examples=[1], gt=0)
    person_name: str | None = Field(
        None, description="Person name.", examples=["Person A"], min_length=1
    )
    role_name: str | None = Field(None, description="Role name.", examples=["Role A"], min_length=1)


class UserUpdate(BaseModel):
    person_id: int | None = Field(None, description="Person ID.", examples=[1], gt=0)
    user_acronym: str | None = Field(
        None, description="User acronym.", examples=["ABC"], min_length=1
    )
    role_id: int | None = Field(None, description="Role ID.", examples=[1], gt=0)


class UserCreate(BaseModel):
    person_id: int = Field(..., description="Person ID.", examples=[1], gt=0)
    user_acronym: str = Field(..., description="User acronym.", examples=["ABC"], min_length=1)
    role_id: int = Field(..., description="Role ID.", examples=[1], gt=0)


class UserDelete(BaseModel):
    user_id: int = Field(..., description="User ID.", examples=[1], gt=0)


class PermissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    permission_id: int = Field(..., description="Permission ID.", examples=[1], gt=0)
    user_id: int = Field(..., description="User ID.", examples=[1], gt=0)
    project_id: int | None = Field(None, description="Project ID.", examples=[1], gt=0)
    discipline_id: int | None = Field(None, description="Discipline ID.", examples=[1], gt=0)
    user_acronym: str | None = Field(
        None, description="User acronym.", examples=["ABC"], min_length=1
    )
    person_name: str | None = Field(
        None, description="Person name.", examples=["Person A"], min_length=1
    )
    project_name: str | None = Field(
        None, description="Project name.", examples=["Project A"], min_length=1
    )
    discipline_name: str | None = Field(
        None, description="Discipline name.", examples=["Discipline A"], min_length=1
    )


class PermissionCreate(BaseModel):
    user_id: int = Field(..., description="User ID.", examples=[1], gt=0)
    project_id: int | None = Field(None, description="Project ID.", examples=[1], gt=0)
    discipline_id: int | None = Field(None, description="Discipline ID.", examples=[1], gt=0)

    def validate_scope(self) -> None:
        if self.project_id is None and self.discipline_id is None:
            raise HTTPException(status_code=400, detail="Provide project_id or discipline_id")


class PermissionDelete(BaseModel):
    permission_id: int | None = Field(None, description="Permission ID.", examples=[1], gt=0)
    user_id: int = Field(..., description="User ID.", examples=[1], gt=0)
    project_id: int | None = Field(None, description="Project ID.", examples=[1], gt=0)
    discipline_id: int | None = Field(None, description="Discipline ID.", examples=[1], gt=0)

    def validate_scope(self) -> None:
        if self.permission_id is None and self.project_id is None and self.discipline_id is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Provide permission_id or project_id/discipline_id "
                    "to identify the permission"
                ),
            )


class PermissionUpdate(BaseModel):
    user_id: int = Field(..., description="User ID.", examples=[1], gt=0)
    project_id: int | None = Field(None, description="Project ID.", examples=[1], gt=0)
    discipline_id: int | None = Field(None, description="Discipline ID.", examples=[1], gt=0)
    new_project_id: int | None = Field(None, description="New Project ID.", examples=[1], gt=0)
    new_discipline_id: int | None = Field(
        None, description="New Discipline ID.", examples=[1], gt=0
    )

    def validate_current(self) -> None:
        if self.project_id is None and self.discipline_id is None:
            raise HTTPException(
                status_code=400, detail="Provide current project_id or discipline_id"
            )
