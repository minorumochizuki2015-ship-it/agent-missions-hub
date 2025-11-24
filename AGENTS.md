# Repository Guidelines

## プロジェクト構造とモジュール
- ルート `C:\Users\User\Trae\Codex-CLImutipule-CMD` が全作業の基準であり、配下パスはこのディレクトリからの完全パスを使用します。
- `C:\Users\User\Trae\Codex-CLImutipule-CMD\src\mcp_agent_mail\` が FastMCP サーバー本体で、HTTP/CLI/UI レイヤーとメールボックス機能を提供します。
- `C:\Users\User\Trae\Codex-CLImutipule-CMD\tests\` は transport・guard・UI など機能別に整理され、`...\tests\terminal_hub_api\` など領域単位で検証できます。
- `C:\Users\User\Trae\Codex-CLImutipule-CMD\scripts\` には guard 導入や UI 監査の運用スクリプト、`...\plans\` と `...\reports\` には Plan-Test-Patch 証跡が集約されます。
- `C:\Users\User\Trae\Codex-CLImutipule-CMD\.trae\rules\*.yaml` が運用規約、`...\data\logs\current\` と `...\artifacts\` が CI と監査ログの保存先です。

## ビルド・テスト・開発コマンド
- 依存解決は `uv sync`、アプリ起動は `uv run python -m mcp_agent_mail.cli serve-http` または `make serve-http` を実行します。
- データベース初期化は `make migrate`、guard 操作は `make guard-install PROJECT=<path>`／`make guard-uninstall` を使用します。
- 最低限のヘルスチェックは `C:\Users\User\Trae\Codex-CLImutipule-CMD\.venv\Scripts\python.exe -m pytest -q`、完全検証は `uv run pytest` で `.coveragerc` 設定のカバレッジとレポートを取得します。
- フロントエンド監査は `npm run test:ui` や `npm run ui:audit:ci` (Node 18+) を使い、生成物を `C:\Users\User\Trae\Codex-CLImutipule-CMD\observability\ui\` 配下へ保存します。

## コーディングスタイルと命名
- Python 3.12 と `from __future__ import annotations` を前提に、全クラス・関数へ日本語 docstring を付与し、新規 `Any` を禁止します。
- `black` (120 桁)・`isort`・`ruff` は必ず `.venv` 経由で実行し、`Optional` 利用時は `None` ハンドリングを明示します。
- 1 ファイル 300 行以内・単一責務、定数は UPPER_SNAKE、型付き dataclass や Enum を優先してください。

## テスト指針
- Pytest 設定は `pyproject.toml` に集約され、`--strict-markers` と asyncio マーカーを厳守します。
- カバレッジ目標は statements/branches/functions/lines >= 80%、差分は `diff-cover` Added >= 85%、Changed >= 80% です。
- UI 変更時は Playwright スクリーンショット、axe 結果、visual diff を `artifacts\<task_id>\ui\` に格納し、手動検証を `APPROVALS.md` に追記します。

## コミットとプルリク
- Conventional Commits (例: `feat(mail): add lease audit`)＋署名＋`Signed-off-by` を必須とし、ブランチは `feature/*` `hotfix/*` `release/*` 命名を用います。
- PR には `diff-plan.json`、PLAN/Test/Patch 証跡、`APPROVALS.md` の二者承認、CI（black/isort/ruff/mypy/pytest/diff-cover/bandit/sbom/secret_scan/eol_check）結果を添付します。
- UI や危険操作は必ず Dry-Run→Apply 手順・SafeOps ログ・スクリーンショットを伴わせ、`observability\dashboard\` 更新と `artifacts\<task_id>\overview.html` 生成を確認してください。

## セキュリティとエージェント手順
- すべての変更は Plan-Test-Patch ワークフロー上で行い、実行ファイルは `C:\Users\User\Trae\Codex-CLImutipule-CMD\.venv\Scripts\python.exe` など許可済みツールに限定します。
- `APPROVALS.md` の二者承認、`data\locks\workflow.lock` の取得、秘密情報の持ち出し禁止を徹底してください。
- UI 予算 (LCP <= 2.5s, TTI <= 3.0s, CLS <= 0.10, visual diff <= 10%, axe serious+ = 0) を超えた場合は即時ロールバックと再検証を行います。

## 実装作業の規則
- このリポジトリで作業・実装をする作業エージェントは、必ず `"C:\Users\User\Trae\ORCH-Next\projects\agent-missions-hub\作業方法.md"` に記載されたルールに従うこと。
- 1. まず `作業方法.md` を読み、その内容をすべて前提とする。
- 2. 以降のタスクは、`作業方法.md` のルールに従って Plan→Predict→Test→Patch→Commit→MD 更新のサイクルで実行する。

## ## 監査・テスト作業の規則
- このリポジトリの変更を監査・テスト・UI/デザインレビューする監査エージェントは、必ずリポジトリ直下の `監査・テスト方法.md` に記載されたルールに従うこと。
- 1. 監査タスクを開始する前に、`AGENTS.md` と `監査・テスト方法.md` を読み、MVP スコープと優先順位、評価観点（Blocking / Major / Minor / Cosmetic）および出力フォーマット（Summary / Findings / Tests / Suggested Patches / TODO for Worker Agent）を前提とする。
- 2. 監査結果を出力する際は、必ず `Status: Block / Proceed with fixes / Proceed` を含む Summary と、Blocker / Major / Minor / Cosmetic に分類した Findings、実行したテストと結果、必要最小限の diff を含む Suggested Patches、作業エージェント向けの TODO をセットでレポートすること。
- 3. Blocking / Critical な問題が存在しない場合は、原則として Status を `Proceed` または `Proceed with fixes` とし、「MVP 観点では出荷可能」であることを明示する。Minor / Cosmetic のみの場合、それらは TODO として整理するが、merge 自体をブロックしない。


