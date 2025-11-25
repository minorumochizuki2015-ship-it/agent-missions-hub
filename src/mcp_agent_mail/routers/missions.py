"""Mission-centric CRUD/trace API for Phase 2."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from ..db import get_session
from ..models import Artifact, Knowledge, Mission, TaskGroup, WorkflowRun
from ..workflow_engine import SelfHealWorkflow, SequentialWorkflow

router = APIRouter(prefix="/missions", tags=["missions"])


class MissionSummary(SQLModel):
    """Lightweight view of a mission for list endpoints."""

    id: UUID
    title: str
    status: str
    run_mode: str
    task_group_count: int = 0
    artifact_count: int = 0
    updated_at: datetime


class ArtifactPayload(BaseModel):
    """Payload for artifact creation."""

    type: str
    path: str
    version: str
    sha256: str
    scope: str = Field(default="mission", max_length=32)
    tags: Optional[list[str]] = None
    content_meta: Optional[dict[str, Any]] = None
    knowledge_summary: Optional[str] = None
    knowledge_tags: Optional[list[str]] = None


class ArtifactRead(SQLModel):
    """Read model for artifact responses."""

    id: UUID
    mission_id: UUID
    task_id: Optional[UUID]
    type: str
    path: str
    version: str
    sha256: str
    scope: str
    tags: Optional[list[str]]
    knowledge_id: Optional[UUID] = None


@router.get("/", response_model=list[MissionSummary])
async def list_missions(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[MissionSummary]:
    stmt = select(Mission)
    missions = (await session.execute(stmt)).scalars().all()

    tg_counts = await session.execute(
        select(TaskGroup.mission_id, func.count(TaskGroup.id)).group_by(
            TaskGroup.mission_id
        )
    )
    tg_map = {row[0]: row[1] for row in tg_counts}

    artifact_counts = await session.execute(
        select(Artifact.mission_id, func.count(Artifact.id)).group_by(
            Artifact.mission_id
        )
    )
    artifact_map = {row[0]: row[1] for row in artifact_counts}

    return [
        MissionSummary(
            id=mission.id,
            title=mission.title,
            status=mission.status,
            run_mode=mission.run_mode,
            task_group_count=tg_map.get(mission.id, 0),
            artifact_count=artifact_map.get(mission.id, 0),
            updated_at=mission.updated_at,
        )
        for mission in missions
    ]


@router.get("/{mission_id}/artifacts", response_model=list[ArtifactRead])
async def list_artifacts(
    mission_id: UUID, session: Annotated[AsyncSession, Depends(get_session)]
) -> list[ArtifactRead]:
    mission = await session.get(Mission, mission_id)
    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="MISSION_NOT_FOUND"
        )

    stmt = (
        select(Artifact)
        .where(Artifact.mission_id == mission_id)
        .order_by(Artifact.path)
    )
    artifacts = (await session.execute(stmt)).scalars().all()

    knowledge_entries = await session.execute(
        select(Knowledge.artifact_id, Knowledge.id).where(
            Knowledge.artifact_id.in_([a.id for a in artifacts])
        )
    )
    knowledge_map = {row[0]: row[1] for row in knowledge_entries}

    return [
        ArtifactRead(
            id=artifact.id,
            mission_id=artifact.mission_id,
            task_id=artifact.task_id,
            type=artifact.type,
            path=artifact.path,
            version=artifact.version,
            sha256=artifact.sha256,
            scope=artifact.scope,
            tags=artifact.tags,
            knowledge_id=knowledge_map.get(artifact.id),
        )
        for artifact in artifacts
    ]


@router.post(
    "/{mission_id}/artifacts",
    response_model=ArtifactRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_artifact(
    mission_id: UUID,
    payload: ArtifactPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ArtifactRead:
    mission = await session.get(Mission, mission_id)
    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="MISSION_NOT_FOUND"
        )

    artifact = Artifact(
        mission_id=mission_id,
        task_id=None,
        type=payload.type,
        path=payload.path,
        version=payload.version,
        sha256=payload.sha256,
        scope=payload.scope,
        tags=payload.tags,
        content_meta=payload.content_meta,
    )
    session.add(artifact)
    await session.commit()
    await session.refresh(artifact)

    knowledge_id: Optional[UUID] = None
    if payload.knowledge_summary:
        knowledge = Knowledge(
            artifact_id=artifact.id,
            source_artifact_id=artifact.id,
            version=artifact.version,
            sha256=artifact.sha256,
            scope=artifact.scope,
            summary=payload.knowledge_summary,
            tags=payload.knowledge_tags or ["workflow"],
            reusable=True,
        )
        session.add(knowledge)
        await session.commit()
        await session.refresh(knowledge)
        knowledge_id = knowledge.id

    return ArtifactRead(
        id=artifact.id,
        mission_id=artifact.mission_id,
        task_id=artifact.task_id,
        type=artifact.type,
        path=artifact.path,
        version=artifact.version,
        sha256=artifact.sha256,
        scope=artifact.scope,
        tags=artifact.tags,
        knowledge_id=knowledge_id,
    )


class MissionRunResponse(BaseModel):
    """ワークフロー実行の結果概要。"""

    mission_id: UUID
    status: str
    run_id: UUID


@router.post(
    "/{mission_id}/run",
    response_model=MissionRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def run_mission(
    mission_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    allow_self_heal: bool = True,
) -> MissionRunResponse:
    mission = await session.get(Mission, mission_id)
    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="MISSION_NOT_FOUND"
        )

    # Ensure there is at least one task_group; otherwise running is meaningless
    tg_exists = await session.execute(
        select(TaskGroup.id).where(TaskGroup.mission_id == mission_id).limit(1)
    )
    if not tg_exists.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="NO_TASK_GROUPS"
        )

    workflow_cls = SelfHealWorkflow if allow_self_heal else SequentialWorkflow
    engine = workflow_cls(session)
    status_result = await engine.run(mission)

    # pick latest workflow_run for this mission
    run_row = await session.execute(
        select(WorkflowRun)
        .where(WorkflowRun.mission_id == mission_id)
        .order_by(WorkflowRun.started_at.desc())
    )
    run = run_row.scalars().first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="RUN_NOT_RECORDED"
        )

    return MissionRunResponse(
        mission_id=mission_id, status=status_result, run_id=run.run_id
    )
