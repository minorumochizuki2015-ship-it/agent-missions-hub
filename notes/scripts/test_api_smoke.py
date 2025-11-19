#!/usr/bin/env python
"""STEP1_API_SMOKE validation with log suppression."""

import os
import sys
import time
import json
import requests
import subprocess


def main():
    print("=" * 80)
    print("STEP1_API_SMOKE: ensure_project → create_agent_identity → send_message")
    print("=" * 80)

    # Set environment variables with log suppression
    env = os.environ.copy()
    env["STORAGE_ROOT"] = "C:\\tmp\\agent-role-skills-ui-test\\run"
    env["HTTP_RBAC_ENABLED"] = "false"
    env["HTTP_JWT_ENABLED"] = "false"
    env["HTTP_ALLOW_LOCALHOST_UNAUTHENTICATED"] = "true"
    env["LOG_LEVEL"] = "WARNING"  # Suppress INFO logs
    env["TOOLS_LOG_ENABLED"] = "false"  # Disable rich tools logging
    env["LOG_RICH_ENABLED"] = "false"  # Disable rich console output
    env["PYTHONPATH"] = os.path.abspath("src")

    # Start uvicorn server
    port = 8003
    server_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "mcp_agent_mail.http:app",
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

    print(f"\n[SETUP] Starting server on port {port} (logs suppressed)...")

    with open("api_smoke_server.log", "w", encoding="utf-8") as log_file:
        server_proc = subprocess.Popen(server_cmd, env=env, stdout=log_file, stderr=subprocess.STDOUT)

        try:
            # Wait for server startup
            print("[SETUP] Waiting for server startup...")
            time.sleep(10)  # Increased wait time

            # Check health
            try:
                health = requests.get(f"http://127.0.0.1:{port}/health/readiness", timeout=3)
                if health.status_code == 200:
                    print("[SETUP] ✓ Server ready\n")
                else:
                    print(f"[SETUP] ✗ Health check failed: {health.status_code}")
                    return
            except Exception as e:
                print(f"[SETUP] ✗ Server not ready: {e}")
                return

            # Common headers
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            base_url = f"http://127.0.0.1:{port}/mcp"
            project_slug = None
            agent_name = None

            # Test 1: ensure_project
            print("[TEST 1] ensure_project")
            print("-" * 80)
            payload1 = {
                "jsonrpc": "2.0",
                "id": "test-1",
                "method": "tools/call",
                "params": {"name": "ensure_project", "arguments": {"human_key": "C:/tmp/agent-role-skills-ui-test"}},
            }

            start = time.time()
            try:
                resp1 = requests.post(base_url, json=payload1, headers=headers, timeout=10)
                elapsed = (time.time() - start) * 1000

                print(f"Status: {resp1.status_code}")
                print(f"Duration: {elapsed:.0f}ms")

                if resp1.status_code == 200:
                    result1 = resp1.json()
                    project_slug = None
                    if isinstance(result1, dict) and "result" in result1:
                        res1 = result1["result"]
                        project_slug = (
                            res1.get("slug")
                            or res1.get("project_slug")
                            or res1.get("structuredContent", {}).get("slug")
                        )
                    if project_slug:
                        print(f"✓ SUCCESS - project_slug: {project_slug}")
                    else:
                        print(f"✗ ERROR: {json.dumps(result1, indent=2)}")
                        return
                else:
                    print(f"✗ HTTP {resp1.status_code}: {resp1.text}")
                    return
            except Exception as e:
                print(f"✗ FAILED: {e}")
                return

            print()

            # Test 2: create_agent_identity
            print("[TEST 2] create_agent_identity")
            print("-" * 80)

            agent_name = "CodexAssistant"
            payload2 = {
                "jsonrpc": "2.0",
                "id": "test-2",
                "method": "tools/call",
                "params": {
                    "name": "create_agent_identity",
                    "arguments": {
                        "project_key": project_slug,
                        "name_hint": agent_name,
                        "program": "codex-cli",
                        "model": "gpt-5.1-codex-mini",
                        "task_description": "一級市民を支援するテスト用のロールプロンプト（長文）...",
                        "task_summary": "テスト用一級市民エージェント",
                        "skills": ["doc-search", "code-edit"],
                        "primary_model": "gpt-5.1-codex-mini",
                    },
                },
            }

            start = time.time()
            try:
                resp2 = requests.post(base_url, json=payload2, headers=headers, timeout=60)
                elapsed = (time.time() - start) * 1000

                print(f"Status: {resp2.status_code}")
                print(f"Duration: {elapsed:.0f}ms")

                if resp2.status_code == 200:
                    result2 = resp2.json()
                    res_body = result2.get("result", {})
                    structured = res_body.get("structuredContent", {}) if isinstance(res_body, dict) else {}
                    agent_id = res_body.get("id") or structured.get("id")
                    agent_name = res_body.get("name") or structured.get("name") or agent_name
                    if agent_id:
                        print(f"✓ SUCCESS - agent_id: {agent_id} (name: {agent_name})")
                    else:
                        print(f"✗ ERROR: {json.dumps(result2, indent=2)}")
                        return
                else:
                    print(f"✗ HTTP {resp2.status_code}: {resp2.text}")
                    return
            except Exception as e:
                print(f"✗ FAILED: {e}")
                return

            print()

            # Test 3: send_message
            print("[TEST 3] send_message")
            print("-" * 80)

            payload3 = {
                "jsonrpc": "2.0",
                "id": "test-3",
                "method": "tools/call",
                "params": {
                    "name": "send_message",
                    "arguments": {
                        "project_key": project_slug,
                        "sender_name": agent_name,
                        "to": [agent_name],
                        "subject": "API Smoke Test",
                        "body_md": "Testing send_message via HTTP JSON-RPC",
                        "ack_required": False,
                    },
                },
            }

            start = time.time()
            try:
                resp3 = requests.post(base_url, json=payload3, headers=headers, timeout=60)
                elapsed = (time.time() - start) * 1000

                print(f"Status: {resp3.status_code}")
                print(f"Duration: {elapsed:.0f}ms")

                if resp3.status_code == 200:
                    result3 = resp3.json()
                    if "result" in result3:
                        message_id = result3["result"].get("message_id")
                        print(f"✓ SUCCESS - message_id: {message_id}")
                    else:
                        print(f"✗ ERROR: {json.dumps(result3, indent=2)}")
                        return
                else:
                    print(f"✗ HTTP {resp3.status_code}: {resp3.text}")
                    return
            except Exception as e:
                print(f"✗ FAILED: {e}")
                return

            print()
            print("=" * 80)
            print("STEP1_API_SMOKE: ✓ ALL TESTS PASSED")
            print("=" * 80)

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
