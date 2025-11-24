# マルチエージェント端末 マイルストーン v2

更新日時: 2025-11-20T11:02:09Z (UTC換算)

## 現在の状況
- UI Gate: PASS（preview_dir=artifacts/preview/, UI-Audit=ui-audit-v2, EN=2025/11/20 11:02:09, JA=2025/11/20 11:01:37）
- エビデンス:
  - 英語ビュー `ui_gate_pass_en`（summary SHA=40233969C1BE9A6585B74D3EF3E0B5EAE395B64CB937F220401180DE8B7889C0、screenshot SHA=4CFF8863068629E431823861FF3BD5078AAB990D89A4BEE7B9BBC31036515DDD、LCP=428ms / TTI=0.030s、baseline SSIM=1.0、HTML SHA=0B10909A08A3E99F3765C7C83770B97BAE5FA31821279BD5092A81A75CF5DB69）
  - 日本語ビュー `ui_gate_pass_ja`（summary SHA=241C2B14C896C18DCC86AE40FFE47072D8B3209DE5C22E8E4544441506629715、screenshot SHA=4CFF8863068629E431823861FF3BD5078AAB990D89A4BEE7B9BBC31036515DDD、LCP=448ms / TTI=0.052s、baseline SSIM=1.0、HTML 同一 SHA）
  - `observability/policy/ci_evidence.jsonl` に 11:01:37 / 11:02:09 の `ui_audit_executed` / `ui_gate_pass_ja|en` を追記（coverage_updated: 2025/11/17 16:47:42 / line_coverage=0.03864 は UI Gate より前の時刻）

## 直近で完了した項目
1. preview 生成（`artifacts/preview/index.html` + README）を整備。
2. UI-Audit（Playwright + axe + WebVitals、日本語ビュー）を再実行し、serious=0 を確認。
3. Gate=PASS に更新し、`summary.json` の `gate.pass=true` を確認（JA/EN 両ビュー）。
4. `ci_evidence.jsonl` に最新 SHA と `ui_gate_pass_ja` / `ui_gate_pass_en` を追記。
5. 統合受信箱ソートメニュー日本語化（新しい順/古い順/送信者順）と戻りリンクの言語伝搬を完了。

## 次のマイルストーン
- **Phase 2A (データモデル/マイグレーション)**  
  - missions/task_groups/tasks/artifacts/knowledge を追加し、マイグレーション＋ ER 差分を `plans/diff-plan.json` に記録。
- **Phase 2B (WorkflowEngine/self-heal)**  
  - SequentialWorkflow と self-heal フックを実装し、workflow_runs と ci_evidence にトレースを残す。
- **Phase 2C (Manager UI)**  
  - Mission 一覧／TaskGroup タイムライン／Artifact タイルを Manager View に実装し、Playwright で検証。
- **Phase 2D (Knowledge/Inbox/Graph 計画)**  
  - Artifact promote→Knowledge、Inbox を Mission スレッド化、Graph View は Phase 3 で TODO として明記。
- **運用タスク**  
  - docs/operations/handover_recovery_checklist.md の PASS 維持、nightly UI-Audit 監視、週次 preview 差分レポート。

## 参照ドキュメント
- `docs/multi_agent_terminal_checklist_v2.md`
- `docs/operations/handover_recovery_checklist.md`

## 備考
- すべて UTF-8 / LF・Plan→Test→Patch を順守し、SafeOps ログと SHA 記録を欠かさない。
- preview_dir 不備や UI 予算超過時は即時に Blocker を掲示し、ci_evidence へ記録する（`houkokuzenbun.txt` はユーザーのみが記載し、AI は触れない）。
### 追加マイルストン（UI Breadcrumb/i18n）
- 導入範囲拡張: 統合受信箱／プロジェクト／Inbox／Compose にBreadcrumb適用
- 監査合格: 日本語ビューで `nav[aria-label="Breadcrumb"]`・`aria-current="page"`・リンクへの `?lang` 伝搬を確認、UI Gate PASS維持
- Runner整備: DOM/スクリーンのピン留めと Evidence 追記（`ci_evidence.jsonl`）
