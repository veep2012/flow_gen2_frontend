from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    PrimaryKeyConstraint,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, foreign, mapped_column, relationship

metadata = MetaData(schema="flow")


class Base(DeclarativeBase):
    metadata = metadata


class Area(Base):
    __tablename__ = "areas"

    area_id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    area_name: Mapped[str] = mapped_column(String(45), unique=True, nullable=False)
    area_acronym: Mapped[str] = mapped_column(String(5), unique=True, nullable=False)

    docs: Mapped[list["Doc"]] = relationship(back_populates="area")


class Discipline(Base):
    __tablename__ = "disciplines"

    discipline_id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    discipline_name: Mapped[str] = mapped_column(String(45), unique=True, nullable=False)
    discipline_acronym: Mapped[str] = mapped_column(String(5), unique=True, nullable=False)

    doc_types: Mapped[list["DocType"]] = relationship(back_populates="discipline")
    permissions: Mapped[list["Permission"]] = relationship(back_populates="discipline")


class Project(Base):
    __tablename__ = "projects"

    project_id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    project_name: Mapped[str] = mapped_column(String(45), unique=True, nullable=False)

    docs: Mapped[list["Doc"]] = relationship(back_populates="project")
    distribution_lists: Mapped[list["DistributionList"]] = relationship(back_populates="project")
    permissions: Mapped[list["Permission"]] = relationship(back_populates="project")
    doc_cache_entries: Mapped[list["DocCache"]] = relationship(back_populates="project")


class Unit(Base):
    __tablename__ = "units"

    unit_id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    unit_name: Mapped[str] = mapped_column(String(45), unique=True, nullable=False)

    docs: Mapped[list["Doc"]] = relationship(back_populates="unit")
    doc_cache_entries: Mapped[list["DocCache"]] = relationship(back_populates="unit")


class Jobpack(Base):
    __tablename__ = "jobpacks"

    jobpack_id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    jobpack_name: Mapped[str] = mapped_column(String(45), unique=True, nullable=False)

    docs: Mapped[list["Doc"]] = relationship(back_populates="jobpack")
    doc_cache_entries: Mapped[list["DocCache"]] = relationship(back_populates="jobpack")


class Role(Base):
    __tablename__ = "roles"

    role_id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    role_name: Mapped[str] = mapped_column(String(45), unique=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="role")


class DocRevMilestone(Base):
    __tablename__ = "doc_rev_milestones"

    milestone_id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    milestone_name: Mapped[str] = mapped_column(String(45), unique=True, nullable=False)
    progress: Mapped[Optional[int]] = mapped_column(SmallInteger, default=0)

    revisions: Mapped[list["DocRevision"]] = relationship(back_populates="milestone")


class RevisionOverview(Base):
    __tablename__ = "revision_overview"

    rev_code_id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    rev_code_name: Mapped[str] = mapped_column(String(15), unique=True, nullable=False)
    rev_code_acronym: Mapped[str] = mapped_column(String(5), nullable=False)
    rev_description: Mapped[str] = mapped_column(String(45), unique=True, nullable=False)
    percentage: Mapped[Optional[int]] = mapped_column(SmallInteger)

    revisions: Mapped[list["DocRevision"]] = relationship(back_populates="revision_overview")


class DocRevStatus(Base):
    __tablename__ = "doc_rev_statuses"

    rev_status_id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    rev_status_name: Mapped[str] = mapped_column(String(45), unique=True, nullable=False)
    ui_behavior_id: Mapped[int] = mapped_column(
        ForeignKey("flow.doc_rev_status_ui_behaviors.ui_behavior_id"), nullable=False
    )
    next_rev_status_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("flow.doc_rev_statuses.rev_status_id")
    )
    revertible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    editable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    final: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    start: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    revisions: Mapped[list["DocRevision"]] = relationship(back_populates="status")
    ui_behavior: Mapped["DocRevStatusUiBehavior"] = relationship(back_populates="statuses")


class DocRevStatusUiBehavior(Base):
    __tablename__ = "doc_rev_status_ui_behaviors"

    ui_behavior_id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    ui_behavior_name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    ui_behavior_file: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    statuses: Mapped[list[DocRevStatus]] = relationship(back_populates="ui_behavior")


class FileAccepted(Base):
    __tablename__ = "files_accepted"

    file_type: Mapped[str] = mapped_column(String(10), primary_key=True)
    mimetype: Mapped[str] = mapped_column(String(90), nullable=False)


class LeasedDocNum(Base):
    __tablename__ = "leased_doc_nums"

    doc_number: Mapped[str] = mapped_column(String(45), primary_key=True)
    created_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class SqlQuery(Base):
    __tablename__ = "sql_queries"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    query: Mapped[str] = mapped_column(String(4096), nullable=False)
    titles: Mapped[Optional[str]] = mapped_column(String(1024))
    project_filtered_field: Mapped[Optional[str]] = mapped_column(String(45))
    discipline_filtered_field: Mapped[Optional[str]] = mapped_column(String(45))


class Person(Base):
    __tablename__ = "person"

    person_id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    person_name: Mapped[str] = mapped_column(String(45), nullable=False)
    photo_s3_uid: Mapped[Optional[str]] = mapped_column(Text)

    user: Mapped[Optional["User"]] = relationship(back_populates="person", uselist=False)
    authored_revisions: Mapped[list["DocRevision"]] = relationship(
        back_populates="author",
        foreign_keys="DocRevision.rev_author_id",
    )
    originated_revisions: Mapped[list["DocRevision"]] = relationship(
        back_populates="originator",
        foreign_keys="DocRevision.rev_originator_id",
    )


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("person_id", name="uq_users_person_id"),)

    user_id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    person_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("flow.person.person_id"), nullable=False
    )
    user_acronym: Mapped[str] = mapped_column(String(10), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("flow.roles.role_id"), nullable=False)

    person: Mapped[Person] = relationship(back_populates="user")
    role: Mapped[Role] = relationship(back_populates="users")
    permissions: Mapped[list["Permission"]] = relationship(back_populates="user")
    commented_files: Mapped[list["FileCommented"]] = relationship(
        back_populates="user",
        foreign_keys="FileCommented.user_id",
    )


class DocType(Base):
    __tablename__ = "doc_types"

    type_id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    doc_type_name: Mapped[str] = mapped_column(String(45), nullable=False)
    ref_discipline_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("flow.disciplines.discipline_id"), nullable=False
    )
    doc_type_acronym: Mapped[str] = mapped_column(String(10), nullable=False)

    discipline: Mapped[Discipline] = relationship(back_populates="doc_types")
    docs: Mapped[list["Doc"]] = relationship(back_populates="doc_type")
    doc_cache_entries: Mapped[list["DocCache"]] = relationship(back_populates="doc_type")


class DistributionList(Base):
    __tablename__ = "distribution_list"

    dist_id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    distribution_list_name: Mapped[str] = mapped_column(String(45), nullable=False)
    project_id: Mapped[int] = mapped_column(ForeignKey("flow.projects.project_id"), nullable=False)

    project: Mapped[Project] = relationship(back_populates="distribution_lists")
    members: Mapped[list["DistributionListContent"]] = relationship(
        back_populates="distribution_list"
    )


class DistributionListContent(Base):
    __tablename__ = "distribution_list_content"
    __table_args__ = (PrimaryKeyConstraint("dist_id", "person_id"),)

    dist_id: Mapped[int] = mapped_column(
        ForeignKey("flow.distribution_list.dist_id"), nullable=False
    )
    person_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("flow.person.person_id"), nullable=False
    )

    distribution_list: Mapped[DistributionList] = relationship(back_populates="members")
    person: Mapped[Person] = relationship()


class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = (
        CheckConstraint(
            "project_id IS NOT NULL OR discipline_id IS NOT NULL",
            name="chk_permissions_scope",
        ),
        Index(
            "ix_permissions_user_proj_disc",
            "user_id",
            "project_id",
            "discipline_id",
            unique=True,
            postgresql_where=text("project_id IS NOT NULL AND discipline_id IS NOT NULL"),
        ),
        Index(
            "ix_permissions_user_proj_anydisc",
            "user_id",
            "project_id",
            unique=True,
            postgresql_where=text("discipline_id IS NULL"),
        ),
        Index(
            "ix_permissions_user_anyproj_disc",
            "user_id",
            "discipline_id",
            unique=True,
            postgresql_where=text("project_id IS NULL"),
        ),
        Index(
            "ix_permissions_user_anyscope",
            "user_id",
            unique=True,
            postgresql_where=text("project_id IS NULL AND discipline_id IS NULL"),
        ),
    )

    permission_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("flow.users.user_id"), nullable=False
    )
    project_id: Mapped[Optional[int]] = mapped_column(
        SmallInteger, ForeignKey("flow.projects.project_id")
    )
    discipline_id: Mapped[Optional[int]] = mapped_column(
        SmallInteger, ForeignKey("flow.disciplines.discipline_id")
    )

    user: Mapped[User] = relationship(back_populates="permissions")
    project: Mapped[Optional[Project]] = relationship(back_populates="permissions")
    discipline: Mapped[Optional[Discipline]] = relationship(back_populates="permissions")


class Doc(Base):
    __tablename__ = "doc"

    doc_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    doc_name_unique: Mapped[str] = mapped_column(String(45), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(45), nullable=False)
    project_id: Mapped[Optional[int]] = mapped_column(
        SmallInteger, ForeignKey("flow.projects.project_id")
    )
    jobpack_id: Mapped[Optional[int]] = mapped_column(
        SmallInteger, ForeignKey("flow.jobpacks.jobpack_id")
    )
    type_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("flow.doc_types.type_id"), nullable=False
    )
    area_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("flow.areas.area_id"), nullable=False
    )
    unit_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("flow.units.unit_id"), nullable=False
    )
    rev_actual_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("flow.doc_revision.rev_id", use_alter=True, name="fk_doc_rev_actual")
    )
    rev_current_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("flow.doc_revision.rev_id", use_alter=True, name="fk_doc_rev_current")
    )
    voided: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        SmallInteger, ForeignKey("flow.users.user_id")
    )
    updated_by: Mapped[Optional[int]] = mapped_column(
        SmallInteger, ForeignKey("flow.users.user_id")
    )

    project: Mapped[Optional[Project]] = relationship(back_populates="docs")
    jobpack: Mapped[Optional[Jobpack]] = relationship(back_populates="docs")
    doc_type: Mapped[DocType] = relationship(back_populates="docs")
    area: Mapped[Area] = relationship(back_populates="docs")
    unit: Mapped[Unit] = relationship(back_populates="docs")
    revisions: Mapped[list["DocRevision"]] = relationship(
        back_populates="doc",
        foreign_keys="DocRevision.doc_id",
    )
    current_revision: Mapped[Optional["DocRevision"]] = relationship(
        foreign_keys=[rev_current_id],
        post_update=True,
        overlaps="revisions,actual_revision",
    )
    actual_revision: Mapped[Optional["DocRevision"]] = relationship(
        foreign_keys=[rev_actual_id],
        post_update=True,
        overlaps="revisions,current_revision",
    )


class DocCache(Base):
    __tablename__ = "doc_cache"
    __table_args__ = (PrimaryKeyConstraint("user_id", "project_id", "doc_name_unique"),)

    user_id: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    project_id: Mapped[int] = mapped_column(ForeignKey("flow.projects.project_id"), nullable=False)
    doc_name_unique: Mapped[str] = mapped_column(String(45), nullable=False)
    title: Mapped[str] = mapped_column(String(45), nullable=False)
    jobpack_id: Mapped[Optional[int]] = mapped_column(
        SmallInteger, ForeignKey("flow.jobpacks.jobpack_id")
    )
    type_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("flow.doc_types.type_id"), nullable=False
    )
    area_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("flow.areas.area_id"), nullable=False
    )
    unit_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("flow.units.unit_id"), nullable=False
    )

    project: Mapped[Project] = relationship(back_populates="doc_cache_entries")
    jobpack: Mapped[Optional[Jobpack]] = relationship(back_populates="doc_cache_entries")
    doc_type: Mapped[DocType] = relationship(back_populates="doc_cache_entries")
    area: Mapped[Area] = relationship()
    unit: Mapped[Unit] = relationship()


class DocRevision(Base):
    __tablename__ = "doc_revision"

    rev_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rev_code_id: Mapped[int] = mapped_column(
        ForeignKey("flow.revision_overview.rev_code_id"), nullable=False
    )
    rev_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    rev_author_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("flow.person.person_id"), nullable=False
    )
    rev_originator_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("flow.person.person_id"), nullable=False
    )
    as_built: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    superseded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    voided: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    transmital_current_revision: Mapped[str] = mapped_column(String(45), nullable=False)
    milestone_id: Mapped[Optional[int]] = mapped_column(
        SmallInteger, ForeignKey("flow.doc_rev_milestones.milestone_id")
    )
    planned_start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    planned_finish_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    actual_finish_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    canceled_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    rev_status_id: Mapped[int] = mapped_column(
        ForeignKey("flow.doc_rev_statuses.rev_status_id"), nullable=False
    )
    doc_id: Mapped[int] = mapped_column(
        ForeignKey("flow.doc.doc_id", ondelete="CASCADE"), nullable=False
    )
    seq_num: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    rev_modifier_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("flow.person.person_id"), nullable=False
    )
    modified_doc_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        SmallInteger, ForeignKey("flow.users.user_id")
    )
    updated_by: Mapped[Optional[int]] = mapped_column(
        SmallInteger, ForeignKey("flow.users.user_id")
    )

    doc: Mapped[Doc] = relationship(
        back_populates="revisions",
        foreign_keys=[doc_id],
    )
    revision_overview: Mapped[RevisionOverview] = relationship(back_populates="revisions")
    author: Mapped[Person] = relationship(
        back_populates="authored_revisions",
        foreign_keys=[rev_author_id],
    )
    originator: Mapped[Person] = relationship(
        back_populates="originated_revisions",
        foreign_keys=[rev_originator_id],
    )
    milestone: Mapped[Optional[DocRevMilestone]] = relationship(back_populates="revisions")
    status: Mapped[DocRevStatus] = relationship(back_populates="revisions")
    files: Mapped[list["File"]] = relationship(back_populates="revision")
    history_entries: Mapped[list["DocRevisionHistory"]] = relationship(
        primaryjoin=lambda: DocRevision.rev_id == foreign(DocRevisionHistory.rev_id),
        viewonly=True,
    )


class DocRevisionHistory(Base):
    __tablename__ = "doc_revision_history"
    __table_args__ = (PrimaryKeyConstraint("rev_id", "archived_at"),)

    rev_id: Mapped[int] = mapped_column(Integer, nullable=False)
    rev_code_id: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    rev_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rev_author_id: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    rev_originator_id: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    as_built: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    superseded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    voided: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    transmital_current_revision: Mapped[str] = mapped_column(String(45), nullable=False)
    milestone_id: Mapped[Optional[int]] = mapped_column(SmallInteger)
    planned_start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    planned_finish_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    actual_finish_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    canceled_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    rev_status_id: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    doc_id: Mapped[int] = mapped_column(Integer, nullable=False)
    seq_num: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    archived_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    revision: Mapped[DocRevision] = relationship(
        primaryjoin=lambda: DocRevisionHistory.rev_id == foreign(DocRevision.rev_id),
        viewonly=True,
    )


class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(90), nullable=False)
    s3_uid: Mapped[str] = mapped_column(Text, nullable=False)
    mimetype: Mapped[str] = mapped_column(String(90), nullable=False)
    rev_id: Mapped[int] = mapped_column(
        ForeignKey("flow.doc_revision.rev_id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        SmallInteger, ForeignKey("flow.users.user_id")
    )
    updated_by: Mapped[Optional[int]] = mapped_column(
        SmallInteger, ForeignKey("flow.users.user_id")
    )

    revision: Mapped[DocRevision] = relationship(back_populates="files")
    comments: Mapped[list["FileCommented"]] = relationship(back_populates="file")


class FileCommented(Base):
    __tablename__ = "files_commented"
    __table_args__ = (UniqueConstraint("file_id", "user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_id: Mapped[int] = mapped_column(
        ForeignKey("flow.files.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("flow.users.user_id"), nullable=False
    )
    s3_uid: Mapped[str] = mapped_column(Text, nullable=False)
    mimetype: Mapped[str] = mapped_column(String(90), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        SmallInteger, ForeignKey("flow.users.user_id")
    )
    updated_by: Mapped[Optional[int]] = mapped_column(
        SmallInteger, ForeignKey("flow.users.user_id")
    )

    file: Mapped[File] = relationship(back_populates="comments")
    user: Mapped[User] = relationship(
        back_populates="commented_files",
        foreign_keys=[user_id],
    )


class DocRevisionHistoryView(Base):
    __tablename__ = "doc_revision_history_view"
    __table_args__ = (PrimaryKeyConstraint("rev_id", "seq_num", "source_type"),)

    rev_id: Mapped[int] = mapped_column(Integer, nullable=False)
    rev_code_id: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    rev_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rev_author_id: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    rev_originator_id: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    as_built: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    superseded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    voided: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    transmital_current_revision: Mapped[str] = mapped_column(String(45), nullable=False)
    milestone_id: Mapped[Optional[int]] = mapped_column(SmallInteger)
    planned_start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    planned_finish_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    actual_finish_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    canceled_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    rev_status_id: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    doc_id: Mapped[int] = mapped_column(Integer, nullable=False)
    seq_num: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    source_type: Mapped[str] = mapped_column(String(10), nullable=False)
