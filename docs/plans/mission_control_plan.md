# agent-missions-hub Mission Control Plan

現行のノウハウ（`docs/legacy/` 配下）を踏まえ、Mission/Task/Artifact/Knowledge + Manager/Graph/Inbox 三面構成へ移行するための実行プラン。

## 1. チェックリスト（継続的に更新）

### 1.1 基盤とAPI
- [x] FastMCP ネイティブマウント + stateless_http=true（`src/agent_missions_hub/http.py`）
- [x] ensure_project / create_agent_identity / send_message を SQLModel バックエンドに接続
- [x] missions / task_groups / tasks / artifacts / knowledge の CRUD REST/JSON-RPC 追加
- [x] init_db/startup フックで DB マイグレーションを自動実行（`docs/legacy/plans/mvp_implementation_plan.md` 参照）
- [ ] WorkflowEngine v1（Sequential + self-heal）を CLI から切り出し

### 1.2 UI / Runner / Health
- [ ] 言語トグル＋`/plan` `/test` ビューの Next.js 版を移植（`multi_agent_terminal_checklist_v2.md` の UI Gate 要件を満たす）
- [ ] `/api/health/ui` と runner スクリプト（Quick/Full）を移植
- [ ] mail_project.html の Manager/Inbox/Graph 3 面ラフ（`notes/ui/*.html` を参照し React へ再構築）

### 1.3 Evidence / Gate / Docs
- [ ] UI-Audit (JA/EN) スクリプトを `scripts/` に実装し、`observability/policy/ci_evidence.jsonl` へ追記
- [ ] `rules/APPROVALS.md` の二者承認フローを agent-missions-hub 用に更新
- [ ] `docs/plans/migration_up_down.md`（後述）に正式マイグレーション案を記載

## 2. 設計書・追加ドキュメント

### 2.1 Migration Draft
- `docs/plans/migration_up_down.md` を新規作成し、agents/ missions/ artifacts/ knowledge の up/down 手順を明文化。
- `docs/legacy/plans/agent_registration_ui_plan.md` の「起動時 ALTER」項を引用し、本番適用前に SQL ファイル化する方針を書く。

### 2.2 API 仕様
- `mvp_technical_design.md`/`mvp_detailed_technical_design.md` へ create_agent_identity のオプション 4 項（task_description/summary/skills/primary_model）を追加。
- Missions/Tasks/Artifacts のエンドポイント（GET/POST）のペイロード・レスポンス例を追記。

### 2.3 UI / Workflow 設計
- `multi_agent_terminal_milestones_v2.md` に Manager/Graph/Inbox 三面構成のマイルストンを追加（Phase 1: Manager, Phase 2: Graph, Phase 3: Inbox 統合）。
- `multi_agent_terminal_checklist_v2.md` の UI Gate セクションへ Agent Mail 向けの具体タスク（言語トグル、Plan/Test、プロンプト確認）を追記。

## 3. マイルストン（例）

| Milestone | 目的 | 完了条件 |
|-----------|------|-----------|
| M0 | 基盤整備 | REST/JSON-RPC CRUD、init_db、自動テスト（`scripts/test_api_smoke.py`）が green |
| M1 | UI 土台 | Lang toggle + `/plan` `/test` + `/health/ui` + runner + UI-Audit pipeline |
| M2 | Workflow/Artifacts | WorkflowEngine v1、自動 self-heal、Artifacts/Knowledge 保存・表示 |
| M3 | Manager/Graph/Inbox | 三面 UI、ミッションタイムライン、Graph 可視化、Inbox メール連携 |

## 4. 運用メモ
- ドキュメントは `docs/legacy/` から参照しつつ、新規計画は `docs/plans/` 以下にまとめる。
- 変動の大きいチェックリストでも Git 管理を継続し、更新履歴でレビュアブルにする。
- `observability/policy/ci_evidence.jsonl` はサンプルを参考にジョブ毎の SHA と日付を残す。
