from __future__ import annotations

"""FastAPI + FastMCP のエントリーポイント骨子。"""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from .settings import Settings, get_settings
from .mcp import build_mcp_server

try:
    # fastmcp は依存に含まれるため、そのまま利用する
    from fastmcp import Server as FastMCPServer  # type: ignore
except Exception:  # pragma: no cover - import guard
    FastMCPServer = None


def build_app(settings: Settings | None = None) -> FastAPI:
    """FastAPI アプリを構築する。"""

    app_settings = settings or get_settings()
    app = FastAPI(title=app_settings.app_name, debug=app_settings.debug)

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        """単純なヘルスチェック応答を返す。"""

        return {"status": "ok", "app": app_settings.app_name}

    # FastMCP ネイティブマウント
    if FastMCPServer is not None:
        # ツールを組み込んだサーバを構築
        server = build_mcp_server(app_settings)

        mcp_app = server.http_app(
            path="/",
            stateless_http=app_settings.stateless_http,
            json_response=True,
        )

        mount_base = app_settings.mcp_mount_path or "/mcp"
        if not mount_base.startswith("/"):
            mount_base = f"/{mount_base}"

        @asynccontextmanager
        async def lifespan_context(_: FastAPI):
            # FastMCP 側の lifespan を確実に起動する
            if hasattr(mcp_app, "lifespan"):
                async with mcp_app.lifespan(mcp_app):  # type: ignore[attr-defined]
                    yield
            else:  # pragma: no cover - fallback
                yield

        app.router.lifespan_context = lifespan_context
        app.mount(mount_base, mcp_app)
    else:
        @app.get("/mcp", include_in_schema=False)
        async def mcp_unavailable() -> dict[str, str]:
            """fastmcp 未導入時の簡易応答。"""

            return {"detail": "fastmcp not available"}

    return app


app = build_app()
