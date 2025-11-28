"""Phase 2A ER alignment: add missing indexes/columns for artifacts & knowledge.

Revision ID: f3b0b0c96c12
Revises: 25d1f3a8b32f
Create Date: 2025-11-28 08:16:12.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import context, op
from sqlalchemy import inspect
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision: str = "f3b0b0c96c12"  # pragma: allowlist secret - Alembic revision id
down_revision: Union[str, Sequence[str], None] = "25d1f3a8b32f"  # pragma: allowlist secret
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table: str) -> bool:
    return inspector.has_table(table)


def _has_column(inspector: sa.Inspector, table: str, column: str) -> bool:
    return any(col.get("name") == column for col in inspector.get_columns(table))


def _has_index(inspector: sa.Inspector, table: str, name: str) -> bool:
    return any(idx.get("name") == name for idx in inspector.get_indexes(table))


def upgrade() -> None:
    """Add Phase 2A schema alignments (idempotent, inspection-driven)."""
    if context.is_offline_mode():
        op.execute("-- offline: skip inspection-driven migration")
        return

    bind: Connection = op.get_bind()
    inspector = inspect(bind)

    # artifacts: add indexes for mission/task relations
    if _has_table(inspector, "artifacts"):
        if not _has_index(inspector, "artifacts", "ix_artifacts_mission_id"):
            op.create_index("ix_artifacts_mission_id", "artifacts", ["mission_id"])
        if not _has_index(inspector, "artifacts", "ix_artifacts_task_id"):
            op.create_index("ix_artifacts_task_id", "artifacts", ["task_id"])

    # knowledge: add tags column and indexes for FK columns
    if _has_table(inspector, "knowledge"):
        if not _has_column(inspector, "knowledge", "tags"):
            op.add_column("knowledge", sa.Column("tags", sa.JSON(), nullable=True))
        if not _has_index(inspector, "knowledge", "ix_knowledge_artifact_id"):
            op.create_index("ix_knowledge_artifact_id", "knowledge", ["artifact_id"])
        if not _has_index(inspector, "knowledge", "ix_knowledge_source_artifact_id"):
            op.create_index("ix_knowledge_source_artifact_id", "knowledge", ["source_artifact_id"])


def downgrade() -> None:
    """Remove Phase 2A additions where possible."""
    if context.is_offline_mode():
        op.execute("-- offline: downgrade is no-op")
        return

    bind: Connection = op.get_bind()
    inspector = inspect(bind)

    if _has_table(inspector, "knowledge"):
        if _has_index(inspector, "knowledge", "ix_knowledge_source_artifact_id"):
            op.drop_index("ix_knowledge_source_artifact_id", table_name="knowledge")
        if _has_index(inspector, "knowledge", "ix_knowledge_artifact_id"):
            op.drop_index("ix_knowledge_artifact_id", table_name="knowledge")
        if _has_column(inspector, "knowledge", "tags"):
            op.drop_column("knowledge", "tags")

    if _has_table(inspector, "artifacts"):
        if _has_index(inspector, "artifacts", "ix_artifacts_task_id"):
            op.drop_index("ix_artifacts_task_id", table_name="artifacts")
        if _has_index(inspector, "artifacts", "ix_artifacts_mission_id"):
            op.drop_index("ix_artifacts_mission_id", table_name="artifacts")
