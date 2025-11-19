# マルチエージェント端末 マイルストーン v2

更新日時: 2025-11-17T17:10:20Z (UTC換算)

## 現在の状況
- UI Gate: PASS（preview_dir=artifacts/preview/, UI-Audit=ui-audit-v2, ts=2025/11/17 17:10:20）
- エビデンス:
  - 日本語ビュー `ui_gate_pass_ja`（`artifacts/ui_audit/summary_ja.json` 生成を nightly で行い、summary/screen/DOM の SHA を ci_evidence に記録）
  - 英語ビュー `ui_gate_pass_en`（`artifacts/ui_audit/summary_en.json` の LCP=344ms / TTI=0.018s を基準, screen/html は `_en` 付与でスナップショット済み）
  - `observability/policy/ci_evidence.jsonl` へ両イベント・nightly_preview_diff を追記（coverage_updated: 2025/11/17 16:47:42 / line_coverage=0.03864、UI Gate より前の時刻である旨を注記）

## 直近で完了した項目
1. preview 生成（`artifacts/preview/index.html` + README）を整備。
2. UI-Audit（Playwright + axe + WebVitals、日本語ビュー）を再実行し、serious=0 を確認。
3. Gate=PASS に更新し、`summary.json` の `gate.pass=true` を確認（JA/EN 両ビュー）。
4. `ci_evidence.jsonl` に最新 SHA と `ui_gate_pass_ja` / `ui_gate_pass_en` を追記。
5. 統合受信箱ソートメニュー日本語化（新しい順/古い順/送信者順）と戻りリンクの言語伝搬を完了。

## 次のマイルストーン
1. docs/operations/handover_recovery_checklist.md を PASS 状態と「ユーザー専用ログ」ポリシーに合わせて維持する。
2. nightly UI-Audit（cron）で `preview_dir` と `artifacts/ui_audit`（summary_{lang}/html_{lang}/screen_{lang}）の SHA を監視し、差分が出たら自動で Jira 連携。
3. 週次で `artifacts/preview/` と最新 Design-UI ハンドオフを突き合わせ、差分サマリを `reports/work/` に出力。

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
