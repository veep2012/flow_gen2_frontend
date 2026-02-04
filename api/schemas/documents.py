"""Pydantic schemas for document-related entities."""

from datetime import datetime
from typing import Literal

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
    model_config = ConfigDict(extra="forbid")

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
    rev_status_id: int | None = Field(None, description="Revision status ID.", examples=[1], gt=0)
    rev_status_name: str | None = Field(
        None, description="Revision status name.", examples=["Issued"], min_length=1
    )
    percentage: int | None = Field(
        None, description="Completion percentage.", examples=[50], ge=0, le=100
    )
    voided: bool = Field(False, description="Whether document is voided.", examples=[False])
    created_at: datetime | None = Field(None, description="Creation timestamp.")
    updated_at: datetime | None = Field(None, description="Last update timestamp.")
    created_by: int | None = Field(None, description="User ID who created the document.", gt=0)
    updated_by: int | None = Field(None, description="User ID who last updated the document.", gt=0)


class DeleteResult(BaseModel):
    result: str = Field(
        ...,
        description="Delete outcome.",
        examples=["deleted", "voided"],
        pattern="^(deleted|voided)$",
    )


class DocUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

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


class DocCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_name_unique: str = Field(
        ..., description="Document unique name.", examples=["DOC-001"], min_length=1
    )
    title: str = Field(
        ..., description="Document title.", examples=["Document Title"], min_length=1
    )
    project_id: int | None = Field(None, description="Project ID.", examples=[1], gt=0)
    jobpack_id: int | None = Field(None, description="Jobpack ID.", examples=[1], gt=0)
    type_id: int = Field(..., description="Type ID.", examples=[1], gt=0)
    area_id: int = Field(..., description="Area ID.", examples=[1], gt=0)
    unit_id: int = Field(..., description="Unit ID.", examples=[1], gt=0)
    rev_code_id: int = Field(..., description="Revision code ID.", examples=[1], gt=0)
    rev_author_id: int = Field(..., description="Revision author person ID.", examples=[1], gt=0)
    rev_originator_id: int = Field(
        ..., description="Revision originator person ID.", examples=[1], gt=0
    )
    rev_modifier_id: int = Field(
        ..., description="Revision modifier person ID.", examples=[1], gt=0
    )
    transmital_current_revision: str = Field(
        ..., description="Transmittal current revision.", examples=["TR-001"], min_length=1
    )
    milestone_id: int | None = Field(None, description="Milestone ID.", examples=[1], gt=0)
    planned_start_date: datetime = Field(
        ..., description="Planned start date.", examples=["2024-01-02T12:00:00Z"]
    )
    planned_finish_date: datetime = Field(
        ..., description="Planned finish date.", examples=["2024-01-05T12:00:00Z"]
    )


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
    model_config = ConfigDict(extra="forbid")
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


class DocRevisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rev_id: int = Field(..., description="Revision ID.", examples=[1], gt=0)
    doc_id: int = Field(..., description="Doc ID.", examples=[1], gt=0)
    seq_num: int = Field(..., description="Revision sequence number.", examples=[1], gt=0)
    rev_code_id: int = Field(..., description="Revision code ID.", examples=[1], gt=0)
    rev_code_name: str | None = Field(
        None, description="Revision code name.", examples=["IFC"], min_length=1
    )
    rev_code_acronym: str | None = Field(
        None, description="Revision code acronym.", examples=["E"], min_length=1
    )
    rev_description: str | None = Field(
        None,
        description="Revision description.",
        examples=["Issued for Construction."],
        min_length=1,
    )
    rev_author_id: int = Field(..., description="Revision author person ID.", examples=[1], gt=0)
    rev_originator_id: int = Field(
        ..., description="Revision originator person ID.", examples=[1], gt=0
    )
    rev_modifier_id: int = Field(
        ..., description="Revision modifier person ID.", examples=[1], gt=0
    )
    transmital_current_revision: str = Field(
        ..., description="Transmittal current revision.", examples=["TR-001"], min_length=1
    )
    milestone_id: int | None = Field(None, description="Milestone ID.", examples=[1], gt=0)
    milestone_name: str | None = Field(
        None, description="Milestone name.", examples=["IFC"], min_length=1
    )
    planned_start_date: datetime = Field(
        ..., description="Planned start date.", examples=["2024-01-02T12:00:00Z"]
    )
    planned_finish_date: datetime = Field(
        ..., description="Planned finish date.", examples=["2024-01-05T12:00:00Z"]
    )
    actual_start_date: datetime | None = Field(
        None, description="Actual start date.", examples=["2024-01-03T12:00:00Z"]
    )
    actual_finish_date: datetime | None = Field(
        None, description="Actual finish date.", examples=["2024-01-06T12:00:00Z"]
    )
    canceled_date: datetime | None = Field(
        None, description="Canceled date.", examples=["2024-01-04T12:00:00Z"]
    )
    rev_status_id: int = Field(..., description="Revision status ID.", examples=[1], gt=0)
    rev_status_name: str | None = Field(
        None, description="Revision status name.", examples=["InDesign"], min_length=1
    )
    as_built: bool = Field(False, description="As-built flag.", examples=[False])
    superseded: bool = Field(False, description="Superseded flag.", examples=[False])
    modified_doc_date: datetime = Field(
        ..., description="Modified document date.", examples=["2024-01-05T12:00:00Z"]
    )
    created_at: datetime | None = Field(None, description="Creation timestamp.")
    updated_at: datetime | None = Field(None, description="Last update timestamp.")
    created_by: int | None = Field(None, description="User ID who created the revision.", gt=0)
    updated_by: int | None = Field(None, description="User ID who last updated the revision.", gt=0)


class DocRevisionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seq_num: int | None = Field(None, description="Revision sequence number.", examples=[1], gt=0)
    rev_code_id: int | None = Field(None, description="Revision code ID.", examples=[1], gt=0)
    rev_author_id: int | None = Field(
        None, description="Revision author person ID.", examples=[1], gt=0
    )
    rev_originator_id: int | None = Field(
        None, description="Revision originator person ID.", examples=[1], gt=0
    )
    rev_modifier_id: int | None = Field(
        None, description="Revision modifier person ID.", examples=[1], gt=0
    )
    transmital_current_revision: str | None = Field(
        None, description="Transmittal current revision.", examples=["TR-001"], min_length=1
    )
    milestone_id: int | None = Field(None, description="Milestone ID.", examples=[1], gt=0)
    planned_start_date: datetime | None = Field(
        None, description="Planned start date.", examples=["2024-01-02T12:00:00Z"]
    )
    planned_finish_date: datetime | None = Field(
        None, description="Planned finish date.", examples=["2024-01-05T12:00:00Z"]
    )
    actual_start_date: datetime | None = Field(
        None, description="Actual start date.", examples=["2024-01-03T12:00:00Z"]
    )
    actual_finish_date: datetime | None = Field(
        None, description="Actual finish date.", examples=["2024-01-06T12:00:00Z"]
    )
    as_built: bool | None = Field(None, description="As-built flag.", examples=[False])
    modified_doc_date: datetime | None = Field(
        None, description="Modified document date.", examples=["2024-01-05T12:00:00Z"]
    )


class DocRevisionStatusTransition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    direction: Literal["forward", "back"] = Field(
        ..., description="Status transition direction.", examples=["forward"]
    )


class DocRevisionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rev_code_id: int = Field(..., description="Revision code ID.", examples=[1], gt=0)
    rev_author_id: int = Field(..., description="Revision author person ID.", examples=[1], gt=0)
    rev_originator_id: int = Field(
        ..., description="Revision originator person ID.", examples=[1], gt=0
    )
    rev_modifier_id: int = Field(
        ..., description="Revision modifier person ID.", examples=[1], gt=0
    )
    transmital_current_revision: str = Field(
        ..., description="Transmittal current revision.", examples=["TR-001"], min_length=1
    )
    milestone_id: int | None = Field(None, description="Milestone ID.", examples=[1], gt=0)
    planned_start_date: datetime = Field(
        ..., description="Planned start date.", examples=["2024-01-02T12:00:00Z"]
    )
    planned_finish_date: datetime = Field(
        ..., description="Planned finish date.", examples=["2024-01-05T12:00:00Z"]
    )
    actual_start_date: datetime | None = Field(
        None, description="Actual start date.", examples=["2024-01-03T12:00:00Z"]
    )
    actual_finish_date: datetime | None = Field(
        None, description="Actual finish date.", examples=["2024-01-06T12:00:00Z"]
    )
    as_built: bool = Field(False, description="As-built flag.", examples=[False])
    modified_doc_date: datetime | None = Field(
        None, description="Modified document date.", examples=["2024-01-05T12:00:00Z"]
    )


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
    model_config = ConfigDict(extra="forbid")
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
    model_config = ConfigDict(extra="forbid")
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
