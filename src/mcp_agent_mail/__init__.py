"""Top-level package for the MCP Agent Mail server."""

from __future__ import annotations

import asyncio
import inspect

# Python 3.14 warns when third-party code calls asyncio.iscoroutinefunction.
# Patch it globally to the inspect implementation before importing submodules.
asyncio.iscoroutinefunction = inspect.iscoroutinefunction  # type: ignore[attr-defined]

def build_mcp_server():
    from .app import build_mcp_server as _build_mcp_server
    return _build_mcp_server()

__all__ = ["build_mcp_server"]
