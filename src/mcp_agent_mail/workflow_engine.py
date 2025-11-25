"""ミッションとタスクを実行するワークフローエンジン。"""

from __future__ import annotations

import hashlib
import json
import logging
import traceback
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from .models import Artifact, Knowledge, Mission, Task, TaskGroup, WorkflowRun

TRACE_DIR_DEFAULT = Path("data/logs/current/audit/workflow_runs")

logger = logging.getLogger(__name__)


def _build_trace_path(trace_dir: Path | None, run_id: UUID) -> Path:
    """Trace ファイルのパスを準備し、親ディレクトリを確保する。"""
    target_dir = trace_dir or TRACE_DIR_DEFAULT
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir / f"workflow_run_{run_id}.jsonl"


def _write_trace_entry(
    trace_path: Path | None, event: str, payload: dict[str, Any]
) -> None:
    """Trace ファイルに JSON line を追記する。"""
    if trace_path is None:
        return
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {"ts": datetime.now(timezone.utc).isoformat(), "event": event}
    entry.update(payload)
    with trace_path.open("a", encoding="utf-8") as fh:
        json.dump(entry, fh, ensure_ascii=False)
        fh.write("\n")


class WorkflowContext:
    """ワークフロー実行中にタスク間で共有するコンテキストを保持する。"""

    def __init__(
        self,
        mission_id: UUID,
        session: AsyncSession,
        run_id: UUID,
        trace_path: Path | None = None,
    ):
        self.mission_id = mission_id
        self.session = session
        self.run_id = run_id
        self.shared_data: dict[str, Any] = {}
        self.execution_history: list[dict[str, Any]] = []
        self.trace_path = trace_path

    def update(self, key: str, value: Any) -> None:
        """共有データをセットする。"""
        self.shared_data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """共有データを取得する。"""
        return self.shared_data.get(key, default)

    def append_history(self, entry: dict[str, Any]) -> None:
        """実行履歴にイベントを追加する。"""
        self.execution_history.append(entry)
        _write_trace_entry(self.trace_path, "workflow_engine_task_event", entry)


class WorkflowEngine(ABC):
    """ワークフローエンジンの抽象基底クラス。"""

    def __init__(self, session: AsyncSession, trace_dir: Path | None = None):
        self.session = session
        self.trace_dir = Path(trace_dir or TRACE_DIR_DEFAULT)

    @abstractmethod
    async def run(self, mission: Mission) -> str:
        """ミッションを実行し、最終ステータスを返す。"""


class SequentialWorkflow(WorkflowEngine):
    """タスクグループとタスクを順次実行するワークフロー。"""

    async def run(self, mission: Mission) -> str:
        logger.info(f"Starting mission {mission.id}: {mission.title}")
        mission.status = "running"
        mission.updated_at = datetime.now(timezone.utc)
        self.session.add(mission)
        await self.session.commit()

        run = WorkflowRun(
            mission_id=mission.id,
            mode=mission.run_mode or "sequential",
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        trace_path = _build_trace_path(self.trace_dir, run.run_id)
        run.trace_uri = str(trace_path)
        self.session.add(run)
        await self.session.commit()

        context = WorkflowContext(
            mission.id, self.session, run.run_id, trace_path=trace_path
        )
        if mission.context:
            context.shared_data.update(mission.context)

        _write_trace_entry(
            trace_path,
            "workflow_engine_run_started",
            {
                "mission_id": str(mission.id),
                "mode": run.mode,
                "status": run.status,
                "run_id": str(run.run_id),
            },
        )

        last_task: Task | None = None
        try:
            # Fetch task groups sorted by order
            stmt = (
                select(TaskGroup)
                .where(TaskGroup.mission_id == mission.id)
                .order_by(TaskGroup.order)
            )
            result = await self.session.execute(stmt)
            task_groups = result.scalars().all()

            for group in task_groups:
                await self.execute_group(group, context)

                # Reload mission to check if it was cancelled externally
                await self.session.refresh(mission)
                if mission.status == "failed":
                    break
                # keep reference to last executed task for summary artifact
                stmt_tasks = (
                    select(Task).where(Task.group_id == group.id).order_by(Task.order)
                )
                result_tasks = await self.session.execute(stmt_tasks)
                tasks_in_group = result_tasks.scalars().all()
                if tasks_in_group:
                    last_task = tasks_in_group[-1]

            if mission.status != "failed":
                mission.status = "completed"
                run.status = "completed"
                if last_task is not None:
                    await _record_self_heal_artifact(
                        session=self.session,
                        context=context,
                        task=last_task,
                        summary="workflow completed",
                        success=True,
                    )

        except Exception as e:
            logger.error(f"Mission failed: {e}")
            traceback.print_exc()
            mission.status = "failed"
            run.status = "failed"
            _write_trace_entry(
                trace_path,
                "workflow_engine_run_failed",
                {
                    "mission_id": str(mission.id),
                    "run_id": str(run.run_id),
                    "error": str(e),
                },
            )
            # In a real system, we might want to store the error in the mission model

        mission.updated_at = datetime.now(timezone.utc)
        self.session.add(mission)
        run.ended_at = datetime.now(timezone.utc)
        self.session.add(run)
        _write_trace_entry(
            trace_path,
            "workflow_engine_run_completed",
            {
                "mission_id": str(mission.id),
                "run_id": str(run.run_id),
                "status": mission.status,
            },
        )
        await self.session.commit()

        logger.info(f"Mission {mission.id} finished with status: {mission.status}")
        return mission.status

    async def execute_group(self, group: TaskGroup, context: WorkflowContext):
        """タスクグループを順次実行する。"""
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

            stmt = select(Task).where(Task.group_id == group.id).order_by(Task.order)
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
        """単一タスクを実行し、出力・ステータスを反映する (MVP では擬似実行)。"""
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

            task.output = {
                "result": "simulated_success",
                "timestamp": str(datetime.now()),
            }
            task.status = "completed"
            context.append_history(
                {
                    "task_id": str(task.id),
                    "status": task.status,
                    "output": task.output,
                    "run_id": str(context.run_id),
                }
            )

        except Exception as e:
            task.error = str(e)
            task.status = "failed"
            logger.error(f"Task execution failed: {e}")
        finally:
            self.session.add(task)
            await self.session.commit()


class SelfHealWorkflow(SequentialWorkflow):
    """タスク失敗時にリカバリを試みるワークフロー。"""

    async def execute_group(self, group: TaskGroup, context: WorkflowContext):
        try:
            await super().execute_group(group, context)
        except Exception as e:
            logger.warning(
                f"TaskGroup {group.id} failed, attempting self-heal... Error: {e}"
            )

            # Check if we can heal
            # Simple logic: If a task failed, try to insert a recovery task

            # 1. Identify failed task
            stmt = select(Task).where(
                Task.group_id == group.id, Task.status == "failed"
            )
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
                    input={
                        "error": failed_task.error,
                        "original_input": failed_task.input,
                    },
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
                    await _record_self_heal_artifact(
                        session=self.session,
                        context=context,
                        task=failed_task,
                        summary=f"Recovered after {failed_task.title} -> {failed_task.error}",
                    )
                    return  # Suppress the exception
                else:
                    logger.error("Recovery failed.")
                    await _record_self_heal_artifact(
                        session=self.session,
                        context=context,
                        task=failed_task,
                        summary=f"Recovery failed for {failed_task.title}: {failed_task.error}",
                        success=False,
                    )
                    raise e  # Re-raise original exception
            else:
                raise e


async def _record_self_heal_artifact(
    session: AsyncSession,
    context: WorkflowContext,
    task: Task,
    summary: str,
    success: bool = True,
) -> tuple[Artifact, Knowledge | None]:
    """Record artifact + knowledge entry for self-heal events."""

    run_id = context.run_id
    mission_id = context.mission_id
    version = context.get("workflow_version", "v1")
    detail = summary or "Self-heal recovery triggered"
    sha_seed = f"{run_id}:{task.id}:{detail}"
    sha = hashlib.sha256(sha_seed.encode()).hexdigest()
    artifact = Artifact(
        mission_id=mission_id,
        task_id=task.id,
        type="self_heal_artifact" if success else "self_heal_failure",
        scope="mission",
        path=f"self_heal/{run_id}/{task.id}:{detail[:32]}",
        version=version,
        sha256=sha,
        tags=["self-heal", "workflow"],
        content_meta={"error": task.error, "status": task.status, "success": success},
    )
    session.add(artifact)
    await session.commit()
    await session.refresh(artifact)

    knowledge = Knowledge(
        artifact_id=artifact.id,
        source_artifact_id=artifact.id,
        version=artifact.version,
        sha256=artifact.sha256,
        scope=artifact.scope,
        summary=detail[:1024],
        tags=["self-heal", "knowledge"],
        reusable=True,
    )
    session.add(knowledge)
    await session.commit()
    await session.refresh(knowledge)
    return artifact, knowledge
