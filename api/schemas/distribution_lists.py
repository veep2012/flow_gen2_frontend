"""Pydantic schemas for distribution list-related entities."""

from pydantic import BaseModel, ConfigDict, Field


class PersonOut(BaseModel):
    """Schema for person information in distribution list."""
    model_config = ConfigDict(from_attributes=True)

    person_id: int = Field(..., description="Person ID", examples=[1], gt=0)
    person_name: str = Field(..., description="Person name", examples=["John Doe"])


class DistributionListCreate(BaseModel):
    """Schema for creating a distribution list."""

    distribution_list_name: str = Field(
        ..., description="Distribution list name", examples=["Review Team"], min_length=1
    )


class DistributionListOut(BaseModel):
    """Schema for distribution list output."""
    model_config = ConfigDict(from_attributes=True)

    dist_id: int = Field(..., description="Distribution list ID", examples=[1], gt=0)
    dist_list_id: int | None = Field(None, description="Alternative ID field for compatibility", examples=[1], gt=0)
    distribution_list_name: str = Field(
        ..., description="Distribution list name", examples=["Review Team"]
    )
    list_name: str | None = Field(None, description="Alternative name field for compatibility", examples=["Review Team"])
    project_id: int = Field(..., description="Project ID", examples=[1], gt=0)


class DistributionListDetailOut(DistributionListOut):
    """Schema for distribution list with members."""

    members: list[PersonOut] = Field(default=[], description="List of recipients/members")


class RecipientAdd(BaseModel):
    """Schema for adding a recipient to a distribution list."""

    person_id: int | None = Field(None, description="Person ID", examples=[1], gt=0)
    email: str | None = Field(None, description="Email address (optional, for reference)", examples=["john@example.com"])


class SendForReviewRequest(BaseModel):
    """Schema for sending document for review."""

    recipients: list[str] = Field(
        ..., description="List of recipient email addresses", examples=[["john@example.com"]]
    )
