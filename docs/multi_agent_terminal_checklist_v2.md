# マルチエージェント端末 チェックリスト v2

更新日時: 2025-11-30T18:52:00Z (UTC換算)

## UI Gate 状況
- Auto Gate v1 を導入する。`auto_gate_rules.yaml` を参照し、`auto_gate_decider.py`（CI）で UI Gate の run/skip を判定する。
  - 判定結果は `event=auto_gate_decision` として `observability/policy/ci_evidence.jsonl` に記録する（component=ui_gate, decision=run/skip/force_run, reason を必須）。
  - 判定エラーや巨大 diff（閾値超過）、`main`/`release/*` へのマージ、`label: run-ui-gate` が付いた PR では強制実行（decision=run/force_run）。
  - 対象パス例: `apps/orchestrator-ui/**`, `src/**/templates/**`, `**/*.css|scss|ts|tsx`, `playwright.config*`, `scripts/ui_audit*.py`, `package*.json`。
  - UI Gate 実行時は従来どおり `npm run ui:audit:ci`（または `scripts/ui_audit_run.py`）を実行し、summary/screenshot/HTML の SHA を `ui_audit_executed` / `ui_gate_pass_*` として ci_evidence に追記。
- 最新状況: 2025-11-30 に `/mail` `/mail/manager` を EN/JA で ui_audit_run.py 実行し Gate=PASS（vitals_missing 許容）。Auto Gate 判定は引き続き no-ui-change=skip だが手動で実施済み。
- Web Vitals が取得できない場合（vitals_missing=true）は警告扱いで許容し、axe=0 であれば Gate=PASS と見なす。取得できた場合は LCP<=2.5s / CLS<=0.10 / FID<=100ms の予算で判定する。
- ローカルでの手動実行が必要な場合は従来手順を踏むこと:
  1. `npm run lint && npm run test && npm run test:e2e --prefix apps/orchestrator-ui`
  2. `python scripts/ui_audit_run.py`（JA/EN 両方）
  3. `artifacts/ui_audit/summary*.json`・`screens/*.png`・`report.html` の SHA を `observability/policy/ci_evidence.jsonl` に追記
  4. Gate=PASS を確認後、本チェックリストと docs/multi_agent_terminal_milestones_v2.md を同期更新

## PASS 維持フロー
1. `artifacts/preview/` を更新して差分を記録（Plan→Test→Patch の範囲内）。
2. `./.venv/Scripts/python.exe scripts/ui_audit_run.py` で axe + WebVitals + screenshot を再取得（JA/EN 両方を実行）。
3. `artifacts/ui_audit/summary.json`・`artifacts/ui_audit/screens/unified_inbox.png`・`artifacts/ui_audit/report.html` の SHA を `observability/policy/ci_evidence.jsonl` に追記。
 4. Gate=PASS を再確認後、`docs/multi_agent_terminal_milestones_v2.md` と `docs/operations/handover_recovery_checklist.md` を同期更新。
 5. CLI 経由で `/api/missions` を叩く E2E (serve+call) を実行し、ci_evidence に `cli_call` / `cli_e2e_run` を記録。

## Phase3（UI ダッシュボード刷新）完了条件（案B'）
- MISSIONS_HUB_API_BASE + `/api/missions` など実データを表示（モック撤廃）。
- 旧 `/mail` ダッシュボード要素（Smoke Test / メッセージ / プロジェクトカードなど）を統合した新レイアウト。
- i18n (EN/JA) 維持、axe=0、Web Vitals は取得できれば予算判定。未取得時は vitals_missing 許容を継続。
- Playwright/Jest/UI Audit EN/JA を再実行し PASS、ci_evidence に `ui_audit_executed` / `ui_gate_pass_*` を追記。

## ロードマップ（P0〜P4：Phase3 以降を含む）
- P0 設計同期: v1 スコープ（Sequential＋Windows/PS7＋ConPTY、CodexCLI+Claudeのみ、CodeMachine外部扱い）と mcp_agent_mail 中核化、役割プリセット/Signals 方針を設計・checklist・plan_diff に反映。
- P1 Mail/Lease 統合: mcp_agent_mail をマウントし Inbox/Outbox/予約 API を UI/CLI で統一、ci_evidence に mail/lease イベントを追記。
- P2 Orchestration UI + Signals: planner/executor/reviewer/overseer（ターミナル上限3〜4）で多エージェント起動し、ログから Dangerous/Approvals/Signals を検知して UI 表示。
- P3 Dashboard/Inbox 拡充: Smoke Test/メッセージ/プロジェクトカード/検索・フィルタを実データで復元し、UI Gate/テスト/UI Audit を再実行。
- P4 Mission/Task/Artifact/Knowledge: 中期スキーマを追加し、Manager/Graph/Knowledge の基盤を整備。

## 記録状況
- ci_evidence.jsonl: 2025/11/30 18:49–18:51 に `ui_audit_executed` / `ui_gate_pass_en|ja`（unified_inbox / manager）を追記。旧 11/20 分は履歴参照のみ。
- pytest: `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_workflow_engine.py tests/test_http_liveness_min.py` → 2 passed / 1 skipped（11/20 実行）。
- ui_audit: `artifacts/ui_audit/summary.json`（SHA256: 40233969...89C0, LCP=428ms / TTI=0.030s）・`summary_ja.json`（SHA256: 241C2B14...9715, LCP=448ms / TTI=0.052s）と `screens/unified_inbox.png` / `screens/unified_inbox_ja.png`（4CFF8863...5DDD）。`axe_result.json`/`report.html` に加え HTML ダンプ `artifacts/ui_audit/html/route_unified_inbox.html` を再生成。HTML レポートは `artifacts/ui_audit_report/20251120-0930` を参照。
- JS tests: `npm run lint --prefix apps/orchestrator-ui` / `CI=1 npm run test --prefix apps/orchestrator-ui` / `npm run test:e2e --prefix apps/orchestrator-ui` を 11/20 09:25–09:30 に実行し、いずれも PASS（Jest は Dashboard ヘッダ期待値更新後、Playwright 13/13）。
- coverage: 2025/11/17 16:47:42 に `coverage_updated`（lines_valid=6522 / lines_covered=252 / line_coverage=0.03864）を記録（UI Gate より前の時刻）。

## Mission/Workflow 拡張チェック
- データモデル: missions/task_groups/tasks/artifacts/knowledge のスキーマとマイグレーションを定義し、ER 差分を `plans/diff-plan.json` に反映する
- WorkflowEngine: Sequential 実行＋self-heal フックと `workflow_runs` トレースを実装する
- Artifacts/Knowledge: sha/version/tags を保持し、promote API で Knowledge に昇格できる
- Manager UI: Mission 一覧／TaskGroup タイムライン／Artifact タイルを表示し、Playwright/Jest で検証する
- Graph/Inbox: Graph View は Phase 3 で TODO、Inbox は Mission スレッド化の計画を docs に記載する
- 観測と記録: `ci_evidence.jsonl` に workflow_engine/manager_view イベント、Auto Gate の run/skip（event=auto_gate_decision, component=ui_gate/sbom/secret_scan/bandit/gitops_*）を残し、`data/logs/current/audit/` にマイグレーション・実行ログを残す
- v1 スコープ: Workflow は Sequential＋TaskGroup 内の簡易並列に限定し、DAG/AsyncThink/LangGraph など高度並列は Phase 3 以降。CLI 実行は Windows/PS7＋ConPTY で親 CLI（`.\.venv\Scripts\python.exe src\orchestrator\cli.py`）から `subprocess.Popen` 経由で起動。初期サポート CLI は CodexCLI＋Claude Code CLI のみ（その他はプレースホルダ）。WSL+tmux/CAO はオプション扱いで v1 の対象外。
- Mail/Lease SSOT: MailClient API（/api/mail send/list, /api/leases create/release）で統一済み。ci_evidence に smoke OK (2025-11-30) を記録。
- Signals UI: Manager 右カラムに Signals パネル実装済み。2025/11/30 UI Gate（EN/JA）で表示確認済み。

## 備考
- Nightly の `nightly_preview_diff` は 08:10:20 のスナップショット時刻を基準として記録（UI Gate の最新は 17:10:xx）。運用上は UI Gate を“最新”基準とし、nightlyは差分検知用途に限定。
- すべて UTF-8 / LF を維持し、preview_dir 欠落を検知した場合は即座に Blocker を再登録。
- UI 予算（LCP<=2.5s, CLS<=0.10, FID<=100ms, TTI<=5s）を超過した際はロールバック→修正→再監査。
### UI Breadcrumb 監査項目（新規）
- ランドマーク: `nav`＋`aria-label="Breadcrumb"` が存在する
- 構造: `ol`＋`li` で階層を構造化し、現在ページに `aria-current="page"`
- 言語維持: `?lang=ja|en` がリンクへ伝搬し、文言が切り替わる
- キーボード: Tabでリンクに順次フォーカス可能、フォーカスインジケータが見える
- コントラスト: テキストと背景のコントラスト比≥4.5:1（リンク・現在ページ）
### UI Gate 最新
- 日本語/英語双方のビューで監査済み。`artifacts/ui_audit/summary.json`（EN）および `summary_ja.json`（JA）の `gate.pass=true`
- Evidence: `observability/policy/ci_evidence.jsonl` の `ui_gate_pass_ja` / `ui_gate_pass_en` イベントに summary / screen の SHA を記録済み。
- 追加検証: ソートメニュー（新しい順/古い順/送信者順）と「Back to Project」等のリンクに `?lang=ja` / `?lang=en` が伝搬することを確認

## Council PoC v1（ChatGPT CLI / 正確性のみ）
- プロファイル: 生成=creative/concise/code、ジャッジ=fact_checker、議長=chair（すべて直列、timeout=60s、再試行なし）。
- 評価軸: 正確性のみ（0–10整数、Score: X/10 形式、3以下は不採用候補として議長に伝達）。
- 匿名化: プロファイル名・自己紹介・挨拶を除去、ですます統一、回答順シャッフル。
- ci_evidence: `event=council_run`, `run_id`, `timestamp`, `question_hash`（生質問はログ禁止）, `chosen_answer_id`, `scores:{accuracy}`, `scores_ext`, `profiles_used`。
- エラー処理: 個別失敗はスキップ記録、生成全滅で status=failed、fact_checker 全滅時は評価なしで議長が素回答から選択。
- アーティファクト: `artifacts/council/<run_id>/` に question.txt（原文はここだけ保存）、answers_raw/anonymized、accuracy_evaluations、final_decision、council_run.log を残す。
