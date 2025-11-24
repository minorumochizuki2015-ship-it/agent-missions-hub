# Repository Guidelines (agent-missions-hub)

## プロジェクト構造とモジュール
- 作業ルート: `C:\Users\User\Trae\ORCH-Next\projects\agent-missions-hub`（クリーン worktree 推奨）。
- サーバー本体: `src\mcp_agent_mail\`（FastMCP/HTTP/CLI/UI・メールボックス機能）。
- テスト: `tests\` 配下で領域別（例: `tests\terminal_hub_api\`）。運用スクリプトは `scripts\`、計画・証跡は `plans\` / `reports\`、監査・メトリクスは `observability\`。
- 規約・運用: `rules\` および `.trae\rules\*.yaml`。ログ/成果物は `data\logs\current\` と `artifacts\` に保存。

## ビルド・テスト・開発コマンド
- 依存解決: `uv sync`
- アプリ起動: `uv run python -m mcp_agent_mail.cli serve-http` または `make serve-http`
- DB 初期化: `make migrate`、guard: `make guard-install PROJECT=<path>` / `make guard-uninstall`
- ヘルスチェック（最小）: `.venv\Scripts\python.exe -m pytest -q`
- フル検証: `uv run pytest`（.coveragerc に従いカバレッジ取得）
- フロント監査: `npm run test:ui` / `npm run ui:audit:ci`（Node 18+）。成果物は `observability\ui\` 配下へ。

## コーディングスタイルと命名
- Python 3.12 + `from __future__ import annotations` 前提。全クラス/関数に日本語 docstring、新規 `Any` 禁止。
- 整形: `black`（120 桁）・`isort`・`ruff` は `.venv` 経由で実行。`Optional` 使用時は `None` ハンドリングを明示。
- 1 ファイル 300 行以内・単一責務。定数は UPPER_SNAKE、型付き dataclass / Enum を優先。

## テスト指針
- Pytest 設定は `pyproject.toml`。`--strict-markers` と asyncio マーカーを遵守。
- カバレッジ目標: statements/branches/functions/lines >= 80%、差分は `diff-cover` Added >= 85%、Changed >= 80%。
- UI 変更時: Playwright スクショ・axe 結果・visual diff を `artifacts\<task_id>\ui\` に保存し、手動検証を `APPROVALS.md` に追記。

## コミットとプルリク
- Conventional Commits（例: `feat(mail): add lease audit`）＋署名＋`Signed-off-by` 必須。ブランチ命名: `feature/*` `hotfix/*` `release/*`。
- PR には `diff-plan.json`、PLAN/Test/Patch 証跡、`APPROVALS.md` 二者承認、CI（black/isort/ruff/mypy/pytest/diff-cover/bandit/sbom/secret_scan/eol_check）結果を添付。
- UI/危険操作は Dry-Run→Apply 手順＋SafeOps ログ＋スクリーンショットを伴い、`observability\dashboard\` 更新と `artifacts\<task_id>\overview.html` 生成を確認。

## セキュリティとエージェント手順
- 変更は Plan-Test-Patch に従い、実行ツールは許可済み（例: `.venv\Scripts\python.exe`）に限定。
- `APPROVALS.md` の二者承認、`data\locks\workflow.lock` 取得、秘密情報の持ち出し禁止を徹底。
- UI 予算 (LCP <= 2.5s, TTI <= 3.0s, CLS <= 0.10, visual diff <= 10%, axe serious+ = 0) を超過した場合は即ロールバックと再検証を行う。
