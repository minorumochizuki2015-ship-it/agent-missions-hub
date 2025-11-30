# fmt: off
# ruff: noqa: E701,E702
# isort: skip_file
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from sqlmodel import select
from .db import ensure_schema, get_session
from .models import Agent, FileReservation, Message, Project


class MailClient:
    """メッセージとファイル予約の最小統一ラッパー。"""
    async def _ids(self, project_key: str, agent_name: str | None = None) -> tuple[int, int | None]:
        """プロジェクトIDと任意のエージェントIDを解決する。""" ; await ensure_schema()
        async with get_session() as s:
            pid = (await s.exec(select(Project.id).where((Project.slug == project_key) | (Project.human_key == project_key)))).first()
            if pid is None: raise ValueError("project not found")
            if agent_name is None: return int(pid), None
            aid = (await s.exec(select(Agent.id).where((Agent.project_id == pid) & (Agent.name == agent_name)))).first()
            if aid is None: raise ValueError("agent not found")
            return int(pid), int(aid)

    async def send_message(self, project_key: str, agent_name: str, subject: str, body_md: str) -> Message:
        """指定プロジェクト/エージェントでメッセージを保存する。""" ; pid, sid = await self._ids(project_key, agent_name)
        async with get_session() as s:
            msg = Message(project_id=pid, sender_id=sid, subject=subject, body_md=body_md); s.add(msg); await s.commit(); await s.refresh(msg); return msg

    async def list_messages(self, project_key: str) -> list[Message]:
        """プロジェクト内のメッセージを新しい順に返す。""" ; pid, _ = await self._ids(project_key)
        async with get_session() as s:
            res = await s.exec(select(Message).where(Message.project_id == pid).order_by(Message.created_ts.desc())); return list(res.all())

    async def create_lease(self, project_key: str, agent_name: str, path_pattern: str) -> FileReservation:
        """1時間TTLのファイル予約を作成する。""" ; await ensure_schema(); pid, aid = await self._ids(project_key, agent_name); now = datetime.now(timezone.utc)
        lease = FileReservation(project_id=pid, agent_id=aid, path_pattern=path_pattern, exclusive=True, reason="mail-client", created_ts=now, expires_ts=now + timedelta(hours=1))
        async with get_session() as s:
            s.add(lease); await s.commit(); await s.refresh(lease); return lease

    async def release_lease(self, lease_id: int) -> FileReservation:
        """予約を解放し released_ts を記録する。""" ; await ensure_schema()
        async with get_session() as s:
            res = await s.exec(select(FileReservation).where(FileReservation.id == lease_id)); lease = res.first()
            if lease is None: raise ValueError("lease not found")
            lease.released_ts = datetime.now(timezone.utc); s.add(lease); await s.commit(); await s.refresh(lease); return lease
