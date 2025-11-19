from __future__ import annotations

"""FastMCP サーバとツール実装の最小スタブ。"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List

from fastmcp import MCPServer, Tool  # type: ignore


@dataclass(slots=True)
class ProjectRecord:
    slug: str
    title: str
    created_at: float = field(default_factory=time.time)


@dataclass(slots=True)
class AgentRecord:
    id: str
    project_slug: str
    name: str
    program: str
    model: str
    task_description: str
    task_summary: str
    skills: List[str]
    primary_model: str
    created_at: float = field(default_factory=time.time)


@dataclass(slots=True)
class MessageRecord:
    id: str
    project_slug: str
    sender_name: str
    to: List[str]
    subject: str
    body_md: str
    created_at: float = field(default_factory=time.time)


class InMemoryStore:
    """単純なインメモリ永続化。"""

    def __init__(self) -> None:
        self.projects: Dict[str, ProjectRecord] = {}
        self.agents: Dict[str, AgentRecord] = {}
        self.messages: Dict[str, MessageRecord] = {}

    def ensure_project(self, human_key: str) -> ProjectRecord:
        slug = human_key.replace("\\", "/").replace(":", "-")
        if slug not in self.projects:
            self.projects[slug] = ProjectRecord(slug=slug, title=human_key)
        return self.projects[slug]

    def create_agent(self, project_slug: str, payload: Dict[str, Any]) -> AgentRecord:
        agent_id = str(uuid.uuid4())
        record = AgentRecord(
            id=agent_id,
            project_slug=project_slug,
            name=payload.get("name_hint") or payload.get("name") or "agent",
            program=payload.get("program", ""),
            model=payload.get("model", ""),
            task_description=payload.get("task_description", ""),
            task_summary=payload.get("task_summary", ""),
            skills=list(payload.get("skills") or []),
            primary_model=payload.get("primary_model", ""),
        )
        self.agents[agent_id] = record
        return record

    def add_message(self, project_slug: str, payload: Dict[str, Any]) -> MessageRecord:
        msg_id = str(uuid.uuid4())
        record = MessageRecord(
            id=msg_id,
            project_slug=project_slug,
            sender_name=payload.get("sender_name", ""),
            to=list(payload.get("to") or []),
            subject=payload.get("subject", ""),
            body_md=payload.get("body_md", ""),
        )
        self.messages[msg_id] = record
        return record


_store = InMemoryStore()


def build_mcp_server() -> MCPServer:
    """FastMCP サーバとツールを構築する。"""

    server = MCPServer("agent-missions-hub")

    @server.tool()
    def ensure_project(human_key: str) -> Dict[str, str]:
        """プロジェクトを作成または取得する。"""

        project = _store.ensure_project(human_key)
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

        store_project = _store.ensure_project(project_key)
        agent = _store.create_agent(
            project_slug=store_project.slug,
            payload={
                "name_hint": name_hint,
                "program": program,
                "model": model,
                "task_description": task_description or "",
                "task_summary": task_summary or "",
                "skills": skills or [],
                "primary_model": primary_model or model,
            },
        )
        return {
            "id": agent.id,
            "name": agent.name,
            "project_slug": agent.project_slug,
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
        """メッセージ送信（スタブ）。"""

        _store.ensure_project(project_key)
        message = _store.add_message(
            project_slug=project_key,
            payload={
                "sender_name": sender_name,
                "to": to,
                "subject": subject,
                "body_md": body_md,
                "ack_required": ack_required,
            },
        )
        return {"message_id": message.id, "status": "queued", "project_slug": project_key}

    return server
