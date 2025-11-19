#!/usr/bin/env python
"""ensure_project → create_agent_identity → send_message のスモークテスト（雛形）。"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from typing import Any

import requests


def _print_section(title: str) -> None:
    print("=" * 80)
    print(title)
    print("=" * 80)


def main() -> None:
    _print_section("STEP1_API_SMOKE: ensure_project → create_agent_identity → send_message")

    env = os.environ.copy()
    env.setdefault("AMH_STORAGE_ROOT", "./data/run")
    env.setdefault("AMH_DEBUG", "false")
    env.setdefault("TOOLS_LOG_ENABLED", "false")
    env.setdefault("LOG_RICH_ENABLED", "false")
    env.setdefault("PYTHONPATH", os.path.abspath("src"))

    port = 8003
    server_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "agent_missions_hub.http:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--factory",
        "--app-dir",
        "src",
        "--log-level",
        "warning",
    ]

    print(f"[SETUP] Starting server on port {port} (logs suppressed)...")
    with open("api_smoke_server.log", "w", encoding="utf-8") as log_file:
        server_proc = subprocess.Popen(server_cmd, env=env, stdout=log_file, stderr=subprocess.STDOUT)

        try:
            print("[SETUP] Waiting for server startup...")
            time.sleep(5)

            base_url = f"http://127.0.0.1:{port}/mcp"
            rest_base = f"http://127.0.0.1:{port}/api"
            health_url = f"http://127.0.0.1:{port}/health"
            headers = {"Content-Type": "application/json", "Accept": "application/json"}

            try:
                health = requests.get(health_url, timeout=3)
                print(f"[SETUP] Health: {health.status_code} {health.text}")
            except Exception as exc:  # pragma: no cover - network issue
                print(f"[SETUP] ✗ Health check failed: {exc}")
                return

            # payload definitions
            payload1: dict[str, Any] = {
                "jsonrpc": "2.0",
                "id": "test-1",
                "method": "tools/call",
                "params": {"name": "ensure_project", "arguments": {"human_key": "C:/tmp/amh-test"}},
            }

            payload2: dict[str, Any] = {
                "jsonrpc": "2.0",
                "id": "test-2",
                "method": "tools/call",
                "params": {
                    "name": "create_agent_identity",
                    "arguments": {
                        "project_key": None,
                        "name_hint": "CodexAssistant",
                        "program": "codex-cli",
                        "model": "gpt-5.1-codex-mini",
                        "task_description": "ロールプロンプト（長文）...",
                        "task_summary": "テスト用エージェント",
                        "skills": ["doc-search", "code-edit"],
                        "primary_model": "gpt-5.1-codex-mini",
                    },
                },
            }

            payload3: dict[str, Any] = {
                "jsonrpc": "2.0",
                "id": "test-3",
                "method": "tools/call",
                "params": {
                    "name": "send_message",
                    "arguments": {
                        "project_key": None,
                        "sender_name": "CodexAssistant",
                        "to": ["CodexAssistant"],
                        "subject": "API Smoke Test",
                        "body_md": "Testing send_message via HTTP JSON-RPC",
                        "ack_required": False,
                    },
                },
            }

            # Test 1
            print("[TEST 1] ensure_project")
            start = time.time()
            resp1 = requests.post(base_url, json=payload1, headers=headers, timeout=10)
            elapsed1 = (time.time() - start) * 1000
            print(f"Status: {resp1.status_code}  Duration: {elapsed1:.0f}ms")
            body1 = resp1.json() if resp1.headers.get("content-type","" ).startswith("application/json") else resp1.text
            print(json.dumps(body1, ensure_ascii=False, indent=2))

            # patch project_key for following calls if available
            project_key = None
            if isinstance(body1, dict):
                result1 = body1.get("result", {}) if isinstance(body1.get("result"), dict) else body1.get("result")
                if isinstance(result1, dict):
                    project_key = result1.get("slug") or result1.get("project_slug")

            payload2["params"]["arguments"]["project_key"] = project_key
            payload3["params"]["arguments"]["project_key"] = project_key

            # Test 2
            print("\n[TEST 2] create_agent_identity")
            start = time.time()
            resp2 = requests.post(base_url, json=payload2, headers=headers, timeout=30)
            elapsed2 = (time.time() - start) * 1000
            print(f"Status: {resp2.status_code}  Duration: {elapsed2:.0f}ms")
            body2 = resp2.json() if resp2.headers.get("content-type","" ).startswith("application/json") else resp2.text
            print(json.dumps(body2, ensure_ascii=False, indent=2))

            agent_name = "CodexAssistant"
            if isinstance(body2, dict):
                result2 = body2.get("result")
                if isinstance(result2, dict):
                    agent_name = result2.get("name") or agent_name
                    payload3["params"]["arguments"]["to"] = [agent_name]
                    payload3["params"]["arguments"]["sender_name"] = agent_name

            # Test 3
            print("\n[TEST 3] send_message")
            start = time.time()
            resp3 = requests.post(base_url, json=payload3, headers=headers, timeout=30)
            elapsed3 = (time.time() - start) * 1000
            print(f"Status: {resp3.status_code}  Duration: {elapsed3:.0f}ms")
            body3 = resp3.json() if resp3.headers.get("content-type","" ).startswith("application/json") else resp3.text
            print(json.dumps(body3, ensure_ascii=False, indent=2))

            # Test 4 - REST mission CRUD
            if not project_key:
                project_key = "C:/tmp/amh-test"
            mission_payload = {
                "project_slug": project_key,
                "title": "smoke-mission",
                "summary": "smoke mission auto created",
                "status": "draft",
            }
            print("\n[TEST 4] REST missions")
            resp4 = requests.post(f"{rest_base}/missions", json=mission_payload, timeout=10)
            print(f"POST /missions Status: {resp4.status_code}")
            print(resp4.text)
            resp4_list = requests.get(f"{rest_base}/missions", timeout=10)
            print(f"GET /missions Status: {resp4_list.status_code}")
            print(resp4_list.text)

        finally:
            print("\n[CLEANUP] Stopping server...")
            server_proc.terminate()
            try:
                server_proc.wait(timeout=5)
                print("[CLEANUP] ✓ Server stopped")
            except subprocess.TimeoutExpired:
                server_proc.kill()
                print("[CLEANUP] ! Force killed")


if __name__ == "__main__":
    main()
