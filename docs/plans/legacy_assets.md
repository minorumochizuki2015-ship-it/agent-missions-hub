# Legacy Asset Inventory

Codex-CLImutipule-CMD から移植した知識資産の一覧と用途メモ。

## 1. Documentation
- `docs/legacy/plans/*`: agent_registration/mvp など既存計画
- `docs/legacy/operations/*`: AGENTS, ONBOARDING, CROSS_PROJECT, handover runbooks
- `docs/legacy/observability/runbook_v1.md`
- `docs/legacy/external/*.md`: MCP サーバ設計ガイド、運用アラインメント指針

## 2. Scripts (reference only)
Stored under `notes/scripts/legacy/` for再実装時の参照:
- `runner.py`
- `ui_audit/minimal_playwright_audit.py`
- `nightly_ui_audit.py`
- `ui_audit_run.py`
- ops ツール群: `update_coverage_and_evidence.py`, `verify_ui_gate_assets.py`, `normalize_eol.py`, `scan_secrets.py`

## 3. Observability / Policy Samples
- `observability/legacy/policy/REPORT_DRAFT_M4.md`
- `.../safeops_kpi.json`
- `.../detect_secrets_report_current.txt`
- `.../check_eol_report_current.txt`

## 4. Next Steps
- 必要箇所から仕様を抽出して `docs/plans/mission_control_plan.md` と `rules/` を更新。
- UI-Audit/runner の再実装時に `notes/scripts/legacy` を参照し、Playwright/ops スクリプトを再構築。
