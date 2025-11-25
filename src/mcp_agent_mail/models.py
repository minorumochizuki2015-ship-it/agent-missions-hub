"""SQLModel data models representing agents, messages, projects, and file reservations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import Column, UniqueConstraint
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel


class Project(SQLModel, table=True):
    __tablename__ = "projects"

    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(index=True, unique=True, max_length=255)
    human_key: str = Field(max_length=255, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Agent(SQLModel, table=True):
    __tablename__ = "agents"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_agent_project_name"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id", index=True)
    name: str = Field(index=True, max_length=128)
    program: str = Field(max_length=128)
    model: str = Field(max_length=128)
    task_description: str = Field(default="")
    task_summary: Optional[str] = Field(default=None)
    skills: Optional[list[str]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    primary_model: Optional[str] = Field(default=None, max_length=128)
    inception_ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_active_ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    attachments_policy: str = Field(default="auto", max_length=16)
    contact_policy: str = Field(
        default="auto", max_length=16
    )  # open | auto | contacts_only | block_all


class MessageRecipient(SQLModel, table=True):
    __tablename__ = "message_recipients"

    message_id: int = Field(foreign_key="messages.id", primary_key=True)
    agent_id: int = Field(foreign_key="agents.id", primary_key=True)
    kind: str = Field(max_length=8, default="to")
    read_ts: Optional[datetime] = Field(default=None)
    ack_ts: Optional[datetime] = Field(default=None)


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id", index=True)
    sender_id: int = Field(foreign_key="agents.id", index=True)
    thread_id: Optional[str] = Field(default=None, index=True, max_length=128)
    subject: str = Field(max_length=512)
    body_md: str
    importance: str = Field(default="normal", max_length=16)
    ack_required: bool = Field(default=False)
    created_ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    attachments: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False, server_default="[]"),
    )


class FileReservation(SQLModel, table=True):
    __tablename__ = "file_reservations"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id", index=True)
    agent_id: int = Field(foreign_key="agents.id", index=True)
    path_pattern: str = Field(max_length=512)
    exclusive: bool = Field(default=True)
    reason: str = Field(default="", max_length=512)
    created_ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_ts: datetime
    released_ts: Optional[datetime] = None


class AgentLink(SQLModel, table=True):
    """Directed contact link request from agent A to agent B.

    When approved, messages may be sent cross-project between A and B.
    """

    __tablename__ = "agent_links"
    __table_args__ = (
        UniqueConstraint(
            "a_project_id",
            "a_agent_id",
            "b_project_id",
            "b_agent_id",
            name="uq_agentlink_pair",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    a_project_id: int = Field(foreign_key="projects.id", index=True)
    a_agent_id: int = Field(foreign_key="agents.id", index=True)
    b_project_id: int = Field(foreign_key="projects.id", index=True)
    b_agent_id: int = Field(foreign_key="agents.id", index=True)
    status: str = Field(
        default="pending", max_length=16
    )  # pending | approved | blocked
    reason: str = Field(default="", max_length=512)
    created_ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_ts: Optional[datetime] = None


class ProjectSiblingSuggestion(SQLModel, table=True):
    """LLM-ranked sibling project suggestion (undirected pair)."""

    __tablename__ = "project_sibling_suggestions"
    __table_args__ = (
        UniqueConstraint(
            "project_a_id", "project_b_id", name="uq_project_sibling_pair"
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    project_a_id: int = Field(foreign_key="projects.id", index=True)
    project_b_id: int = Field(foreign_key="projects.id", index=True)
    score: float = Field(default=0.0)
    status: str = Field(
        default="suggested", max_length=16
    )  # suggested | confirmed | dismissed
    rationale: str = Field(default="", max_length=4096)
    created_ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    evaluated_ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confirmed_ts: Optional[datetime] = Field(default=None)
    dismissed_ts: Optional[datetime] = Field(default=None)


class Mission(SQLModel, table=True):
    __tablename__ = "missions"

    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: int = Field(foreign_key="projects.id", index=True)
    title: str = Field(max_length=255)
    status: str = Field(
        default="pending", max_length=32
    )  # pending|running|completed|failed
    owner: Optional[str] = Field(default=None, max_length=128)
    run_mode: str = Field(
        default="sequential", max_length=32
    )  # sequential|parallel|loop
    context: Optional[dict] = Field(default=None, sa_column=Column(JSON, nullable=True))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TaskGroup(SQLModel, table=True):
    __tablename__ = "task_groups"

    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    mission_id: UUID = Field(foreign_key="missions.id", index=True)
    title: str = Field(max_length=255)
    kind: str = Field(default="sequential", max_length=32)  # sequential|parallel|loop
    order: int = Field(default=0)
    status: str = Field(default="pending", max_length=32)


class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    mission_id: Optional[UUID] = Field(
        default=None, foreign_key="missions.id", index=True
    )
    group_id: UUID = Field(foreign_key="task_groups.id", index=True)
    agent_id: int = Field(foreign_key="agents.id", index=True)
    title: str = Field(max_length=255)
    status: str = Field(default="pending", max_length=32)
    order: int = Field(default=0)
    input: Optional[dict] = Field(default=None, sa_column=Column(JSON, nullable=True))
    output: Optional[dict] = Field(default=None, sa_column=Column(JSON, nullable=True))
    error: Optional[str] = Field(default=None)


class Artifact(SQLModel, table=True):
    __tablename__ = "artifacts"

    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    mission_id: UUID = Field(foreign_key="missions.id", index=True)
    task_id: Optional[UUID] = Field(default=None, foreign_key="tasks.id", index=True)
    type: str = Field(max_length=64)  # file|diff|plan|test_result|screenshot
    scope: str = Field(default="project", max_length=32)  # session|user|project
    path: str = Field(max_length=1024)
    version: str = Field(max_length=64)
    sha256: str = Field(max_length=64)
    content_meta: Optional[dict] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    tags: Optional[list[str]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )


class Knowledge(SQLModel, table=True):
    __tablename__ = "knowledge"

    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    artifact_id: UUID = Field(foreign_key="artifacts.id", index=True)
    source_artifact_id: Optional[UUID] = Field(
        default=None, foreign_key="artifacts.id", index=True
    )
    version: Optional[str] = Field(default=None, max_length=64)
    sha256: Optional[str] = Field(default=None, max_length=64)
    scope: str = Field(default="project", max_length=32)
    tags: Optional[list[str]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    summary: Optional[str] = Field(default=None, max_length=1024)
    reusable: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WorkflowRun(SQLModel, table=True):
    __tablename__ = "workflow_runs"

    run_id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    mission_id: UUID = Field(foreign_key="missions.id", index=True)
    mode: str = Field(default="sequential", max_length=32)
    status: str = Field(default="running", max_length=32)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = Field(default=None)
    trace_uri: Optional[str] = Field(default=None, max_length=1024)
