# pyright: reportOptionalMemberAccess=false, reportOptionalSubscript=false, reportOptionalIterable=false
# pytype: disable=attribute-error

import json
from pathlib import Path

import pytest
import pytest_asyncio
from mcp_agent_mail.models import (
    Agent,
    Artifact,
    Knowledge,
    Mission,
    Project,
    Task,
    TaskGroup,
    WorkflowRun,
)
from mcp_agent_mail.workflow_engine import SelfHealWorkflow, SequentialWorkflow
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, select


# Test setup
@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture
def workflow_trace_dir(tmp_path: Path) -> Path:
    return tmp_path / "workflow_runs"


@pytest.mark.asyncio
async def test_sequential_workflow_success(db_session, workflow_trace_dir: Path):
    # Setup data
    project = Project(slug="test-proj", human_key="Test Project")
    db_session.add(project)
    await db_session.commit()

    agent = Agent(project_id=project.id, name="TestAgent", program="test", model="test")
    db_session.add(agent)
    await db_session.commit()

    mission = Mission(project_id=project.id, title="Test Mission")
    db_session.add(mission)
    await db_session.commit()

    group = TaskGroup(mission_id=mission.id, title="Group 1")
    db_session.add(group)
    await db_session.commit()

    task1 = Task(group_id=group.id, agent_id=agent.id, title="Task 1")
    task2 = Task(group_id=group.id, agent_id=agent.id, title="Task 2")
    db_session.add(task1)
    db_session.add(task2)
    await db_session.commit()

    # Run workflow
    engine = SequentialWorkflow(db_session, trace_dir=workflow_trace_dir)
    status = await engine.run(mission)

    assert status == "completed"

    runs = (await db_session.execute(select(WorkflowRun))).scalars().all()
    assert len(runs) == 1
    run = runs[0]
    assert run.status == "completed"
    assert run.mode == "sequential"
    assert run.ended_at is not None
    assert run.trace_uri is not None
    trace_path = Path(run.trace_uri)
    assert trace_path.exists()
    events = [
        json.loads(line)
        for line in trace_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert any(event.get("event") == "workflow_engine_run_started" for event in events)
    assert any(
        event.get("event") == "workflow_engine_run_completed" for event in events
    )

    artifacts = (
        (
            await db_session.execute(
                select(Artifact).where(Artifact.type.like("self_heal%"))  # type: ignore[attr-defined]
            )
        )
        .scalars()
        .all()
    )
    assert artifacts
    artifact = artifacts[0]
    assert artifact is not None
    knowledge_entries = await db_session.execute(
        select(Knowledge).where(Knowledge.artifact_id == artifact.id)
    )
    knowledge_list = list(knowledge_entries.scalars())
    assert knowledge_list
    first_knowledge = knowledge_list[0]
    assert first_knowledge is not None
    assert first_knowledge.summary is not None

    # Verify tasks
    await db_session.refresh(task1)
    await db_session.refresh(task2)
    assert task1.status == "completed"
    assert task2.status == "completed"
    assert task1.output is not None
    output = task1.output
    assert output is not None
    assert output.get("result") == "simulated_success"
    assert "timestamp" in output


@pytest.mark.asyncio
async def test_self_heal_workflow(db_session, workflow_trace_dir: Path):
    # Setup data
    project = Project(slug="heal-proj", human_key="Heal Project")
    db_session.add(project)
    await db_session.commit()

    agent = Agent(project_id=project.id, name="HealAgent", program="test", model="test")
    db_session.add(agent)
    await db_session.commit()

    mission = Mission(project_id=project.id, title="Heal Mission")
    db_session.add(mission)
    await db_session.commit()

    group = TaskGroup(mission_id=mission.id, title="Group 1")
    db_session.add(group)
    await db_session.commit()

    # Create a custom workflow that mocks failure for the first task
    class MockFailingWorkflow(SelfHealWorkflow):
        async def execute_task(self, task, context):
            if "Recovery" in task.title:
                # Recovery succeeds
                await super().execute_task(task, context)
            else:
                # Normal task fails
                task.status = "failed"
                task.error = "Simulated failure"
                self.session.add(task)
                await self.session.commit()

    task1 = Task(group_id=group.id, agent_id=agent.id, title="Failing Task")
    db_session.add(task1)
    await db_session.commit()

    engine = MockFailingWorkflow(db_session, trace_dir=workflow_trace_dir)
    status = await engine.run(mission)

    # Should be completed because of healing
    assert status == "completed"
    run = (await db_session.execute(select(WorkflowRun))).scalars().first()
    assert run is not None
    assert run.status == "completed"
    assert run.ended_at is not None

    await db_session.refresh(task1)
    assert task1.status == "failed"

    # Check for recovery task
    stmt = select(Task).where(
        Task.group_id == group.id,
        Task.title.contains("Recovery"),  # type: ignore[attr-defined]
    )
    result = await db_session.execute(stmt)
    recovery_task = result.scalars().first()

    assert recovery_task is not None
    assert recovery_task.status == "completed"
    run = (await db_session.execute(select(WorkflowRun))).scalars().first()
    assert run.trace_uri is not None
    trace_path = Path(run.trace_uri)
    assert trace_path.exists()
    events = [
        json.loads(line)
        for line in trace_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert any(event.get("event") == "workflow_engine_run_started" for event in events)
    assert any(
        event.get("event") == "workflow_engine_run_completed" for event in events
    )


@pytest.mark.asyncio
async def test_self_heal_failure_records_artifact(db_session):
    project = Project(slug="heal-fail", human_key="Heal Fail Project")
    db_session.add(project)
    await db_session.commit()

    agent = Agent(
        project_id=project.id, name="HealFailAgent", program="test", model="test"
    )
    db_session.add(agent)
    await db_session.commit()

    mission = Mission(project_id=project.id, title="Heal Fail Mission")
    db_session.add(mission)
    await db_session.commit()

    group = TaskGroup(mission_id=mission.id, title="Group 1")
    db_session.add(group)
    await db_session.commit()

    class MockAlwaysFail(SelfHealWorkflow):
        async def execute_task(self, task, context):
            task.status = "failed"
            task.error = "Simulated hard failure"
            self.session.add(task)
            await self.session.commit()

    task1 = Task(group_id=group.id, agent_id=agent.id, title="Failing Task")
    db_session.add(task1)
    await db_session.commit()

    engine = MockAlwaysFail(db_session, trace_dir=None)
    status = await engine.run(mission)

    assert status == "failed"
    # recovery artifact/knowledge should be recorded as failure
    artifacts = (
        (
            await db_session.execute(
                select(Artifact).where(Artifact.type == "self_heal_failure")
            )
        )
        .scalars()
        .all()
    )
    assert artifacts
    knowledge_entries = (
        (
            await db_session.execute(
                select(Knowledge).where(
                    Knowledge.artifact_id.in_([a.id for a in artifacts])  # type: ignore[attr-defined]
                )
            )
        )
        .scalars()
        .all()
    )
    assert knowledge_entries
    assert knowledge_entries[0].summary is not None
