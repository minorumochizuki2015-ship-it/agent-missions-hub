from __future__ import annotations

"""FastMCP サーバと DB バックエンドの最小実装。"""

from typing import Any, Dict, List

from fastmcp import MCPServer  # type: ignore
from sqlmodel import select

from .db import Agent, Message, Project, get_session, init_db
from .settings import Settings


def _ensure_schema(settings: Settings) -> None:
    """起動時にスキーマを作成する。"""

    init_db(settings.database_url)


def build_mcp_server(settings: Settings) -> MCPServer:
    """FastMCP サーバとツールを構築する。"""

    _ensure_schema(settings)
    server = MCPServer("agent-missions-hub")

    @server.tool()
    def ensure_project(human_key: str) -> Dict[str, str]:
        """プロジェクトを作成または取得する。"""

        slug = human_key.replace("\\", "/").replace(":", "-")
        with get_session(settings.database_url) as session:
            project = session.exec(select(Project).where(Project.slug == slug)).first()
            if project is None:
                project = Project(slug=slug, title=human_key)
                session.add(project)
                session.commit()
                session.refresh(project)
        return {"slug": project.slug, "title": project.title}

    @server.tool()
    def create_agent_identity(
        project_key: str,
        name_hint: str,
        program: str,
        model: str,
        task_description: str | None = None,
        task_summary: str | None = None,
        skills: List[str] | None = None,
        primary_model: str | None = None,
    ) -> Dict[str, Any]:
        """エージェントを作成する。"""

        slug = project_key
        with get_session(settings.database_url) as session:
            project = session.exec(select(Project).where(Project.slug == slug)).first()
            if project is None:
                project = Project(slug=slug, title=slug)
                session.add(project)
                session.commit()
                session.refresh(project)

            agent = Agent(
                project_id=project.id,
                name=name_hint or "agent",
                program=program,
                model=model,
                task_description=task_description or "",
                task_summary=task_summary or "",
                skills=skills or [],
                primary_model=primary_model or model,
            )
            session.add(agent)
            session.commit()
            session.refresh(agent)
        return {
            "id": agent.id,
            "name": agent.name,
            "project_slug": project.slug,
            "skills": agent.skills,
            "primary_model": agent.primary_model,
        }

    @server.tool()
    def send_message(
        project_key: str,
        sender_name: str,
        to: List[str],
        subject: str,
        body_md: str,
        ack_required: bool = False,
    ) -> Dict[str, Any]:
        """メッセージ送信（簡易 DB バックエンド）。"""

        slug = project_key
        with get_session(settings.database_url) as session:
            project = session.exec(select(Project).where(Project.slug == slug)).first()
            if project is None:
                project = Project(slug=slug, title=slug)
                session.add(project)
                session.commit()
                session.refresh(project)

            message = Message(
                project_id=project.id,
                sender_name=sender_name,
                to=to,
                subject=subject,
                body_md=body_md,
            )
            session.add(message)
            session.commit()
            session.refresh(message)

        return {"message_id": message.id, "status": "queued", "project_slug": slug}

    return server
