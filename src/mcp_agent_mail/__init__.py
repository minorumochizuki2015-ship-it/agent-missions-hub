"""Top-level package for the MCP Agent Mail server."""

from __future__ import annotations

def build_mcp_server() -> object:
    from .app import build_mcp_server as _build_mcp_server

    return _build_mcp_server()


__all__ = ["build_mcp_server"]
