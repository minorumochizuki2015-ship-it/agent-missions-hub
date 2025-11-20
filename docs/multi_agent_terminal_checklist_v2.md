# マルチエージェント端末 チェックリスト v2

更新日時: 2025-11-20T11:02:09Z (UTC換算)

## UI Gate 状況
- 現在: PASS（EN: 2025/11/20 11:02:09 JST, JA: 2025/11/20 11:01:37 JST, script=ui-audit-v2）
- 証跡:
  - 英語ビュー: `artifacts/ui_audit/summary.json`（SHA256: 40233969C1BE9A6585B74D3EF3E0B5EAE395B64CB937F220401180DE8B7889C0, LCP=428ms / TTI=0.030s）と `artifacts/ui_audit/screens/unified_inbox.png`（SHA256: 4CFF8863068629E431823861FF3BD5078AAB990D89A4BEE7B9BBC31036515DDD）による `ui_gate_pass_en`（ci_evidence 時刻 2025/11/20 11:02:09）＋ HTML `artifacts/ui_audit/html/route_unified_inbox.html`（SHA256: 0B10909A08A3E99F3765C7C83770B97BAE5FA31821279BD5092A81A75CF5DB69）
  - 日本語ビュー: `artifacts/ui_audit/summary_ja.json`（SHA256: 241C2B14C896C18DCC86AE40FFE47072D8B3209DE5C22E8E4544441506629715, LCP=448ms / TTI=0.052s）と `artifacts/ui_audit/screens/unified_inbox_ja.png`（SHA256: 4CFF8863068629E431823861FF3BD5078AAB990D89A4BEE7B9BBC31036515DDD）による `ui_gate_pass_ja`（ci_evidence 時刻 2025/11/20 11:01:37）＋同 HTML ダンプ
  - `observability/policy/ci_evidence.jsonl` に 11:01/11:02 の `ui_audit_executed` / `ui_gate_pass_ja|en` を追記（旧 10:38/10:52/08:03 実行は superseded 履歴）
- 所見:
  - axe violations = 0（serious/critical 0）
- Web Vitals: 最新値（EN LCP=428ms / TTI=0.030s, JA LCP=448ms / TTI=0.052s）。閾値: LCP<=2.5s, CLS<=0.10, FID<=100ms, TTI<=5s
  - preview_dir: artifacts/preview/index.html（UI-Audit HTML の同期コピー）

## PASS 維持フロー
1. `artifacts/preview/` を更新して差分を記録（Plan→Test→Patch の範囲内）。
2. `./.venv/Scripts/python.exe scripts/ui_audit_run.py` で axe + WebVitals + screenshot を再取得（JA/EN 両方を実行）。
3. `artifacts/ui_audit/summary.json`・`artifacts/ui_audit/screens/unified_inbox.png`・`artifacts/ui_audit/report.html` の SHA を `observability/policy/ci_evidence.jsonl` に追記。
4. Gate=PASS を再確認後、`docs/multi_agent_terminal_milestones_v2.md` と `docs/operations/handover_recovery_checklist.md` を同期更新。

## 記録状況
- ci_evidence.jsonl: 2025/11/20 11:01:37（`ui_audit_executed` / `ui_gate_pass_ja`）と 11:02:09（`ui_audit_executed` / `ui_gate_pass_en`）を最新として追記。旧 08:03/10:24:57/10:52:01 実行は superseded で履歴参照のみ。
- pytest: `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_workflow_engine.py tests/test_http_liveness_min.py` → 2 passed / 1 skipped（11/20 実行）。
- ui_audit: `artifacts/ui_audit/summary.json`（SHA256: 40233969...89C0, LCP=428ms / TTI=0.030s）・`summary_ja.json`（SHA256: 241C2B14...9715, LCP=448ms / TTI=0.052s）と `screens/unified_inbox.png` / `screens/unified_inbox_ja.png`（4CFF8863...5DDD）。`axe_result.json`/`report.html` に加え HTML ダンプ `artifacts/ui_audit/html/route_unified_inbox.html` を再生成。HTML レポートは `artifacts/ui_audit_report/20251120-0930` を参照。
- JS tests: `npm run lint --prefix apps/orchestrator-ui` / `CI=1 npm run test --prefix apps/orchestrator-ui` / `npm run test:e2e --prefix apps/orchestrator-ui` を 11/20 09:25–09:30 に実行し、いずれも PASS（Jest は Dashboard ヘッダ期待値更新後、Playwright 13/13）。
- coverage: 2025/11/17 16:47:42 に `coverage_updated`（lines_valid=6522 / lines_covered=252 / line_coverage=0.03864）を記録（UI Gate より前の時刻）。

## Mission/Workflow 拡張チェック
- データモデル: missions/task_groups/tasks/artifacts/knowledge のスキーマとマイグレーションを定義し、ER 差分を plan_diff に反映する
- WorkflowEngine: Sequential 実行＋self-heal フックと `workflow_runs` トレースを実装する
- Artifacts/Knowledge: sha/version/tags を保持し、promote API で Knowledge に昇格できる
- Manager UI: Mission 一覧／TaskGroup タイムライン／Artifact タイルを表示し、Playwright/Jest で検証する
- Graph/Inbox: Graph View は Phase 3 で TODO、Inbox は Mission スレッド化の計画を docs に記載する
- 観測と記録: `ci_evidence.jsonl` に workflow_engine/manager_view イベント、`data/logs/current/audit/` にマイグレーション・実行ログを残す

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
