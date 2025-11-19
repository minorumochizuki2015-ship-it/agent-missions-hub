# MVP 実装計画（UI Breadcrumb / i18n / Runner 日本語監査）

## 目的
- 日本語ビューで Breadcrumb のランドマークと階層を維持し、`?lang` の伝搬を保証する
- Runner により DOM/スクリーン/Evidence を最新化して SSOT と整合させる

## スコープ
- ルート: 統合受信箱・Inbox・Compose の3系統
- 証跡: `observability/policy/ci_evidence.jsonl` に `ui_gate_pass_ja` を記録（summary/screen/DOMのSHA）
- 文書: Checklist / Milestone / Operations の UI Gate セクション同期

## 実施手順
1. UI DOM監査テスト強化（`tests/test_ui_breadcrumb_lang.py`）
2. Runner 実行（日本語ビュー）で DOM/スクリーン・summary を更新
3. Evidence に `ui_gate_pass_ja` を追記し SHA を付与
4. 文書3点（Checklist/Milestone/Operations）を 2025/11/17 10:12 に同期
5. `scripts/nightly_ui_audit.py` をスケジュール実行し、`UI_AUDIT_LANG=ja/en` で順番に監査→`artifacts/ui_audit/summary_{lang}.json`/`route_unified_inbox_{lang}.html`/`unified_inbox_{lang}.png` をスナップショット保存し、`reports/work/nightly_preview_diff_<date>.md` と `observability/policy/ci_evidence.jsonl` (`ui_audit_executed`/`ui_gate_pass_{lang}`/`nightly_preview_diff`) に SHA・diff 指標を残す
6. `scripts/runner_validation.py --event ui_gate_pass_ja` で DOM/スクリーン/summary の SHA・SafeOps/Runner/ユーザーログ・Checklist/Milestone「更新日時」の同期を自動検証
7. pytest (`HTTP transport / storage / UI Gate` 追加テスト) の結果を `reports/ci_evidence.jsonl` に `coverage_updated` イベントとして追記し、差分カバレッジ≥80% を継続監視

## 完了判定
- 3ルートの DOM テストが合格
- Evidence の `ui_gate_pass_ja` に summary/screen/DOM の SHA が存在
- 文書の UI Gate セクションが同一タイムスタンプで整合
- `nightly_preview_diff_<date>.md` に JA/EN の diff 結果が記録され、差分発生時は Jira Webhook 通知が自動送信されている
- `scripts/runner_validation.py` の実行ログで DOM/ログ同期と Checklist/Milestone 更新日時一致が確認済み
- `reports/ci_evidence.jsonl` に `coverage_updated` イベントと LCP/CLS/TTI/視覚 diff 指標付きの `ui_audit_executed` / `ui_gate_pass_{lang}` が揃っている
