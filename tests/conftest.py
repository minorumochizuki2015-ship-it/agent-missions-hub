import asyncio
import contextlib
import os
import shutil
import tempfile
from pathlib import Path

import anyio
import pytest

"""pytest 共通設定(Windows PermissionError 対策)"""

# グローバルに TMP/TEMP をローカル配下に固定(セッション開始前に有効化)
_PYTEST_BASE = Path.cwd() / ".pytest_tmp"
with contextlib.suppress(Exception):
    _PYTEST_BASE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("TMP", str(_PYTEST_BASE))
os.environ.setdefault("TEMP", str(_PYTEST_BASE))
tempfile.tempdir = str(_PYTEST_BASE)

with contextlib.suppress(Exception):
    if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):  # type: ignore[attr-defined]
        asyncio.set_event_loop_policy(
            asyncio.WindowsSelectorEventLoopPolicy()
        )  # pragma: no cover

try:
    from mcp_agent_mail.config import clear_settings_cache  # type: ignore[import]
except ModuleNotFoundError:

    def clear_settings_cache() -> None:
        pass


try:
    from mcp_agent_mail.db import reset_database_state  # type: ignore[import]
except ModuleNotFoundError:

    def reset_database_state() -> None:
        pass


try:
    from mcp_agent_mail.storage import close_all_archives  # type: ignore[import]
except ModuleNotFoundError:

    def close_all_archives() -> None:
        pass


@pytest.fixture
def isolated_env(tmp_path, monkeypatch):
    """Provide isolated database settings for tests and reset caches."""
    db_path: Path = tmp_path / "test.sqlite3"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("HTTP_HOST", "127.0.0.1")
    monkeypatch.setenv("HTTP_PORT", "8765")
    monkeypatch.setenv("HTTP_PATH", "/mcp/")
    monkeypatch.setenv("APP_ENVIRONMENT", "test")
    storage_root = tmp_path / "storage"
    storage_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("STORAGE_ROOT", str(storage_root))
    monkeypatch.setenv("GIT_AUTHOR_NAME", "test-agent")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "test@example.com")
    monkeypatch.setenv("INLINE_IMAGE_MAX_BYTES", "128")
    monkeypatch.setenv("LLM_ENABLED", "false")
    monkeypatch.setenv("LLM_DEFAULT_MODEL", "stub-model")
    monkeypatch.setenv("LLM_TEMPERATURE", "0")
    monkeypatch.setenv("LLM_MAX_TOKENS", "0")
    try:
        import litellm  # type: ignore[import]

        monkeypatch.setattr(
            litellm,
            "completion",
            lambda *args, **kwargs: {"choices": [{"message": {"content": ""}}]},
            raising=False,
        )
        monkeypatch.setattr(litellm, "success_callback", [], raising=False)
    except Exception:
        # litellm またはその依存関係が未整備/不整合でもテストを続行する
        pass
    clear_settings_cache()
    reset_database_state()
    try:
        yield
    finally:
        clear_settings_cache()
        reset_database_state()
        # Ensure any open Git repos and archive locks are released before cleanup
        close_all_archives()

        async def _remove_with_retry(target: Path) -> None:
            for attempt in range(30):
                try:
                    await asyncio.to_thread(target.unlink)
                    return
                except FileNotFoundError:
                    return
                except PermissionError:
                    await anyio.sleep(min(0.05 * (1 + attempt // 5), 0.2))
            # 最終フォールバック: リネームでハンドル解放を誘発し、次回に削除
            with contextlib.suppress(Exception):
                await asyncio.to_thread(
                    target.rename, target.with_suffix(target.suffix + ".stale")
                )

        async def _cleanup() -> None:
            # DB ファイルの削除
            if db_path.exists():
                await _remove_with_retry(db_path)
            # ストレージ内のアーカイブロックとメタデータを先行解除
            if storage_root.exists():
                for lock_path in storage_root.rglob("*.lock"):
                    await _remove_with_retry(lock_path)
                    meta = lock_path.parent / f"{lock_path.name}.owner.json"
                    if meta.exists():
                        await _remove_with_retry(meta)

                # rmtree は使用中ファイルで停止しがちなので onerror で継続しつつ、
                # 失敗時は個別削除にフォールバック
                def _onerror(func, path, exc_info):
                    # Windows の使用中ファイルに対しては継続(後段で個別削除)
                    return

                try:
                    await asyncio.to_thread(
                        shutil.rmtree,
                        storage_root,
                        ignore_errors=False,
                        onerror=_onerror,
                    )
                except Exception:
                    # 個別削除フォールバック
                    for p in sorted(
                        storage_root.rglob("*"),
                        key=lambda x: len(x.parts),
                        reverse=True,
                    ):
                        try:
                            if p.is_file():
                                await _remove_with_retry(p)
                            else:
                                await asyncio.to_thread(p.rmdir)
                        except Exception:
                            pass
                # まだ残っていれば最終削除試行
                if storage_root.exists():
                    with anyio.move_on_after(5):
                        await asyncio.to_thread(storage_root.rmdir)

    with contextlib.suppress(Exception):
        asyncio.run(asyncio.wait_for(_cleanup(), timeout=10))


def pytest_configure(config: pytest.Config) -> None:
    """Early configuration to force local TMP/TEMP and basetemp.

    This runs before tests start and helps avoid Windows-specific PermissionError
    under system temp paths (e.g., R:\\Temp)."""
    base = Path.cwd() / ".pytest_tmp"
    with contextlib.suppress(Exception):
        base.mkdir(parents=True, exist_ok=True)
    os.environ["TMP"] = str(base)
    os.environ["TEMP"] = str(base)
    # Best-effort: configure internal tmp_path factory when available
    factory = getattr(config, "_tmp_path_factory", None)
    if factory is not None:
        with contextlib.suppress(Exception):
            factory.set_basetemp(base)


@pytest.fixture(autouse=True, scope="session")
def _force_local_tmp_and_basetemp(tmp_path_factory):
    """Windows 環境での PermissionError 回避のため、
    テストセッション全体で TMP/TEMP と basetemp をローカル配下に固定する。
    """
    base = Path.cwd() / ".pytest_tmp"
    base.mkdir(parents=True, exist_ok=True)
    os.environ["TMP"] = str(base)
    os.environ["TEMP"] = str(base)
    with contextlib.suppress(Exception):
        # pytest>=7 で有効。失敗してもテスト継続可能。
        tmp_path_factory.set_basetemp(base)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """セッション終了時にアーカイブと Git リソースを明示的にクローズ。"""
    with contextlib.suppress(Exception):
        close_all_archives()


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    try:
        full = os.environ.get("ENABLE_FULL_SUITE", "0") == "1"
        if full:
            return

        def _split_env(value: str | None) -> tuple[str, ...]:
            if not value:
                return ()
            return tuple(
                part.strip().lower() for part in value.split(",") if part.strip()
            )

        base_allow = (
            "tests/test_workflow_engine.py",
            "tests/test_http_liveness_min.py",
            "tests/test_integration_showcase_unit.py",
            "tests/test_ci_smoke_min.py",
            "tests/test_cli.py::test_cli_help",
            "tests/test_config_unit_min.py",
            "tests/test_models_unit_min.py",
            "tests/test_storage_write_unit_min.py",
            "tests/test_utils_unit_min.py",
        )
        allow_env = os.environ.get("TEST_ALLOWLIST") or os.environ.get(
            "WINDOWS_TEST_ALLOWLIST"
        )
        allow_append = _split_env(
            os.environ.get("TEST_ALLOWLIST_APPEND")
            or os.environ.get("WINDOWS_TEST_ALLOWLIST_APPEND")
        )
        if allow_env:
            allow_targets = tuple(
                t.strip().lower() for t in allow_env.split(",") if t.strip()
            )
        else:
            allow_targets = base_allow + allow_append

        base_deny = (
            "ack_views",
            "ack-",
            "attachment",
            "macro",
            "http_",  # http_* 系を丸ごと除外(通信・レート制限・認可で重い)
            "safeops",
            "kpi_smoke",
            "resources_mailbox",
            "tooling_and_views_resources",
            "tooling_resources",
            "ui_gate",
            "ui_breadcrumb",
            "messaging_semantics",
            "db_basic",
            "db_migrations",
            "mailbox_with_commits",
            "storage_async_file_lock",
            "storage_lock",
        )
        deny_targets = base_deny + _split_env(
            os.environ.get("TEST_DENYLIST") or os.environ.get("WINDOWS_TEST_DENYLIST")
        )

        skip_default = pytest.mark.skip(
            reason="short suite 実行中のため allowlist 以外を skip"
        )
        skip_deny = pytest.mark.skip(
            reason="short suite denylist 対象(IO lock 等不安定領域)"
        )

        def _matches(targets: tuple[str, ...], node_id: str) -> bool:
            return any(target and target in node_id for target in targets)

        for item in items:
            nid = getattr(item, "nodeid", "").lower()
            if _matches(allow_targets, nid):
                if _matches(deny_targets, nid):
                    item.add_marker(skip_deny)
                continue
            item.add_marker(skip_default)
    except Exception:
        pass
