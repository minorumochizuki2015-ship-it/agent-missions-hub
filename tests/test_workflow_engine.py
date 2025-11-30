# pyright: reportOptionalMemberAccess=false, reportOptionalSubscript=false, reportOptionalIterable=false
# pytype: disable=attribute-error

import json
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, select

from mcp_agent_mail.models import (
    Agent,
    Artifact,
    Knowledge,
    Mission,
    Project,
    Signal,
    Task,
    TaskGroup,
    WorkflowRun,
)
from mcp_agent_mail.workflow_engine import SelfHealWorkflow, SequentialWorkflow


# Test setup
@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = sessionmaker(  # type: ignore[arg-type]
        engine, class_=AsyncSession, expire_on_commit=False
    )
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

    artifact_rows = (await db_session.execute(select(Artifact))).scalars().all()
    assert artifact_rows
    artifact = next(
        (
            row
            for row in artifact_rows
            if row.type is not None and row.type.startswith("self_heal")
        ),
        None,
    )
    assert artifact is not None
    knowledge_rows = (await db_session.execute(select(Knowledge))).scalars().all()
    assert knowledge_rows
    first_knowledge = next(
        (row for row in knowledge_rows if row.artifact_id == artifact.id), None
    )
    assert first_knowledge is not None and first_knowledge.summary is not None

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
    task_rows = (
        (await db_session.execute(select(Task).where(Task.group_id == group.id)))
        .scalars()
        .all()
    )
    recovery_task = next(
        (row for row in task_rows if row.title is not None and "Recovery" in row.title),
        None,
    )
    assert recovery_task is not None and recovery_task.status == "completed"
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
    artifacts = (await db_session.execute(select(Artifact))).scalars().all()
    failure_artifacts = [
        row
        for row in artifacts
        if row.type is not None and row.type == "self_heal_failure"
    ]
    assert failure_artifacts
    signals = (await db_session.execute(select(Signal))).scalars().all()
    assert any(sig.type == "self_heal_failed" for sig in signals)
    knowledge_rows = (await db_session.execute(select(Knowledge))).scalars().all()
    related_knowledge = [
        row
        for row in knowledge_rows
        if row.artifact_id in {a.id for a in failure_artifacts}
    ]
    assert related_knowledge
    assert related_knowledge[0].summary is not None


@pytest.mark.asyncio
async def test_self_heal_writes_ci_evidence(db_session, tmp_path: Path, monkeypatch):
    """self-heal が ci_evidence に試行/成功イベントを残すことを検証する。"""
    monkeypatch.chdir(tmp_path)
    ci_evidence = tmp_path / "observability/policy/ci_evidence.jsonl"
    ci_evidence.parent.mkdir(parents=True, exist_ok=True)
    trace_dir = tmp_path / "workflow_runs"

    project = Project(slug="heal-ci", human_key="Heal CI Project")
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

    class MockFailOnce(SelfHealWorkflow):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.failed = False

        async def execute_task(self, task, context):
            if not self.failed and "Recovery" not in task.title:
                self.failed = True
                task.status = "failed"
                task.error = "Simulated failure"
                self.session.add(task)
                await self.session.commit()
            else:
                await super().execute_task(task, context)

    failing_task = Task(group_id=group.id, agent_id=agent.id, title="Failing Task")
    db_session.add(failing_task)
    await db_session.commit()

    engine = MockFailOnce(db_session, trace_dir=trace_dir)
    status = await engine.run(mission)

    assert status == "completed"
    assert ci_evidence.exists()
    events = [
        json.loads(line)
        for line in ci_evidence.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert any(ev["event"] == "workflow_self_heal_attempt" for ev in events)
    assert any(ev["event"] == "workflow_self_heal_success" for ev in events)
    assert any(ev["event"] == "workflow_run_completed" for ev in events)
