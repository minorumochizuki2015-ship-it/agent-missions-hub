from __future__ import annotations

"""アプリ全体の設定を管理するモジュール。"""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """環境変数や .env から読み込む設定定義。"""

    app_name: str = Field(default="agent-missions-hub")
    debug: bool = Field(default=False)
    storage_root: str = Field(default="./data")
    database_url: str = Field(default="sqlite:///./data/app.db")
    mcp_mount_path: str = Field(default="/mcp")
    stateless_http: bool = Field(default=True)

    model_config = {
        "env_prefix": "AMH_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


def get_settings() -> Settings:
    """設定のシングルトン取得ヘルパー。"""
    return Settings()
