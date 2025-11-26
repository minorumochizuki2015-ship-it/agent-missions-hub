"""HTTP トランスポート向けの MCP サーバースタブと FastAPI テストアプリ。"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel


class _ArtifactPayload(BaseModel):
    """アーティファクト作成用のペイロード。"""

    mission_id: UUID
    type: str
    path: str
    version: str
    sha256: str


def _tool_metrics_snapshot() -> dict[str, Any]:
    """ツールメトリクスのダミースナップショット。"""

    return {}


async def get_project_sibling_data() -> dict[str, Any]:
    """プロジェクト関連データを返すダミー。"""

    return {}


async def refresh_project_sibling_suggestions() -> None:
    """プロジェクト関連提案を更新するダミー。"""

    return None


async def update_project_sibling_status(
    project_id: int, other_id: int, target_status: str
) -> dict[str, Any]:
    """プロジェクト関連ステータスを返すダミー。"""

    return {"project_id": project_id, "other_id": other_id, "status": target_status}


class _DummyMcpServer:
    """HTTP 向け MCP サーバースタブ。"""

    def http_app(self, *args: object, **kwargs: object) -> FastAPI:
        """stateless な MCP HTTP サブアプリを返す。"""

        mcp_app = FastAPI(title="mcp_agent_mail_mcp_stub")

        @mcp_app.get("/")
        async def _root() -> dict[str, str]:
            return {"status": "ok"}

        return mcp_app


def build_mcp_server() -> _DummyMcpServer:
    """MCP サーバースタブを生成する。"""

    return _DummyMcpServer()


def app() -> FastAPI:
    """簡易 FastAPI アプリを返す。

    - /health/liveness: ヘルスチェック
    - /missions/{id}: 存在しないミッションとして 404 を返す
    - /artifacts: バリデーションエラーで 422 を返す
    - /artifacts/{id}/promote: 存在しない場合は 404、UUID 変換失敗時は 422 を返す
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
