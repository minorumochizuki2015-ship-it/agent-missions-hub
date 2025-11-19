from __future__ import annotations

"""Mission / Task / Artifact / Knowledge のドメインモデル骨子。"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class MissionStatus(str, Enum):
    """ミッションのステータスを表す列挙。"""

    DRAFT = "draft"
    RUNNING = "running"
    NEEDS_REVIEW = "needs_review"
    DONE = "done"
    FAILED = "failed"


class TaskKind(str, Enum):
    """タスク種別を表す列挙。"""

    RESEARCH = "research"
    PLAN = "plan"
    IMPLEMENT = "implement"
    TEST = "test"
    DELIVER = "deliver"
    SELF_HEAL = "self_heal"


class TaskStatus(str, Enum):
    """タスクのステータスを表す列挙。"""

    PENDING = "pending"
    RUNNING = "running"
    BLOCKED = "blocked"
    DONE = "done"
    FAILED = "failed"


@dataclass(slots=True)
class Artifact:
    """成果物を表現するモデル。"""

    id: str
    mission_id: str
    name: str
    type: str
    uri: str
    created_at: datetime
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class Knowledge:
    """再利用可能なナレッジ断片を表すモデル。"""

    id: str
    mission_id: str
    title: str
    summary: str
    source_artifact_id: Optional[str]
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class Task:
    """ワークフローを構成するタスクモデル。"""

    id: str
    mission_id: str
    group_id: Optional[str]
    kind: TaskKind
    status: TaskStatus = TaskStatus.PENDING
    assignee_agent_id: Optional[str] = None
    summary: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class TaskGroup:
    """タスクのまとまり（シーケンシャル/並列/ループの単位）。"""

    id: str
    mission_id: str
    name: str
    sequence: int
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class Mission:
    """ミッション全体を表すモデル。"""

    id: str
    project_key: str
    title: str
    status: MissionStatus = MissionStatus.DRAFT
    summary: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    agent_ids: List[str] = field(default_factory=list)
    knowledge_ids: List[str] = field(default_factory=list)
