"""Pydantic schemas for distribution list API."""

from pydantic import BaseModel, ConfigDict, Field


class DistributionListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dist_id: int = Field(..., description="Distribution list ID.", examples=[1], gt=0)
    distribution_list_name: str = Field(
        ...,
        description="Distribution list name.",
        examples=["Review Team"],
        min_length=1,
    )
    doc_id: int | None = Field(
        None,
        description="Linked document ID. Nullable for global lists.",
        examples=[101],
        gt=0,
    )


class DistributionListCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    distribution_list_name: str = Field(
        ...,
        description="Distribution list name.",
        examples=["Review Team"],
        min_length=1,
    )
    doc_id: int | None = Field(
        None,
        description="Optional linked document ID.",
        examples=[101],
        gt=0,
    )


class DistributionListMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dist_id: int = Field(..., description="Distribution list ID.", examples=[1], gt=0)
    user_id: int = Field(..., description="User ID.", examples=[2], gt=0)
    person_id: int | None = Field(None, description="Person ID.", examples=[2], gt=0)
    user_acronym: str | None = Field(None, description="User acronym.", examples=["FDQC"])
    person_name: str | None = Field(None, description="Person name.", examples=["Aleksey Krutskih"])


class DistributionListMemberCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int = Field(..., description="User ID to add.", examples=[2], gt=0)
