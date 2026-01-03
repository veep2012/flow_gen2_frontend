"""Pydantic schemas for file-related entities."""

from pydantic import BaseModel, ConfigDict, Field


class FileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Id.", examples=[1], gt=0)
    filename: str = Field(..., description="Filename.", examples=["Example"], min_length=1)
    s3_uid: str = Field(
        ..., description="S3 object key.", examples=["bucket/path/file.pdf"], min_length=1
    )
    mimetype: str = Field(
        ..., description="File MIME type.", examples=["application/pdf"], min_length=1
    )
    rev_id: int = Field(..., description="Rev ID.", examples=[1], gt=0)


class FileUpdate(BaseModel):
    id: int = Field(..., description="Id.", examples=[1], gt=0)
    filename: str = Field(..., description="Filename.", examples=["Example"], min_length=1)


class FileDelete(BaseModel):
    id: int = Field(..., description="Id.", examples=[1], gt=0)


class FileCommentedOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Id.", examples=[1], gt=0)
    file_id: int = Field(..., description="File ID.", examples=[1], gt=0)
    user_id: int = Field(..., description="User ID.", examples=[1], gt=0)
    s3_uid: str = Field(
        ..., description="S3 object key.", examples=["bucket/path/file.pdf"], min_length=1
    )


class FileCommentedUpdate(BaseModel):
    id: int = Field(..., description="Id.", examples=[1], gt=0)
    s3_uid: str = Field(
        ..., description="S3 object key.", examples=["bucket/path/file.pdf"], min_length=1
    )


class FileCommentedDelete(BaseModel):
    id: int = Field(..., description="Id.", examples=[1], gt=0)
