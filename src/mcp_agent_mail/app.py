"""Application factory and MCP server stubs used by HTTP transportとテスト用 FastAPI."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel


class _ArtifactPayload(BaseModel):
    """アーティファクト作成用の簡易ペイロード."""

    mission_id: UUID
    type: str
    path: str
    version: str
    sha256: str


async def _expire_stale_file_reservations(project_id: int | None) -> None:
    """ファイル予約の期限切れクリーンアップ（スタブ・効果なし）。"""
    return None


def _tool_metrics_snapshot() -> dict[str, Any]:
    """ツール利用メトリクスのスナップショット（スタブ）。"""
    return {}


async def get_project_sibling_data() -> dict[str, Any]:
    """プロジェクト間の関連情報を返すスタブ。"""
    return {}


async def refresh_project_sibling_suggestions() -> None:
    """プロジェクト関連候補を更新するスタブ。"""
    return None


async def update_project_sibling_status(
    project_id: int, other_id: int, target_status: str
) -> dict[str, Any]:
    """プロジェクト関連ステータスを更新するスタブ。"""
    return {"project_id": project_id, "other_id": other_id, "status": target_status}


class _DummyMcpServer:
    """HTTP 用 MCP サーバースタブ。"""

    def http_app(self, *args: object, **kwargs: object) -> FastAPI:
        """stateless MCP HTTP サブアプリのスタブを返す。"""
        mcp_app = FastAPI(title="mcp_agent_mail_mcp_stub")

        @mcp_app.get("/")
        async def _root() -> dict[str, str]:
            return {"status": "ok"}

        return mcp_app


def build_mcp_server() -> _DummyMcpServer:
    """HTTP トランスポートが期待する MCP サーバースタブを構築する。"""
    return _DummyMcpServer()


def app() -> FastAPI:
    """簡易な FastAPI アプリケーションを返す。

    - /health/liveness: ヘルスチェック
    - /missions/{id}: 未存在ミッションを 404 として返す
    - /artifacts: バリデーションにより 422 を返す（不足項目）
    - /artifacts/{id}/promote: 未存在で 404（または UUID 変換失敗で 422）
    """
    fastapi_app = FastAPI(title="mcp_agent_mail")

    @fastapi_app.get("/health/liveness")
    async def liveness() -> dict[str, str]:
        return {"status": "alive"}

    @fastapi_app.get("/missions/{mission_id}")
    async def get_mission(mission_id: str) -> None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="MISSION_NOT_FOUND"
        )

    @fastapi_app.post("/artifacts")
    async def create_artifact(payload: _ArtifactPayload) -> None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="MISSION_NOT_FOUND"
        )

    @fastapi_app.post("/artifacts/{artifact_id}/promote")
    async def promote_artifact(artifact_id: UUID) -> None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="ARTIFACT_NOT_FOUND"
        )

    return fastapi_app
