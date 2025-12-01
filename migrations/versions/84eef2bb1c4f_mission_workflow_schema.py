"""mission workflow schema

Revision ID: 84eef2bb1c4f
Revises:
Create Date: 2025-11-20 18:16:59.211092

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import context, op
from sqlalchemy import inspect
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision: str = "84eef2bb1c4f"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table: str) -> bool:
    return inspector.has_table(table)


def _has_column(inspector: sa.Inspector, table: str, column: str) -> bool:
    return any(col.get("name") == column for col in inspector.get_columns(table))


def _has_index(inspector: sa.Inspector, table: str, name: str) -> bool:
    return any(idx.get("name") == name for idx in inspector.get_indexes(table))


def upgrade() -> None:
    """既存オブジェクトを尊重しつつミッション系スキーマを適用する。"""
    if context.is_offline_mode():
        op.execute("-- offline preview: guarded migration; run in online mode for inspection-aware DDL")
        return

    bind: Connection = op.get_bind()
    inspector = inspect(bind)

    # missions
    if not _has_table(inspector, "missions"):
        op.create_table(
            "missions",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
            sa.Column("owner", sa.String(length=128), nullable=True),
            sa.Column("run_mode", sa.String(length=32), nullable=False, server_default="sequential"),
            sa.Column("context", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("(DATETIME('now'))")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("(DATETIME('now'))")),
        )
        op.create_index("ix_missions_project_id", "missions", ["project_id"])
        op.create_index("ix_missions_status", "missions", ["status"])

    # task_groups
    if not _has_table(inspector, "task_groups"):
        op.create_table(
            "task_groups",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("mission_id", sa.String(length=36), sa.ForeignKey("missions.id"), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("kind", sa.String(length=32), nullable=False, server_default="sequential"),
            sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        )
        op.create_index("ix_task_groups_mission_id", "task_groups", ["mission_id"])
        op.create_index("ix_task_groups_order", "task_groups", ["order"])

    # tasks(新規 or 追加カラム)
    if not _has_table(inspector, "tasks"):
        op.create_table(
            "tasks",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("mission_id", sa.String(length=36), sa.ForeignKey("missions.id"), nullable=True),
            sa.Column("group_id", sa.String(length=36), sa.ForeignKey("task_groups.id"), nullable=False),
            sa.Column("agent_id", sa.Integer(), sa.ForeignKey("agents.id"), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
            sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("input", sa.JSON(), nullable=True),
            sa.Column("output", sa.JSON(), nullable=True),
            sa.Column("error", sa.String(), nullable=True),
        )
    else:
        if not _has_column(inspector, "tasks", "mission_id"):
            op.add_column("tasks", sa.Column("mission_id", sa.String(length=36), nullable=True))
        if not _has_column(inspector, "tasks", "order"):
            op.add_column(
                "tasks",
                sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
            )
        if not _has_column(inspector, "tasks", "input"):
            op.add_column("tasks", sa.Column("input", sa.JSON(), nullable=True))
        if not _has_column(inspector, "tasks", "output"):
            op.add_column("tasks", sa.Column("output", sa.JSON(), nullable=True))
        if not _has_column(inspector, "tasks", "error"):
            op.add_column("tasks", sa.Column("error", sa.String(), nullable=True))

    if _has_table(inspector, "tasks"):
        if not _has_index(inspector, "tasks", "ix_tasks_mission_id"):
            op.create_index("ix_tasks_mission_id", "tasks", ["mission_id"])
        if not _has_index(inspector, "tasks", "ix_tasks_group_id"):
            op.create_index("ix_tasks_group_id", "tasks", ["group_id"])
        if not _has_index(inspector, "tasks", "ix_tasks_agent_id"):
            op.create_index("ix_tasks_agent_id", "tasks", ["agent_id"])

    # artifacts 追加カラム
    if _has_table(inspector, "artifacts"):
        if not _has_column(inspector, "artifacts", "scope"):
            op.add_column(
                "artifacts",
                sa.Column("scope", sa.String(length=32), nullable=False, server_default="project"),
            )
        if not _has_column(inspector, "artifacts", "tags"):
            op.add_column("artifacts", sa.Column("tags", sa.JSON(), nullable=True))

    # knowledge 追加カラム
    if _has_table(inspector, "knowledge") and not _has_column(inspector, "knowledge", "summary"):
        op.add_column(
            "knowledge",
            sa.Column("summary", sa.String(length=1024), nullable=True),
        )

    # workflow_runs
    if not _has_table(inspector, "workflow_runs"):
        op.create_table(
            "workflow_runs",
            sa.Column("run_id", sa.String(length=36), primary_key=True),
            sa.Column("mission_id", sa.String(length=36), sa.ForeignKey("missions.id"), nullable=False),
            sa.Column("mode", sa.String(length=32), nullable=False, server_default="sequential"),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="running"),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("(DATETIME('now'))")),
            sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("trace_uri", sa.String(length=1024), nullable=True),
        )
        op.create_index("ix_workflow_runs_mission_id", "workflow_runs", ["mission_id"])
        op.create_index("ix_workflow_runs_status", "workflow_runs", ["status"])


def downgrade() -> None:
    """ミッション系スキーマを可能な範囲で巻き戻す。"""
    if context.is_offline_mode():
        op.execute("-- offline preview: downgrade is no-op in offline mode")
        return

    bind: Connection = op.get_bind()
    inspector = inspect(bind)

    if _has_table(inspector, "workflow_runs"):
        op.drop_index("ix_workflow_runs_status", table_name="workflow_runs")
        op.drop_index("ix_workflow_runs_mission_id", table_name="workflow_runs")
        op.drop_table("workflow_runs")

    if _has_table(inspector, "knowledge") and _has_column(inspector, "knowledge", "summary"):
        op.drop_column("knowledge", "summary")

    if _has_table(inspector, "artifacts"):
        if _has_column(inspector, "artifacts", "tags"):
            op.drop_column("artifacts", "tags")
        if _has_column(inspector, "artifacts", "scope"):
            op.drop_column("artifacts", "scope")

    if _has_table(inspector, "tasks"):
        if _has_index(inspector, "tasks", "ix_tasks_agent_id"):
            op.drop_index("ix_tasks_agent_id", table_name="tasks")
        if _has_index(inspector, "tasks", "ix_tasks_group_id"):
            op.drop_index("ix_tasks_group_id", table_name="tasks")
        if _has_index(inspector, "tasks", "ix_tasks_mission_id"):
            op.drop_index("ix_tasks_mission_id", table_name="tasks")
        if _has_column(inspector, "tasks", "error"):
            op.drop_column("tasks", "error")
        if _has_column(inspector, "tasks", "output"):
            op.drop_column("tasks", "output")
        if _has_column(inspector, "tasks", "input"):
            op.drop_column("tasks", "input")
        if _has_column(inspector, "tasks", "order"):
            op.drop_column("tasks", "order")
        if _has_column(inspector, "tasks", "mission_id"):
            op.drop_column("tasks", "mission_id")
        # テーブル全体を drop する場合は状況に応じてここに追加

    if _has_table(inspector, "task_groups"):
        if _has_index(inspector, "task_groups", "ix_task_groups_order"):
            op.drop_index("ix_task_groups_order", table_name="task_groups")
        if _has_index(inspector, "task_groups", "ix_task_groups_mission_id"):
            op.drop_index("ix_task_groups_mission_id", table_name="task_groups")
        op.drop_table("task_groups")

    if _has_table(inspector, "missions"):
        if _has_index(inspector, "missions", "ix_missions_status"):
            op.drop_index("ix_missions_status", table_name="missions")
        if _has_index(inspector, "missions", "ix_missions_project_id"):
            op.drop_index("ix_missions_project_id", table_name="missions")
        op.drop_table("missions")
