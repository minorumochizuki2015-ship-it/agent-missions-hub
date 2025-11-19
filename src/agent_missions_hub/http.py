from __future__ import annotations

"""FastAPI + FastMCP のエントリーポイント骨子。"""

from fastapi import FastAPI

from .settings import Settings, get_settings


def build_app(settings: Settings | None = None) -> FastAPI:
    """FastAPI アプリを構築する。"""

    app_settings = settings or get_settings()
    app = FastAPI(title=app_settings.app_name, debug=app_settings.debug)

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        """単純なヘルスチェック応答を返す。"""

        return {"status": "ok", "app": app_settings.app_name}

    # FastMCP のマウントは後続で実装予定。
    return app


app = build_app()
