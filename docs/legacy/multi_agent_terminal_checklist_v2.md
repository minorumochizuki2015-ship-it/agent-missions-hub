# マルチエージェント端末 チェックリスト v2

更新日時: 2025-11-17T17:10:20Z (UTC換算)

## UI Gate 状況
- 現在: PASS（2025/11/17 17:10:20 JST, script=ui-audit-v2）
- 証跡:
  - 日本語ビュー: `artifacts/ui_audit/summary_ja.json`（LCP=160ms / TTI=0.025s）/ `artifacts/ui_audit/screens/route_unified_inbox.png`（SHA256: BE3BABFBDF8A669E7CB9668FD0DD99A1663BD757A4FF871299FF13B7621A1339）/ `artifacts/ui_audit/html/route_unified_inbox_ja.html`
  - 英語ビュー: `artifacts/ui_audit/summary_en.json`（最新: LCP=344ms / TTI=0.018s）/ `artifacts/ui_audit/screens/unified_inbox_en.png` / `artifacts/ui_audit/html/route_unified_inbox_en.html`
  - `observability/policy/ci_evidence.jsonl`（events=`ui_gate_pass_ja` 2025/11/17 17:10:07 / `ui_gate_pass_en` 2025/11/17 17:10:20）
- 所見:
  - axe violations = 0（serious/critical 0）
- Web Vitals: 最新値（JA LCP=160ms / TTI=0.025s, EN LCP=344ms / TTI=0.018s）。閾値: LCP<=2.5s, CLS<=0.10, FID<=100ms, TTI<=5s
  - preview_dir: artifacts/preview/index.html（UI-Audit HTML の同期コピー）

## PASS 維持フロー
1. `artifacts/preview/` を更新して差分を記録（Plan→Test→Patch の範囲内）。
2. `./.venv/Scripts/python.exe scripts/ui_audit_run.py` で axe + WebVitals + screenshot を再取得（JA/EN 両方を実行）。
3. `artifacts/ui_audit/summary_{lang}.json`・`route_unified_inbox_{lang}.html`・`unified_inbox_{lang}.png` の SHA を `observability/policy/ci_evidence.jsonl` に追記。
4. Gate=PASS を再確認後、`docs/multi_agent_terminal_milestones_v2.md` と `docs/operations/handover_recovery_checklist.md` を同期更新。

## 記録状況
- ci_evidence.jsonl: 2025/11/17 17:10:07（`ui_gate_pass_ja`）および 17:10:20（`ui_gate_pass_en`）に summary / screen / DOM の SHA と Web Vitals/visual_diff を記録済み。
- artifacts/ui_audit/screens/: `route_unified_inbox.png` / `unified_inbox.png` を最新化し、それぞれ JA/EN 監査と連動。
- coverage: 2025/11/17 16:47:42 に `coverage_updated`（lines_valid=6522 / lines_covered=252 / line_coverage=0.03864）を記録（UI Gate より前の時刻）。

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
- 日本語/英語双方のビューで監査済み。`artifacts/ui_audit/summary.json` の `gate.pass=true`
- Evidence: `observability/policy/ci_evidence.jsonl` の `ui_gate_pass_ja` / `ui_gate_pass_en` イベントに summary / screen / DOM の SHA を記録済み。
- 追加検証: ソートメニュー（新しい順/古い順/送信者順）と「Back to Project」等のリンクに `?lang=ja` / `?lang=en` が伝搬することを確認
