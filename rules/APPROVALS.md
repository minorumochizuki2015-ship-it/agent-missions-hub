# APPROVALS Ledger (Agent Missions Hub)

| id | task_id | scope | op | status | requested_by | approver | approver_role | ts_req | ts_dec | manual_verification | signed_by | expiry_utc | evidence |
|----|---------|-------|----|--------|--------------|----------|---------------|--------|--------|---------------------|-----------|------------|----------|
| APPR-20251120-0001 | PHASE1-CLEANUP | repo_cleanup | Apply | approved | CMD | USER | OWNER | 2025-11-20T04:50:00Z | 2025-11-20T04:55:00Z | YES | USER | 2025-11-21T04:50:00Z | commit:584da44 |

## 運用ルール
1. **2人承認ルール**: 原則として `requested_by` ≠ `approver`。ただし、初期開発フェーズ（Phase 1/2）におけるユーザー承認は特例として許可。
2. **Dry-Run 必須**: 破壊的変更（`git clean`, DB migration 等）は事前に Dry-Run 結果を提示し、承認後に Apply する。
3. **Evidence**: 承認の根拠となるアーティファクト（Diff, Log, Commit Hash）へのリンクを必ず記載する。
4. **Gate 連携**: UI Gate (LCP/TTI/Axe) の PASS が確認された場合のみ、UI 関連の変更を承認する。