"""Application factory placeholder for HTTP import compatibility."""

from __future__ import annotations

from fastapi import FastAPI


def app() -> FastAPI:
    """Return a minimal FastAPI instance.

    http.py が `from .app import app` を行うための互換スタブ。
    必要に応じて実装を拡張する。
    """

    return FastAPI(title="mcp_agent_mail")

