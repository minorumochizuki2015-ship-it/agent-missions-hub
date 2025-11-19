from __future__ import annotations

"""SQLModel ベースの永続化スキーマ雛形。"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Column
from sqlalchemy.orm import sessionmaker
from sqlmodel import Field, Session, SQLModel, create_engine, select


class Project(SQLModel, table=True):
    """プロジェクト情報を保持するテーブル。"""

    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(index=True, unique=True)
    title: str = Field(default="")


class Agent(SQLModel, table=True):
    """エージェントの基本属性を保持するテーブル。"""

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id", index=True)
    name: str
    program: str = Field(default="")
    model: str = Field(default="")
    task_description: str = Field(default="")
    task_summary: str = Field(default="")
    skills: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    primary_model: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Mission(SQLModel, table=True):
    """ミッションのメタデータを保持するテーブル。"""

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id", index=True)
    title: str
    status: str = Field(default="draft")
    summary: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TaskGroup(SQLModel, table=True):
    """タスクグループ（シーケンス単位）を保持するテーブル。"""

    id: int | None = Field(default=None, primary_key=True)
    mission_id: int = Field(foreign_key="mission.id", index=True)
    name: str
    sequence: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Task(SQLModel, table=True):
    """個別タスクを保持するテーブル。"""

    id: int | None = Field(default=None, primary_key=True)
    mission_id: int = Field(foreign_key="mission.id", index=True)
    group_id: Optional[int] = Field(default=None, foreign_key="taskgroup.id", index=True)
    kind: str
    status: str = Field(default="pending")
    assignee_agent_id: Optional[int] = Field(default=None, foreign_key="agent.id")
    summary: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Artifact(SQLModel, table=True):
    """成果物を保持するテーブル。"""

    id: int | None = Field(default=None, primary_key=True)
    mission_id: int = Field(foreign_key="mission.id", index=True)
    task_id: Optional[int] = Field(default=None, foreign_key="task.id")
    name: str
    type: str = Field(default="")
    uri: str = Field(default="")
    metadata: dict[str, str] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Knowledge(SQLModel, table=True):
    """再利用可能なナレッジ断片を保持するテーブル。"""

    id: int | None = Field(default=None, primary_key=True)
    mission_id: int = Field(foreign_key="mission.id", index=True)
    title: str
    summary: str = Field(default="")
    source_artifact_id: Optional[int] = Field(default=None, foreign_key="artifact.id")
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Message(SQLModel, table=True):
    """送受信メッセージの記録を保持するテーブル。"""

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id", index=True)
    sender_name: str
    to: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    subject: str = Field(default="")
    body_md: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)


def get_engine(database_url: str) -> object:
    """同期エンジンを構築する。"""

    return create_engine(database_url, echo=False)


def init_db(database_url: str) -> None:
    """スキーマを一括で作成する初期化ヘルパー。"""

    engine = get_engine(database_url)
    SQLModel.metadata.create_all(engine)


def get_session(database_url: str) -> Session:
    """セッションを生成する。呼び出し側でクローズする。"""

    engine = get_engine(database_url)
    SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
    return SessionLocal()
