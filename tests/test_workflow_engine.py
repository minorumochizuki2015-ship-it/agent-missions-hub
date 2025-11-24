import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from mcp_agent_mail.models import Agent, Mission, Project, Task, TaskGroup
from mcp_agent_mail.workflow_engine import SelfHealWorkflow, SequentialWorkflow


# Test setup
@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_sequential_workflow_success(db_session):
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
    engine = SequentialWorkflow(db_session)
    status = await engine.run(mission)

    assert status == "completed"

    # Verify tasks
    await db_session.refresh(task1)
    await db_session.refresh(task2)
    assert task1.status == "completed"
    assert task2.status == "completed"
    assert task1.output == {"result": "simulated_success", "timestamp": task1.output["timestamp"]}


@pytest.mark.asyncio
async def test_self_heal_workflow(db_session):
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

    engine = MockFailingWorkflow(db_session)
    status = await engine.run(mission)

    # Should be completed because of healing
    assert status == "completed"

    await db_session.refresh(task1)
    assert task1.status == "failed"

    # Check for recovery task
    from sqlmodel import select

    stmt = select(Task).where(Task.group_id == group.id, Task.title.contains("Recovery"))
    result = await db_session.execute(stmt)
    recovery_task = result.scalars().first()

    assert recovery_task is not None
    assert recovery_task.status == "completed"
