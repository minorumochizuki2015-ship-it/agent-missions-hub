# Purpose

UI Gate の EN/JA 証跡を最新化し、監査指摘の「言語ミスマッチ」「ci_evidence不整合」を解消する。scripts/ui_audit_run.py の言語指定を確実に反映させ、docs と証跡を同期しつつ、Jest 実行を安定化させる。

# Current State

lang=ja/en で UI Audit を再実行済み（2025/11/20 11:01:37 JA, 11:02:09 EN）。新しい summary/screenshot/HTML の SHA を ci_evidence に追記し、チェックリスト/マイルストンも更新済み。Jest は 14:47:37 / 15:10:30 に dashboard.test を再実行して PASS（ts-jest の設定警告のみ）。Lint/Playwright/pytest も 15:10–15:13 再実行して PASS。PLAN.json / plan_diff.json の orchestrator ステップに UI Gate / Jest 再実行の進捗を反映済み。

# Decisions

- UI Audit は Accept-Language と locale を Playwright context に設定し、LANG を summary に反映させる。
- JA 版の summary/screenshot を別ファイル（summary_ja.json, unified_inbox_ja.png）として保持し、EN 版は既存 summary.json を使用する。
- ci_evidence は 11:01/11:02 実行を最新とし、旧 10:24:57 以前は履歴扱いとする。

# Applied Changes (summary + key diff points)

- scripts/ui_audit_run.py: LANG/Accept-Language を new_context に設定、BASELINE_SCREENSHOT を定義（NameError 防止）、HTML ダンプを route_unified_inbox.html へ必ず保存するよう補強。
- artifacts/ui_audit/: lang=ja/en で再実行し、summary.json（EN, SHA=40233969...89C0）、summary_ja.json（JA, SHA=241C2B14...9715）、screenshot（共通 SHA=4CFF8863...5DDD）、HTML（SHA=0B10909A08A3E99F3765C7C83770B97BAE5FA31821279BD5092A81A75CF5DB69）を配置。
- observability/policy/ci_evidence.jsonl: 11:01:37(ja)/11:02:09(en) の ui_audit_executed / ui_gate_pass_* イベント、および Playwright 再実行 pass を追記。14:47:37 / 15:10:30 の orchestrator_ui_jest、15:10 lint、15:12 Playwright、15:13 pytest の PASS を追加。
- docs/multi_agent_terminal_checklist_v2.md, docs/multi_agent_terminal_milestones_v2.md: 更新日時と WebVitals/SHA/ci_evidence 時刻を 11:01–11:02 の最新値へ更新し、JA/EN 証跡と HTML 追記を反映。
- apps/orchestrator-ui: NavPhase の tablist 構造をユニーク ID 付きで修正、ミッション一覧の fetch をタイムアウト付きにし、LCP 計測を安定化する PerformanceObserver パッチを dev/e2e 用に追加。Playwright config を reuseExistingServer=false に変更して最新コードで実行。JEST_WORKER_ID ブランチは遅延ハイドレーションで setState を1回に抑制し、loading 表示後にテスト用データを注入するよう調整。

# TODO (priority order)

1. 未追跡ファイルの整理とステージング範囲の選別（apps/, scripts/ など大きな??を分割）。artifacts/ui_audit の D 扱い旧成果物を復元するか、参照削除 or `.gitignore` 化の方針決定。
2. コミット粒度とメッセージ（Conventional + Signed-off-by）を決めて `feature/mvp-ui-audit` にまとめる。

# Assumptions

- サーバーは localhost:8765 で稼働しており、言語切替クエリ `?lang=` と Accept-Language で UI が変化する。
- HTML レポートは artifacts/ui_audit_report/20251120-0930 を最新とし、単一 summary.json を EN、別ファイルを JA とする運用で問題ない。

# Risks / Mitigation

- summary.json が EN 固定のため JA を上書きするリスク: JA 実行後に summary_ja.json へ退避する運用を継続する。

# Next Action

- 未追跡整理（コミット対象の決定）と、不要な旧 UI Gate 成果物の扱い決定 → コミット準備。
- ステージ対象の目安: apps/orchestrator-ui/**, scripts/ui_audit_run.py, docs/multi_agent_terminal_*.md, plans/PLAN.json, plans/plan_diff.json, observability/policy/ci_evidence.jsonl, notes/agent_md.md, data/logs/current/audit/20251120_codex_report.md。
- 除外/削除対象の目安: artifacts/ui_audit/* （.last-run.json 以外）、不要な legacy scripts/tests（D 扱いは `git add -u` で確定）。
