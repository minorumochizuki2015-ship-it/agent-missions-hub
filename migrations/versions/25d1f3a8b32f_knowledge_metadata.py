"""Add extra metadata columns to knowledge table.

Revision ID: 25d1f3a8b32f
Revises: 84eef2bb1c4f
Create Date: 2025-11-24 09:20:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import context, op
from sqlalchemy import inspect
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision: str = "25d1f3a8b32f"
down_revision: Union[str, Sequence[str], None] = "84eef2bb1c4f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table: str) -> bool:
    return inspector.has_table(table)


def _has_column(inspector: sa.Inspector, table: str, column: str) -> bool:
    return any(col.get("name") == column for col in inspector.get_columns(table))


def upgrade() -> None:
    """Add knowledge metadata columns for Phase 2A."""
    if context.is_offline_mode():
        op.execute("-- offline: upgrade needs online mode for schema introspection")
        return

    bind: Connection = op.get_bind()
    inspector = inspect(bind)

    if not _has_table(inspector, "knowledge"):
        return

    if not _has_column(inspector, "knowledge", "source_artifact_id"):
        op.add_column(
            "knowledge",
            sa.Column("source_artifact_id", sa.String(length=36), nullable=True),
        )
        op.create_index("ix_knowledge_source_artifact_id", "knowledge", ["source_artifact_id"])

    if not _has_column(inspector, "knowledge", "version"):
        op.add_column("knowledge", sa.Column("version", sa.String(length=64), nullable=True))

    if not _has_column(inspector, "knowledge", "sha256"):
        op.add_column("knowledge", sa.Column("sha256", sa.String(length=64), nullable=True))

    if not _has_column(inspector, "knowledge", "scope"):
        op.add_column("knowledge", sa.Column("scope", sa.String(length=32), nullable=False, server_default="project"))

    if not _has_column(inspector, "knowledge", "created_at"):
        op.add_column(
            "knowledge",
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("(DATETIME('now'))")),
        )

    if not _has_column(inspector, "knowledge", "updated_at"):
        op.add_column(
            "knowledge",
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("(DATETIME('now'))")),
        )


def downgrade() -> None:
    """Remove metadata columns if necessary."""
    if context.is_offline_mode():
        op.execute("-- offline: downgrade is no-op")
        return

    bind: Connection = op.get_bind()
    inspector = inspect(bind)

    if not _has_table(inspector, "knowledge"):
        return

    if _has_column(inspector, "knowledge", "updated_at"):
        op.drop_column("knowledge", "updated_at")

    if _has_column(inspector, "knowledge", "created_at"):
        op.drop_column("knowledge", "created_at")

    if _has_column(inspector, "knowledge", "scope"):
        op.drop_column("knowledge", "scope")

    if _has_column(inspector, "knowledge", "sha256"):
        op.drop_column("knowledge", "sha256")

    if _has_column(inspector, "knowledge", "version"):
        op.drop_column("knowledge", "version")

    if _has_column(inspector, "knowledge", "source_artifact_id"):
        op.drop_index("ix_knowledge_source_artifact_id", table_name="knowledge")
        op.drop_column("knowledge", "source_artifact_id")
