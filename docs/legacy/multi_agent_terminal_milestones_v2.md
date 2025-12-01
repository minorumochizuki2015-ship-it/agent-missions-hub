# マルチエージェント端末 マイルストーン v2

更新日時: 2025-11-17T17:10:20Z (legacy 証跡) → **新リポでの確認は未実施**

## 現在の状況
- UI Gate: **未検証**（旧リポの PASS を参照中。新リポで Playwright 監査が通った段階で更新する）
- エビデンス（legacy 参考値）:
  - 日本語ビュー `ui_gate_pass_ja`（`artifacts/ui_audit/summary_ja.json` を旧環境で生成、summary/screen/DOM の SHA を ci_evidence に記録）
  - 英語ビュー `ui_gate_pass_en`（`artifacts/ui_audit/summary_en.json` の LCP=344ms / TTI=0.018s を基準として旧環境で取得）
  - `observability/policy/ci_evidence.jsonl` への `ui_gate_pass_*` / nightly_preview_diff は旧リポの値。新リポでの再実行前に参照しない。

## 直近で完了した項目（新リポ視点）
1. 旧リポから UI/runner/監査資産を `apps/orchestrator-ui/`・`scripts/ui_audit*`・`runner*` として取り込み、参照可能にした。
2. pytest／API スモークを新リポのみで実行し、バックエンド基盤が正常に動作することを確認。
3. 今後の UI-Audit を新リポで再実行し、結果をもとに本ドキュメントとチェックリストを更新する予定。

## 次のマイルストーン
1. 新リポで Next/React フロントをビルドし、`/plan` `/test` `/health/ui` の動作と preview 生成を確認する。
2. Playwright + axe UI-Audit を JA/EN で再実行し、`observability/policy/ci_evidence.jsonl` に最新 SHA を記録する。
3. 週次で `artifacts/preview/` と Design-UI ハンドオフを突き合わせ、差分サマリを `reports/work/` に出力。

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
