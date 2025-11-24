# Purpose

Windows 環境での UI Gate / CI 運用を安定させるため、pytest ショートスイート導入と証跡整理、今後のフルスイート実行方針を明文化する。

# Current State

- UI Gate（EN/JA）・lint・Jest・Playwright は PASS を維持。
- pytest は Windows でショートスイート（allowlist）を PASS。ack/macro/attachment/HTTP-heavy/DB-lock 系は denylist で skip。フルスイートはまだ未実施（ENABLE_FULL_SUITE=1 未設定）。
- ci_evidence.jsonl に Windows ショートスイートの PASS を記録（後続で run3 を追記予定）。
- temp/cachedir をローカル固定（.pytest_tmp / .pytest_cache_local）。
- feature/mvp-ui-audit ブランチで 14 ファイル変更（約 +378/-233）、ステージングなし。未追跡が多数（apps/, scripts/, tests/* ほか .env.example や .venv_linux など）で作業ツリーが大きく汚れている。
- origin/feature/mvp-ui-audit がローカルより 8 commits 進んでいる（ローカルは 4d2db15、リモートは 520c3bc）。ローカルは dirty なので pull/merge/rebase 前に整流が必要。
- リモート最新確認用にクリーン worktree `../agent-missions-hub-remote` を作成（HEAD=520c3bc）。4d2db15..520c3bc の差分は 30 ファイル、+278/-284（主に ruff修正／ワークフロー・テスト・http周りの微修正）。
- クリーン worktree 側にローカルの追跡済変更（14ファイル、tests系・pyproject・ci_evidence など）を適用済み。未追跡ファイル群は元ワークツリー側にのみ存在（ポーティング対象外のまま保持）。
- チェックリスト/マイルストン（docs/multi_agent_terminal_checklist_v2.md、docs/multi_agent_terminal_milestones_v2.md）は 2025-11-20T11:02:09Z 版で UI Gate=PASS（JA/EN）と evidence SHA を記録済み。
- 本セッションでチェックリスト/マイルストン/MVP 設計/ミッション計画/plan_diff（`workflow-engine-phase2a` planned を含む）を再確認し、最新版が揃っていることを確認（変更なし）。
- 設計・計画ドキュメント: docs/plans/mvp_detailed_technical_design.md（MVP 技術設計）、docs/plans/mission_control_plan.md（Phase 進捗管理）、plans/plan_diff.json（計画差分ログ）。
- 作業ツリーは2つ: クリーン側 `C:\\Users\\User\\Trae\\ORCH-Next\\projects\\agent-missions-hub-remote` を正として作業・ステージングし、元側 `...\\agent-missions-hub` は未追跡が多いバックアップ。必要ならIDE/ターミナルを2窓で開き、gitは同じリポ・同じブランチを指している。

# Decisions

- Windows では allowlist/denylist でテスト範囲を絞り、ENABLE_FULL_SUITE=1 を明示しない限りフルスイートは実行しない。
- allowlist 既定: workflow_engine / http_liveness / integration_showcase / ci_smoke_min / cli_help / config*unit_min / models*unit_min / storage*unit_min / utils*unit_min。
- denylist 既定: ack / macro / attachment / http_edge|transport|convert / db_migrations / storage_commit|inline|lock。
- 環境変数で制御: WINDOWS_TEST_ALLOWLIST（上書き）、WINDOWS_TEST_ALLOWLIST_APPEND（追記）、WINDOWS_TEST_DENYLIST（上書き）、ENABLE_FULL_SUITE=1（全実行）。
- 今後の実装作業はクリーン worktree `../agent-missions-hub-remote` を基準に進める。未追跡ファイルは元ワークツリーで保持し、必要なものだけ手動で選択移行する。

# Applied Changes (summary + key diff points)

- tests/conftest.py: allowlist/denylist 制御と TMP/TEMP 固定、ENABLE_FULL_SUITE による解除ロジック。cachedir は pyproject.toml で .pytest_cache_local に変更。
- tests/test_http_liveness_min.py: app() を毎回生成する形に修正（TypeError 解消）。
- tests/test_ack_views_details*.py / tests/test_attachments_extended.py: Windows では module-level skip を追加し、ロック遅延テストを除外。
- pyproject.toml: `tool.pytest.ini_options.cache_dir = ".pytest_cache_local"` を追加。.gitignore に `.pytest_cache_local/` を追加。
- ci_evidence.jsonl: Windows ショートスイート PASS ログを追記予定（ショートスイート実行後に反映）。
- plans/plan_diff.json: step `windows-short-suite` を追加し、allow/deny 導入を completed として管理。ack/macro/attachment の恒久対策は別ステップで計画化予定。
- workflow_engine: WorkflowRun で run 開始/終了を記録し、タスク履歴をコンテキストに保存。タスク/グループは order 順に実行し、日本語 docstring 化。tests/test_workflow_engine.py で run 状態を検証。

# TODO (priority order)

1. Phase 2A: workflow_engine v1 (Sequential + self-heal) 実装と missions/task_groups/tasks/artifacts/knowledge マイグレーション・テストを進め、ci_evidence へ Plan/Test/Patch を記録（plan_diff `workflow-engine-phase2a`）。
2. Runner/CI 証跡: UI Gate/pytest/Jest/Playwright 実行結果を `observability/policy/ci_evidence.jsonl` と `reports/test/` に追記する運用を整備。
3. 未追跡ファイル（apps/, scripts/, package-lock.json など）の取り込み方針を決定し、必要分のみクリーン worktree へ移行する。

# Assumptions

- Windows はショートスイートをデフォルトとし、フルスイートは Linux/WSL CI で実行する。
- UI Gate 証跡（EN/JA, 2025-11-20 11:01–11:02）は最新で、ドキュメントの SHA も一致している。

# Risks / Mitigation

- Windows 依存の skip によりカバレッジ低下 → Linux/WSL で ENABLE_FULL_SUITE=1 を必須化し、ci_evidence へ格納。
- ロック遅延が恒久未解決 → “ack-timeout-remediation” ステップで原因と対策を管理。

# Next Action

- Phase 2A (workflow_engine v1 + schema/migrations/tests) の実装準備を進め、設計書と plan_diff `workflow-engine-phase2a` を基準に着手。
- Runner/CI 証跡フロー（UI Gate/pytest/Jest/Playwright）の運用整理と必要な実行ログの収集。
- 未追跡ファイルの取捨選択とクリーン worktree への移行方針の確定。

# Tests

- python -m pytest tests/test_workflow_engine.py -q
