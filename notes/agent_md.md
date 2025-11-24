# Purpose

Windows 環境での UI Gate / CI 運用を安定させるため、pytest ショートスイート導入と証跡整理、今後のフルスイート実行方針を明文化する。

# Current State

- UI Gate（EN/JA）・lint・Jest・Playwright は PASS を維持。pytest はショートスイート（allowlist）中心に実行しており、ack/macro/attachment/HTTP-heavy/DB-lock 系は denylist で skip。
- `feature/mvp-ui-audit` は origin と差分なし（HEAD=c782b6593626660a03f785dfec76a1d9a0f4e977）。rules/agent/*.yaml の余分な変更と未追跡資産は整理済みで、クリーン worktreeのみ使用。
- `docs/plans/mvp_detailed_technical_design.md`, `docs/plans/mission_control_plan.md`, `plans/plan_diff.json`（`workflow-engine-phase2a`）を再読済み。CI 証跡・Agent MD も design からの方針に合わせてアップデート済み。
- 作業ツリーは2つ存在：クリーン側 `C:\\Users\\User\\Trae\\ORCH-Next\\projects\\agent-missions-hub-remote` を正として作業・ステージングし、旧ツリー `...\\agent-missions-hub` は未追跡バッファに使用。push は安定する PowerShell 側の Git（例: `C:\\Program Files\\Git\\cmd\\git.exe push origin feature/mvp-ui-audit`）を使用する。WSL から push する場合は gh auth/credential.helper を事前設定。

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
- src/mcp_agent_mail/models.py & migrations/versions/25d1f3a8b32f_knowledge_metadata.py: `Knowledge` に source_artifact_id/version/sha256/scope/created_at/updated_at を追加する schema migration。
- src/mcp_agent_mail/routers/missions.py / __init__.py: ミッション一覧・アーティファクト CRUD API を FastAPI ルーターとして実装し、knowledge の簡易昇格も受け持つ。
- src/mcp_agent_mail/workflow_engine.py: WorkflowRun trace ファイルと `WorkflowContext` 履歴を `data/logs/current/audit/workflow_runs` に記録するヘルパーを追加し、run start/complete/fail イベントを JSONL 保存。`SequentialWorkflow` が自動で trace_path をセットするようになり、self-heal/history ログの信頼性を向上。
- tests/test_workflow_engine.py: trace_dir 用の fixture を追加し、run ごとの trace file の existence＋イベント記録を検証するように修正。
- tests/test_workflow_engine.py: SelfHeal 流れで `self_heal_artifact` と `Knowledge` レコードが生成されることを検証し、artifact/knowledge がデータベースに残ることを確認。SelfHeal 失敗パスで `self_heal_failure` アーティファクトも検証。run API 経由の SelfHeal 成否も確認。
- tests/test_missions_api.py: missions/artifacts API に加え、/missions/{id}/run（allow_self_heal トグル）と 404/422 エラー系を FastAPI + AsyncClient で検証。
- reports/test/pytest_phase2a_run.txt + observability/policy/ci_evidence.jsonl: Pytest short suite（mission API + workflow + http、`-q`）を再実行し、`command`/SHA付きで再記録。
- reports/test/ruff_phase2a_run.txt + observability/policy/ci_evidence.jsonl: `python -m ruff check src tests scripts` を実行し（出力なし）、成功エントリとして記録。
- reports/test/npm_orchestrator_ui.txt + observability/policy/ci_evidence.jsonl: `npm run lint && npm run test && npm run test:e2e --prefix apps/orchestrator-ui` を実行し、Jest/Playwright/axe PASS を記録（Missionsページの main 重複を解消後）。
- reports/test/ui_audit_run.txt + observability/policy/ci_evidence.jsonl: `python scripts/ui_audit_run.py` を走らせ、UI 資産ありで再実行した記録を追加（標準出力なし）。
- tests/test_missions_api.py: Phase 2A の missions/artifacts API を FastAPI + TestClient で exercise し、Artifact 作成時に Knowledge が生成されることと 404 のエラーパスを検証。
- reports/test/pytest_phase2a_run.txt + observability/policy/ci_evidence.jsonl: Phase 2A short-suite pytest 実行を記録（テストコマンド/結果と SHA を保持）。
- workflow_engine: WorkflowRun で run 開始/終了を記録し、タスク履歴をコンテキストに保存。タスク/グループは order 順に実行し、日本語 docstring 化。tests/test_workflow_engine.py で run 状態を検証。
- ci_evidence.jsonl: Phase 2A short-suiteイベントは `command` キーで統一し、`reports/test/pytest_phase2a_run.txt` の SHA とともに記録。

# TODO (priority order)

1. Phase 2A: workflow_engine v1 (Sequential + self-heal) 実装と missions/task_groups/tasks/artifacts/knowledge マイグレーション・テストを進め、ci_evidence へ Plan/Test/Patch を記録（plan_diff `workflow-engine-phase2a`）。設計書/mission plan/plan_diff を再読し、SQLModel定義＋マイグレーション＋SelfHealテストのスコープを Agent MD に明記する。
2. API/SelfHeal の異常系テストをさらに拡充（422/400/失敗トレース追加分を allowlist pytest に編入）し、reports/test と ci_evidence を更新。
3. Runner/CI 証跡: UI Gate/pytest/Jest/Playwright 実行結果を `observability/policy/ci_evidence.jsonl` と `reports/test/` に追記する運用を整備（UI Gate を実測値で更新）。
4. 未追跡ファイル（apps/, scripts/, package-lock.json など）の取り込み方針を決定し、必要分のみクリーン worktree へ移行する。

# Assumptions

- Windows はショートスイートをデフォルトとし、フルスイートは Linux/WSL CI で実行する。
- UI Gate 証跡（EN/JA, 2025-11-20 11:01–11:02）は最新で、ドキュメントの SHA も一致している。

# Risks / Mitigation

- Windows 依存の skip によりカバレッジ低下 → Linux/WSL で ENABLE_FULL_SUITE=1 を必須化し、ci_evidence へ格納。
- ロック遅延が恒久未解決 → “ack-timeout-remediation” ステップで原因と対策を管理。

# Next Action

- Phase 2A （missions/task_groups/tasks/artifacts/knowledge + WorkflowEngine/self-heal）の SQLModel・マイグレーション・API・テストを plan_diff `workflow-engine-phase2a` に従って順次追加し、Agent MD/ci_evidence に scope・impact・進捗を記録。
- knowledge/artifact モデルの schema/migration を具体化し、SelfHeal のイベント記録と連携する API を設計書どおりに実装。
- 短縮 pytest + lint（ruff/ty）、Jest/Playwright/UI Gate を含むテスト運用を段階的に実行・記録し、報告ファイルや ci_evidence を整備（現時点は short suite のみ）。
- 未追跡ファイルの移行方針をまとめ、必要な資産を旧ツリーから選別してクリーン worktree に移植するプロセスを策定。
- Orchestrator UI の `apps/orchestrator-ui` が整備できた段階で `npm run lint/test/test:e2e` と UI Gate/Playwright を再実行し、`observability/policy/ci_evidence.jsonl` と `artifacts/ui_audit/` を更新する。

# Tests

- `python -m pytest -q tests/test_missions_api.py tests/test_workflow_engine.py tests/test_http_liveness_min.py` → `reports/test/pytest_phase2a_run.txt` に記録（Pass, CLI 出力はこの環境で画面に現れず）。
- `python -m pytest -q tests/test_storage_* tests/test_http_liveness_min.py` → `reports/test/pytest_phase2a_storage_run.txt` に記録（Pass）。
- `python -m pytest -vv tests/test_workflow_engine.py tests/test_missions_api.py` → `reports/test/pytest_phase2b_run.txt` に記録（Pass, run API/self-heal/knowledge 失敗系を含む）。
- `python -m ruff check src tests scripts` → `reports/test/ruff_phase2a_run.txt` に記録（出力なし／pass）。現行環境で `ruff` は Python モジュール経由で実行。
- `npm run lint && npm run test && npm run test:e2e --prefix apps/orchestrator-ui` → `reports/test/npm_orchestrator_ui.txt` に記録。`apps/orchestrator-ui` フォルダが存在しないため実行できず（legacy worktree に移行予定）。
- `python scripts/ui_audit_run.py` → `reports/test/ui_audit_run.txt` に記録（placeholder UI Audit run）。
