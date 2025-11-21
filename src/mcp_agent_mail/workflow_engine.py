"""Workflow Engine for executing Missions and Tasks."""

from __future__ import annotations

import logging
import traceback
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from .models import Mission, Task, TaskGroup

logger = logging.getLogger(__name__)


class WorkflowContext:
    """Context passed between tasks during workflow execution."""

    def __init__(self, mission_id: UUID, session: AsyncSession):
        self.mission_id = mission_id
        self.session = session
        self.shared_data: dict[str, Any] = {}
        self.execution_history: list[dict[str, Any]] = []

    def update(self, key: str, value: Any):
        self.shared_data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.shared_data.get(key, default)


class WorkflowEngine(ABC):
    """Abstract base class for workflow engines."""

    def __init__(self, session: AsyncSession):
        self.session = session

    @abstractmethod
    async def run(self, mission: Mission) -> str:
        """Run the mission. Returns the final status."""
        pass


class SequentialWorkflow(WorkflowEngine):
    """Executes task groups and tasks in sequential order."""

    async def run(self, mission: Mission) -> str:
        logger.info(f"Starting mission {mission.id}: {mission.title}")
        mission.status = "running"
        mission.updated_at = datetime.now(timezone.utc)
        self.session.add(mission)
        await self.session.commit()

        context = WorkflowContext(mission.id, self.session)
        if mission.context:
            context.shared_data.update(mission.context)

        try:
            # Fetch task groups sorted by order
            stmt = select(TaskGroup).where(TaskGroup.mission_id == mission.id).order_by(TaskGroup.order)
            result = await self.session.execute(stmt)
            task_groups = result.scalars().all()

            for group in task_groups:
                await self.execute_group(group, context)

                # Reload mission to check if it was cancelled externally
                await self.session.refresh(mission)
                if mission.status == "failed":
                    break

            if mission.status != "failed":
                mission.status = "completed"

        except Exception as e:
            logger.error(f"Mission failed: {e}")
            traceback.print_exc()
            mission.status = "failed"
            # In a real system, we might want to store the error in the mission model

        mission.updated_at = datetime.now(timezone.utc)
        self.session.add(mission)
        await self.session.commit()

        logger.info(f"Mission {mission.id} finished with status: {mission.status}")
        return mission.status

    async def execute_group(self, group: TaskGroup, context: WorkflowContext):
        logger.info(f"Executing TaskGroup {group.id}: {group.title} ({group.kind})")
        group.status = "running"
        self.session.add(group)
        await self.session.commit()

        try:
            # Fetch tasks for this group
            # Note: In a real sequential group, we might want an order for tasks too.
            # For now, we assume tasks in a group can be run in any order or insertion order.
            # But 'sequential' usually implies an order. Let's assume tasks have an implicit order or we just run them.
            # If TaskGroup kind is 'sequential', we run tasks one by one.
            # If 'parallel', we could run them concurrently (not implemented in v1).

            stmt = select(Task).where(Task.group_id == group.id)
            result = await self.session.execute(stmt)
            tasks = result.scalars().all()

            for task in tasks:
                await self.execute_task(task, context)
                if task.status == "failed":
                    raise Exception(f"Task {task.id} failed: {task.error}")

            group.status = "completed"

        except Exception as e:
            logger.error(f"TaskGroup {group.id} failed: {e}")
            group.status = "failed"
            # Propagate error to stop mission
            raise e
        finally:
            self.session.add(group)
            await self.session.commit()

    async def execute_task(self, task: Task, context: WorkflowContext):
        logger.info(f"Executing Task {task.id}: {task.title}")
        task.status = "running"
        self.session.add(task)
        await self.session.commit()

        try:
            # Here is where we would actually invoke the agent or tool.
            # For V1, we simulate execution or look for a 'runner' implementation.
            # Since we don't have the full Agent execution environment hooked up here yet,
            # we will simulate success if no error is present, or perform a basic action.

            # Input propagation
            if task.input is None:
                task.input = {}

            # Example: If previous task had output, merge it?
            # For now, just log.

            # SIMULATION:
            # In a real implementation, this would call:
            # agent = get_agent(task.agent_id)
            # result = await agent.execute(task.title, task.input)

            # For now, we assume the task is "done" by the time we get here
            # OR we are just marking it as done.
            # BUT, the requirement is "WorkflowEngine".
            # Let's assume we are orchestrating.

            # TODO: Implement actual Agent dispatch.
            # For MVP, we'll just mark completed.

            task.output = {"result": "simulated_success", "timestamp": str(datetime.now())}
            task.status = "completed"

        except Exception as e:
            task.error = str(e)
            task.status = "failed"
            logger.error(f"Task execution failed: {e}")
        finally:
            self.session.add(task)
            await self.session.commit()


class SelfHealWorkflow(SequentialWorkflow):
    """Workflow that attempts to recover from task failures."""

    async def execute_group(self, group: TaskGroup, context: WorkflowContext):
        try:
            await super().execute_group(group, context)
        except Exception as e:
            logger.warning(f"TaskGroup {group.id} failed, attempting self-heal... Error: {e}")

            # Check if we can heal
            # Simple logic: If a task failed, try to insert a recovery task

            # 1. Identify failed task
            stmt = select(Task).where(Task.group_id == group.id, Task.status == "failed")
            result = await self.session.execute(stmt)
            failed_task = result.scalars().first()

            if failed_task:
                logger.info(f"Attempting to heal failed task: {failed_task.title}")

                # 2. Create recovery task
                recovery_task = Task(
                    group_id=group.id,
                    agent_id=failed_task.agent_id,  # Same agent tries to fix
                    title=f"Recovery: {failed_task.title}",
                    status="pending",
                    input={"error": failed_task.error, "original_input": failed_task.input},
                )
                self.session.add(recovery_task)
                await self.session.commit()

                # 3. Execute recovery task
                await self.execute_task(recovery_task, context)

                if recovery_task.status == "completed":
                    logger.info("Recovery successful! Resuming group...")
                    # Mark group as running again? Or just proceed?
                    # Ideally we should retry the original task or move on.
                    # For V1, if recovery works, we consider the group "healed" (but maybe partial).
                    group.status = "completed"  # Force complete for now
                    self.session.add(group)
                    await self.session.commit()
                    return  # Suppress the exception
                else:
                    logger.error("Recovery failed.")
                    raise e  # Re-raise original exception
            else:
                raise e
