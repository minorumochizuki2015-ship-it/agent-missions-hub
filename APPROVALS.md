# APPROVALS Ledger (Codex-CLImutipule-CMD)

| id | task_id | scope | op | status | requested_by | approver | approver_role | ts_req | ts_dec | manual_verification | signed_by | expiry_utc | evidence |
|----|---------|-------|----|--------|--------------|----------|---------------|--------|--------|---------------------|-----------|------------|----------|
| APPR-20251107-0001 | SAFEOPS-20251107-P0 | dangerous_command git clean -fdX | Dry-Run→Apply | approved | WORK | AUDIT@reviewer | AUDIT | 2025-11-07T06:20:00Z | 2025-11-07T07:30:00Z | YES | AUDIT@reviewer | 2025-11-08T06:20:00Z | ORCH/patches/2025-11/SAFEOPS-20251107-P0-APPR-0001.diff.md |
| APPR-20251125-0001 | STORAGE-COVERAGE | tests/test_storage_cov.py + storage.py diff-cover unblock | Patch/Test | approved | WORK | AUDIT@lead | AUDIT | 2025-11-25T17:30:00Z | 2025-11-25T18:00:00Z | YES | AUDIT@lead | 2025-12-02T17:30:00Z | reports/test/coverage_storage_cov.txt, reports/test/diff_cover_storage_cov.txt |
| APPR-20251125-0002 | SBOM-20251125 | SBOM generation (cyclonedx_py environment) | Generate SBOM | approved | WORK | SECURITY@lead | SECURITY | 2025-11-25T17:31:00Z | 2025-11-25T18:05:00Z | YES | SECURITY@lead | 2025-12-02T17:31:00Z | observability/policy/sbom.json, observability/policy/sbom_run.jsonl |

備考:
- 2人承認ルールを適用（requested_by≠approver）。APPROVALS.md と証跡ファイルの整合を維持。
- Apply 前に Dry-Run を実施し、危険コマンドの監査ログへ記録後に承認。
