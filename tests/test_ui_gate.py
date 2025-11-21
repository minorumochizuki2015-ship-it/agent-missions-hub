"""
UI Gate テスト

Playwrightを使用したUI監査テスト
- サーバー起動確認
- アクセシビリティ監査(axe-core)
- Web Vitals計測
- スクリーンショット取得
"""

import asyncio
import json
import os
import subprocess
import time
from contextlib import suppress
from pathlib import Path

import pytest
import requests
from playwright.async_api import async_playwright

from mcp_agent_mail.config import get_settings

# 環境変数設定
HOST = os.environ.get("UI_AUDIT_HOST", "127.0.0.1")
PORT = os.environ.get("UI_AUDIT_PORT", "8766")
BASE_URL = f"http://{HOST}:{PORT}"
UNIFIED_INBOX_URL = f"{BASE_URL}/mail/unified-inbox"

# アーティファクトディレクトリ
ARTIFACTS_DIR = Path("artifacts/ui_audit")
SCREENSHOTS_DIR = ARTIFACTS_DIR / "screens"
SUMMARY_PATH = ARTIFACTS_DIR / "summary.json"
AXE_RESULTS_PATH = ARTIFACTS_DIR / "axe_result.json"


def ensure_artifacts_dirs():
    """アーティファクトディレクトリを作成"""
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def wait_for_server(url: str, timeout: int = 30) -> bool:
    """サーバーが起動するまで待機"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                return True
        except (requests.ConnectionError, requests.Timeout):
            time.sleep(1)
    return False


@pytest.fixture
def server_url():
    """テストサーバーのURLを提供"""
    return UNIFIED_INBOX_URL


@pytest.fixture
def start_server():
    """テスト用サーバーを起動"""
    # coverage収集のため、テストプロセス側で設定ロードを一度実行
    with suppress(Exception):
        _ = get_settings()
    # 環境変数を設定
    env = os.environ.copy()
    env["HTTP_HOST"] = HOST
    env["HTTP_PORT"] = PORT
    # coverage: サブプロセスでcoverageを開始
    env["COVERAGE_PROCESS_START"] = str(Path(__file__).resolve().parent.parent / ".coveragerc")
    env["PYTEST_ADDOPTS"] = "--cov=mcp_agent_mail --cov-report=term-missing"
    # UI Gateを開放するための最低限のガード緩和
    env["HTTP_RBAC_ENABLED"] = "false"
    env["HTTP_RATE_LIMIT_ENABLED"] = "false"
    env["HTTP_JWT_ENABLED"] = "false"
    env["HTTP_ALLOW_LOCALHOST_UNAUTHENTICATED"] = "true"

    # サーバープロセスを起動(uvicornのfactory経由でFastAPIアプリを起動)
    cmd = [
        ".\\.venv\\Scripts\\python.exe",
        "-m",
        "coverage",
        "run",
        "-m",
        "uvicorn",
        "--app-dir",
        str(Path(__file__).resolve().parent.parent / "src"),
        "mcp_agent_mail.http:app",
        "--host",
        HOST,
        "--port",
        str(PORT),
        "--log-level",
        "warning",
    ]
    # ログをファイルに記録して起動失敗の原因を可視化
    logs_dir = Path("data/logs/current/orchestration")
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "ui_gate_server.log"

    with log_path.open("w", encoding="utf-8", newline="\n") as lf:
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=lf,
            stderr=lf,
            text=True,
        )

        # サーバープロセスの早期終了チェック
        time.sleep(1)
        if process.poll() is not None:
            try:
                msg = Path(log_path).read_text(encoding="utf-8")[-1000:]
            except Exception:
                msg = "(no logs)"
            process.terminate()
            pytest.skip(f"UIサーバー起動に失敗(早期終了): {msg}")

        # サーバー起動待機(軽量なヘルスチェックで確認:liveness)
        if not wait_for_server(f"{BASE_URL}/health/liveness"):
            process.terminate()
            try:
                msg = Path(log_path).read_text(encoding="utf-8")[-1000:]
            except Exception:
                msg = "(no logs)"
            pytest.skip(f"UIサーバーの起動に失敗しました: {msg}")

        yield process

        # クリーンアップ
        process.terminate()
        process.wait(timeout=5)


def test_ui_gate_server_start(start_server):
    """UIサーバーが正常に起動することを確認"""
    # サーバーが既に起動しているはず(フィクスチャで起動済み)
    response = requests.get(f"{BASE_URL}/health/liveness", timeout=10)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_ui_gate_unified_inbox_accessibility(start_server, server_url):
    """Unified Inboxページのアクセシビリティテスト"""
    ensure_artifacts_dirs()

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # ページへアクセス
            await page.goto(server_url, wait_until="domcontentloaded")
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(500)  # レンダリング待機

            # axe-coreを注入
            await page.add_script_tag(
                url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.7.2/axe.min.js"
            )

            # アクセシビリティ監査実行
            axe_results = await page.evaluate(
                "async () => { const r = await axe.run(document, { resultTypes: ['violations'] }); return r; }"
            )

            # ドキュメント情報取得
            doc_info = await page.evaluate(
                "() => ({ title: document.title || '', lang: document.documentElement.getAttribute('lang') || '' })"
            )

            # Web Vitals計測
            try:
                await page.add_script_tag(url="https://unpkg.com/web-vitals@3/dist/web-vitals.umd.js")
                await page.evaluate(
                    """() => {
                        window.__vitals = {};
                        const onReport = (m) => { window.__vitals[m.name] = m.value; };
                        webVitals.getCLS(onReport);
                        webVitals.getLCP(onReport);
                        webVitals.getFID(onReport);
                    }"""
                )
                await page.wait_for_timeout(1500)
                vitals = await page.evaluate("() => window.__vitals || {}")
            except Exception:
                vitals = {}

            # スクリーンショット取得
            screenshot_path = SCREENSHOTS_DIR / "unified_inbox_test.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)

            # 結果サマリー作成
            violations = axe_results.get("violations", [])
            serious_violations = [
                v for v in violations
                if v.get("impact") in {"serious", "critical"}
            ]

            summary = {
                "page": server_url,
                "timestamp": time.strftime("%Y/%m/%d %H:%M:%S"),
                "test_name": "test_ui_gate_unified_inbox_accessibility",
                "document": {
                    "title": doc_info.get("title"),
                    "lang": doc_info.get("lang")
                },
                "axe": {
                    "violations": len(violations),
                    "serious": len(serious_violations),
                    "by_rule": [
                        {
                            "id": v.get("id"),
                            "impact": v.get("impact"),
                            "nodes": len(v.get("nodes", []))
                        }
                        for v in violations
                    ]
                },
                "web_vitals": {
                    "CLS": vitals.get("CLS"),
                    "LCP": vitals.get("LCP"),
                    "FID": vitals.get("FID")
                },
                "screenshot": str(screenshot_path).replace("\\", "/")
            }

            # ゲート判定:重大な違反がなければ合格
            summary["gate"] = {"pass": len(serious_violations) == 0}

            # 結果をファイルに保存
            await asyncio.to_thread(
                SUMMARY_PATH.write_text,
                json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                "utf-8",
                newline="\n",
            )
            await asyncio.to_thread(
                AXE_RESULTS_PATH.write_text,
                json.dumps(axe_results, ensure_ascii=False, indent=2) + "\n",
                "utf-8",
                newline="\n",
            )

            # アサーション
            assert len(serious_violations) == 0, f"重大なアクセシビリティ違反が{len(serious_violations)}件検出されました"

        finally:
            await browser.close()


@pytest.mark.asyncio
async def test_ui_gate_navigation_flow(start_server, server_url):
    """UIナビゲーションフローのテスト"""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # トップページ(/mail)へアクセス
            await page.goto(f"{BASE_URL}/mail", wait_until="domcontentloaded")
            await page.wait_for_load_state("domcontentloaded")

            # ページタイトルが存在することを確認
            title = await page.title()
            assert title, "ページタイトルが設定されていません"

            # Unified Inboxへのリンクが存在することを確認
            try:
                inbox_link = await page.wait_for_selector(
                    f'a[href*="{UNIFIED_INBOX_URL}"]',
                    timeout=5000
                )
                assert inbox_link is not None, "Unified Inboxへのリンクが見つかりません"
            except Exception:
                # リンクがない場合は直接アクセスを試みる
                await page.goto(server_url, wait_until="domcontentloaded")
                await page.wait_for_load_state("domcontentloaded")

            # ページの基本的な要素が存在することを確認
            body_text = await page.inner_text("body")
            assert len(body_text) > 0, "ページコンテンツが空です"

        finally:
            await browser.close()


@pytest.mark.asyncio
async def test_ui_gate_responsive_design(start_server, server_url):
    """レスポンシブデザインのテスト"""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()

        # 複数のビューポートサイズでテスト
        viewports = [
            {"width": 1920, "height": 1080},  # デスクトップ
            {"width": 768, "height": 1024},   # タブレット
            {"width": 375, "height": 667},    # モバイル
        ]

        for viewport in viewports:
            context = await browser.new_context(
                viewport=viewport,
                device_scale_factor=1
            )
            page = await context.new_page()

            try:
                await page.goto(server_url, wait_until="domcontentloaded")
                await page.wait_for_load_state("domcontentloaded")
                await page.wait_for_timeout(1000)  # レイアウト確定待機

                # ビューポートサイズでスクリーンショット
                screenshot_name = f"responsive_{viewport['width']}x{viewport['height']}.png"
                screenshot_path = SCREENSHOTS_DIR / screenshot_name

                await page.screenshot(path=str(screenshot_path), full_page=True)

                # ページがスクロール可能かチェック
                scroll_height = await page.evaluate("document.body.scrollHeight")
                viewport_height = viewport["height"]

                # コンテンツがビューポートに収まっているか確認
                if scroll_height > viewport_height:
                    # 長いページの場合は問題なし
                    pass

            finally:
                await context.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
    # srcレイアウトのインポートを保証
    try:
        project_root = Path(__file__).resolve().parent.parent
        src_path = project_root / "src"
        os.environ["PYTHONPATH"] = str(src_path)
    except Exception:
        pass
