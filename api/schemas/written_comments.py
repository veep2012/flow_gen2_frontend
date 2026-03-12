"""Pydantic schemas for written comments entities."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WrittenCommentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    comment_text: str = Field(
        ...,
        description="Short written comment text.",
        examples=["Please check clash in section B-B."],
        min_length=1,
    )


class WrittenCommentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    comment_text: str = Field(
        ...,
        description="Updated written comment text.",
        examples=["Updated note for this revision."],
        min_length=1,
    )


class WrittenCommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Id.", examples=[1], gt=0)
    rev_id: int = Field(..., description="Revision ID.", examples=[1], gt=0)
    user_id: int = Field(..., description="User ID.", examples=[1], gt=0)
    comment_text: str = Field(..., description="Written comment text.", min_length=1)
    created_at: datetime | None = Field(None, description="Creation timestamp.")
    updated_at: datetime | None = Field(None, description="Last update timestamp.")
    created_by: int | None = Field(
        None, description="User ID who created the written comment.", gt=0
    )
    updated_by: int | None = Field(
        None, description="User ID who last updated the written comment.", gt=0
    )
