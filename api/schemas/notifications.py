"""Pydantic schemas for notification-related entities."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class NotificationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sender_user_id: int | None = Field(
        None,
        description="Sender user ID. If omitted, uses X-User-Id.",
        examples=[1],
        gt=0,
    )
    title: str = Field(
        ...,
        description="Notification title.",
        examples=["Review update"],
        min_length=1,
    )
    body: str = Field(
        ...,
        description="Notification message body.",
        examples=["Please review the latest revision."],
        min_length=1,
    )
    rev_id: int = Field(
        ...,
        description="Revision ID linked to the notification.",
        examples=[1],
        gt=0,
    )
    commented_file_id: int | None = Field(
        None,
        description="Optional commented file ID linked to the notification.",
        examples=[1],
        gt=0,
    )
    recipient_user_ids: list[int] = Field(
        default_factory=list,
        description="Direct recipient user IDs.",
        examples=[[2, 3]],
    )
    recipient_dist_ids: list[int] = Field(
        default_factory=list,
        description="Distribution list IDs.",
        examples=[[1, 2]],
    )
    remark: str | None = Field(None, description="Optional remark.", examples=["manual send"])

    @model_validator(mode="after")
    def validate_recipients(self) -> "NotificationCreate":
        if not self.recipient_user_ids and not self.recipient_dist_ids:
            raise ValueError(
                "At least one recipient_user_ids or recipient_dist_ids entry is required"
            )
        return self


class NotificationReplace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(
        ...,
        description="Replacement notification title.",
        examples=["Review update (changed)"],
        min_length=1,
    )
    body: str = Field(
        ...,
        description="Replacement notification body.",
        examples=["There is an updated comment. Please re-check."],
        min_length=1,
    )
    remark: str | None = Field(
        "changed",
        description="Reason/remark for replacement.",
        examples=["changed by sender"],
        min_length=1,
    )


class NotificationDelete(BaseModel):
    model_config = ConfigDict(extra="forbid")

    remark: str | None = Field(
        "dropped",
        description="Reason/remark for dropping notification.",
        examples=["no longer valid"],
        min_length=1,
    )


class NotificationMarkRead(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {}})


class NotificationActionResult(BaseModel):
    notification_id: int = Field(..., description="Created notification ID.", examples=[10], gt=0)
    recipient_count: int = Field(..., description="Delivered recipient count.", examples=[3], ge=0)


class NotificationRecipientStateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    notification_id: int = Field(..., description="Notification ID.", examples=[10], gt=0)
    recipient_user_id: int = Field(..., description="Recipient user ID.", examples=[2], gt=0)
    delivered_at: datetime = Field(..., description="Delivery timestamp.")
    read_at: datetime | None = Field(None, description="Read timestamp.")


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    notification_id: int = Field(..., description="Notification ID.", examples=[10], gt=0)
    sender_user_id: int = Field(..., description="Sender user ID.", examples=[1], gt=0)
    event_type: Literal["regular", "changed_notice", "dropped_notice"] = Field(
        ...,
        description="Notification event type.",
        examples=["regular"],
    )
    title: str = Field(
        ...,
        description="Notification title.",
        examples=["Review update"],
        min_length=1,
    )
    body: str = Field(
        ...,
        description="Notification body.",
        examples=["Please review the latest revision."],
        min_length=1,
    )
    remark: str | None = Field(None, description="Optional remark.", examples=["changed by sender"])
    rev_id: int = Field(..., description="Linked revision ID.", examples=[1], gt=0)
    commented_file_id: int | None = Field(
        None,
        description="Linked commented file ID.",
        examples=[1],
        gt=0,
    )
    created_at: datetime = Field(..., description="Creation timestamp.")
    dropped_at: datetime | None = Field(None, description="Dropped timestamp.")
    dropped_by_user_id: int | None = Field(
        None,
        description="User who dropped original notification.",
        gt=0,
    )
    superseded_by_notification_id: int | None = Field(
        None,
        description="New notification replacing this one.",
        examples=[11],
        gt=0,
    )
    recipient_user_id: int = Field(..., description="Recipient user ID.", examples=[2], gt=0)
    delivered_at: datetime = Field(..., description="Delivery timestamp.")
    read_at: datetime | None = Field(None, description="Read timestamp.")
