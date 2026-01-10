"""Pydantic schemas for document-related entities."""

from pydantic import BaseModel, ConfigDict, Field


class DocTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    type_id: int = Field(..., description="Type ID.", examples=[1], gt=0)
    doc_type_name: str = Field(
        ..., description="Document type name.", examples=["Doc Type A"], min_length=1
    )
    ref_discipline_id: int = Field(..., description="Ref Discipline ID.", examples=[1], gt=0)
    doc_type_acronym: str = Field(
        ..., description="Document type acronym.", examples=["ABC"], min_length=1
    )
    discipline_name: str | None = Field(
        None, description="Discipline name.", examples=["Discipline A"], min_length=1
    )
    discipline_acronym: str | None = Field(
        None, description="Discipline acronym.", examples=["ABC"], min_length=1
    )


class DocTypeCreate(BaseModel):
    doc_type_name: str = Field(
        ..., description="Document type name.", examples=["Doc Type A"], min_length=1
    )
    ref_discipline_id: int = Field(..., description="Ref Discipline ID.", examples=[1], gt=0)
    doc_type_acronym: str = Field(
        ..., description="Document type acronym.", examples=["ABC"], min_length=1
    )


class DocTypeUpdate(BaseModel):
    type_id: int = Field(..., description="Type ID.", examples=[1], gt=0)
    doc_type_name: str | None = Field(
        None, description="Document type name.", examples=["Doc Type A"], min_length=1
    )
    ref_discipline_id: int | None = Field(
        None, description="Ref Discipline ID.", examples=[1], gt=0
    )
    doc_type_acronym: str | None = Field(
        None, description="Document type acronym.", examples=["ABC"], min_length=1
    )


class DocTypeDelete(BaseModel):
    type_id: int = Field(..., description="Type ID.", examples=[1], gt=0)


class DocOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    doc_id: int = Field(..., description="Doc ID.", examples=[1], gt=0)
    doc_name_unique: str = Field(
        ..., description="Document unique name.", examples=["DOC-001"], min_length=1
    )
    title: str = Field(
        ..., description="Document title.", examples=["Document Title"], min_length=1
    )
    project_id: int | None = Field(None, description="Project ID.", examples=[1], gt=0)
    project_name: str | None = Field(
        None, description="Project name.", examples=["Project A"], min_length=1
    )
    jobpack_id: int | None = Field(None, description="Jobpack ID.", examples=[1], gt=0)
    jobpack_name: str | None = Field(
        None, description="Jobpack name.", examples=["Jobpack A"], min_length=1
    )
    type_id: int = Field(..., description="Type ID.", examples=[1], gt=0)
    doc_type_name: str | None = Field(
        None, description="Document type name.", examples=["Doc Type A"], min_length=1
    )
    doc_type_acronym: str | None = Field(
        None, description="Document type acronym.", examples=["ABC"], min_length=1
    )
    area_id: int = Field(..., description="Area ID.", examples=[1], gt=0)
    area_name: str | None = Field(None, description="Area name.", examples=["Area A"], min_length=1)
    area_acronym: str | None = Field(
        None, description="Area acronym.", examples=["ABC"], min_length=1
    )
    unit_id: int = Field(..., description="Unit ID.", examples=[1], gt=0)
    unit_name: str | None = Field(None, description="Unit name.", examples=["Unit A"], min_length=1)
    rev_actual_id: int | None = Field(None, description="Rev Actual ID.", examples=[1], gt=0)
    rev_current_id: int | None = Field(None, description="Rev Current ID.", examples=[1], gt=0)
    rev_seq_num: int | None = Field(
        None, description="Revision sequence number.", examples=[1], gt=0
    )
    discipline_id: int | None = Field(None, description="Discipline ID.", examples=[1], gt=0)
    discipline_name: str | None = Field(
        None, description="Discipline name.", examples=["Discipline A"], min_length=1
    )
    discipline_acronym: str | None = Field(
        None, description="Discipline acronym.", examples=["ABC"], min_length=1
    )
    rev_code_name: str | None = Field(
        None, description="Revision code name.", examples=["Rev Code A"], min_length=1
    )
    rev_code_acronym: str | None = Field(
        None, description="Revision code acronym.", examples=["ABC"], min_length=1
    )
    percentage: int | None = Field(
        None, description="Completion percentage.", examples=[50], ge=0, le=100
    )


class DocUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_id: int = Field(..., description="Doc ID.", examples=[1], gt=0)
    doc_name_unique: str | None = Field(
        None, description="Document unique name.", examples=["DOC-001"], min_length=1
    )
    title: str | None = Field(
        None, description="Document title.", examples=["Document Title"], min_length=1
    )
    project_id: int | None = Field(None, description="Project ID.", examples=[1], gt=0)
    jobpack_id: int | None = Field(None, description="Jobpack ID.", examples=[1], gt=0)
    type_id: int | None = Field(None, description="Type ID.", examples=[1], gt=0)
    area_id: int | None = Field(None, description="Area ID.", examples=[1], gt=0)
    unit_id: int | None = Field(None, description="Unit ID.", examples=[1], gt=0)
    rev_actual_id: int | None = Field(None, description="Rev Actual ID.", examples=[1], gt=0)
    rev_current_id: int | None = Field(None, description="Rev Current ID.", examples=[1], gt=0)


class DocRevMilestoneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    milestone_id: int = Field(..., description="Milestone ID.", examples=[1], gt=0)
    milestone_name: str = Field(
        ..., description="Milestone name.", examples=["Milestone A"], min_length=1
    )
    progress: int | None = Field(
        None, description="Progress percentage.", examples=[50], ge=0, le=100
    )


class DocRevMilestoneUpdate(BaseModel):
    milestone_id: int = Field(..., description="Milestone ID.", examples=[1], gt=0)
    milestone_name: str | None = Field(
        None, description="Milestone name.", examples=["Milestone A"], min_length=1
    )
    progress: int | None = Field(
        None, description="Progress percentage.", examples=[50], ge=0, le=100
    )


class DocRevMilestoneCreate(BaseModel):
    milestone_name: str = Field(
        ..., description="Milestone name.", examples=["Milestone A"], min_length=1
    )
    progress: int | None = Field(
        None, description="Progress percentage.", examples=[50], ge=0, le=100
    )


class DocRevMilestoneDelete(BaseModel):
    milestone_id: int = Field(..., description="Milestone ID.", examples=[1], gt=0)


class RevisionOverviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rev_code_id: int = Field(..., description="Rev Code ID.", examples=[1], gt=0)
    rev_code_name: str = Field(
        ..., description="Revision code name.", examples=["Rev Code A"], min_length=1
    )
    rev_code_acronym: str = Field(
        ..., description="Revision code acronym.", examples=["ABC"], min_length=1
    )
    rev_description: str = Field(
        ..., description="Revision description.", examples=["Initial issue."], min_length=1
    )
    percentage: int | None = Field(
        None, description="Completion percentage.", examples=[50], ge=0, le=100
    )


class RevisionOverviewUpdate(BaseModel):
    rev_code_id: int = Field(..., description="Rev Code ID.", examples=[1], gt=0)
    rev_code_name: str | None = Field(
        None, description="Revision code name.", examples=["Rev Code A"], min_length=1
    )
    rev_code_acronym: str | None = Field(
        None, description="Revision code acronym.", examples=["ABC"], min_length=1
    )
    rev_description: str | None = Field(
        None, description="Revision description.", examples=["Initial issue."], min_length=1
    )
    percentage: int | None = Field(
        None, description="Completion percentage.", examples=[50], ge=0, le=100
    )


class RevisionOverviewCreate(BaseModel):
    rev_code_name: str = Field(
        ..., description="Revision code name.", examples=["Rev Code A"], min_length=1
    )
    rev_code_acronym: str = Field(
        ..., description="Revision code acronym.", examples=["ABC"], min_length=1
    )
    rev_description: str = Field(
        ..., description="Revision description.", examples=["Initial issue."], min_length=1
    )
    percentage: int | None = Field(
        None, description="Completion percentage.", examples=[50], ge=0, le=100
    )


class RevisionOverviewDelete(BaseModel):
    rev_code_id: int = Field(..., description="Rev Code ID.", examples=[1], gt=0)


class DocRevStatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rev_status_id: int = Field(..., description="Rev Status ID.", examples=[1], gt=0)
    rev_status_name: str = Field(
        ..., description="Revision status name.", examples=["Rev Status A"], min_length=1
    )
    ui_behavior_id: int = Field(..., description="UI behavior ID.", examples=[1], gt=0)
    next_rev_status_id: int | None = Field(
        None, description="Next revision status ID.", examples=[2], gt=0
    )
    revertible: bool = Field(..., description="Whether status is revertible.", examples=[True])
    editable: bool = Field(..., description="Whether status is editable.", examples=[True])
    final: bool = Field(
        ...,
        description="Whether status is final (global workflow allows only one final status).",
        examples=[False],
    )
    start: bool = Field(
        ...,
        description="Whether status is the start (global workflow allows only one start status).",
        examples=[False],
    )


class DocRevStatusUpdate(BaseModel):
    rev_status_id: int = Field(..., description="Rev Status ID.", examples=[1], gt=0)
    rev_status_name: str | None = Field(
        None, description="Revision status name.", examples=["Rev Status A"], min_length=1
    )
    ui_behavior_id: int | None = Field(None, description="UI behavior ID.", examples=[1], gt=0)
    next_rev_status_id: int | None = Field(
        None, description="Next revision status ID.", examples=[2], gt=0
    )
    revertible: bool | None = Field(
        None, description="Whether status is revertible.", examples=[True]
    )
    editable: bool | None = Field(None, description="Whether status is editable.", examples=[True])
    final: bool | None = Field(
        None,
        description="Whether status is final (global workflow allows only one final status).",
        examples=[False],
    )
    start: bool | None = Field(
        None,
        description="Whether status is the start (global workflow allows only one start status).",
        examples=[False],
    )


class DocRevStatusCreate(BaseModel):
    rev_status_name: str = Field(
        ..., description="Revision status name.", examples=["Rev Status A"], min_length=1
    )
    ui_behavior_id: int = Field(..., description="UI behavior ID.", examples=[1], gt=0)
    next_rev_status_id: int | None = Field(
        None, description="Next revision status ID.", examples=[2], gt=0
    )
    revertible: bool | None = Field(
        None, description="Whether status is revertible.", examples=[True]
    )
    editable: bool | None = Field(None, description="Whether status is editable.", examples=[True])
    final: bool = Field(
        ...,
        description="Whether status is final (global workflow allows only one final status).",
        examples=[False],
    )
    start: bool | None = Field(
        None,
        description="Whether status is the start (global workflow allows only one start status).",
        examples=[False],
    )


class DocRevStatusDelete(BaseModel):
    rev_status_id: int = Field(..., description="Rev Status ID.", examples=[1], gt=0)


class DocRevStatusUiBehaviorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ui_behavior_id: int = Field(..., description="UI behavior ID.", examples=[1], gt=0)
    ui_behavior_name: str = Field(
        ..., description="UI behavior name.", examples=["InDesign"], min_length=1
    )
    ui_behavior_file: str = Field(
        ..., description="UI behavior file key.", examples=["InDesignBehavior"], min_length=1
    )


class DocRevStatusUiBehaviorUpdate(BaseModel):
    ui_behavior_id: int = Field(..., description="UI behavior ID.", examples=[1], gt=0)
    ui_behavior_name: str | None = Field(
        None, description="UI behavior name.", examples=["InDesign"], min_length=1
    )
    ui_behavior_file: str | None = Field(
        None, description="UI behavior file key.", examples=["InDesignBehavior"], min_length=1
    )


class DocRevStatusUiBehaviorCreate(BaseModel):
    ui_behavior_name: str = Field(
        ..., description="UI behavior name.", examples=["InDesign"], min_length=1
    )
    ui_behavior_file: str = Field(
        ..., description="UI behavior file key.", examples=["InDesignBehavior"], min_length=1
    )


class DocRevStatusUiBehaviorDelete(BaseModel):
    ui_behavior_id: int = Field(..., description="UI behavior ID.", examples=[1], gt=0)
