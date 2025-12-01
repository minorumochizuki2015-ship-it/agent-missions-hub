# agent-missions-hub Mission Control Plan

現行のノウハウ（`docs/legacy/` 配下）を踏まえ、Mission/Task/Artifact/Knowledge + Manager/Graph/Inbox 三面構成へ移行するための実行プラン。

## 1. チェックリスト（継続的に更新）

### 1.1 基盤とAPI
- [x] FastMCP ネイティブマウント + stateless_http=true（`src/agent_missions_hub/http.py`）
- [x] ensure_project / create_agent_identity / send_message を SQLModel バックエンドに接続
- [x] missions / task_groups / tasks / artifacts / knowledge の CRUD REST/JSON-RPC 追加
- [x] init_db/startup フックで DB マイグレーションを自動実行（`docs/legacy/plans/mvp_implementation_plan.md` 参照）
- [ ] WorkflowEngine v1（Sequential + self-heal）を CLI から切り出し

#### 1.1 次アクション
- CLI 版 `WorkflowEngine` から `src/mcp_agent_mail/workflow/` へのモジュール切り出しと docstring 追加、`docs/plans/mvp_detailed_technical_design.md` に定義済みのクラス図へリンク。
- Self-Heal 分岐を pytest `-k workflow` で回すため、`.venv\Scripts\python.exe -m pytest tests/test_workflow_engine.py`（新規）を runner プロファイル `medium` で追加。
- PLAN.json scope `AI オーケストレーション` と連動し、Runner 経由で context 入出力ログを `observability/policy/ci_evidence.jsonl` へ記録する。

### 1.2 UI / Runner / Health
- [x] 旧リポの UI／runner／監査資産（`apps/orchestrator-ui/`, `scripts/ui_audit*`, `runner*` など）を `feature/mvp-ui-audit` ブランチにコピー（※ 新リポ上でのビルド・動作検証はこれから）
- [ ] 言語トグル＋`/plan` `/test` ビューの Next.js 版を移植（`multi_agent_terminal_checklist_v2.md` の UI Gate 要件を満たす）
- [ ] `/api/health/ui` と runner スクリプト（Quick/Full）を移植
- [ ] mail_project.html の Manager/Inbox/Graph 3 面ラフ（`notes/ui/*.html` を参照し React へ再構築）

#### 1.2 次アクション
- `apps/orchestrator-ui` 直下で `npm install` 後に `npm run lint && npm run test && npm run test:e2e` を runner 経由（`.venv` PATH 固定）で実施し、結果を `observability/policy/ci_evidence.jsonl` へ記録。
- Lang toggle と `/plan` `/test` ビューは `app/(routes)/plan`・`app/(routes)/test` としてファイル分割、`Plan/Test Dashboard` を `docs/multi_agent_terminal_checklist_v2.md` の UI Gate 要件と照合して TODO 化。
- `/api/health/ui` の FastAPI 側スタブを `apps/orchestrator-api` へ追加し、`scripts/runner.py` から `curl` チェック→`ci_evidence` 追記までをワンコマンド化。

### 1.3 Evidence / Gate / Docs
- [ ] UI-Audit (JA/EN) スクリプトを `scripts/` に実装し、`observability/policy/ci_evidence.jsonl` へ追記
- [ ] `rules/APPROVALS.md` の二者承認フローを agent-missions-hub 用に更新
- [ ] `docs/plans/migration_up_down.md`（後述）に正式マイグレーション案を記載
- [ ] Auto Gate: `auto_gate_rules.yaml` に基づき CI で `auto_gate_decider` を実行し、`ci_evidence.jsonl` に `event=auto_gate_decision`（component=ui_gate/sbom/secret_scan/bandit/gitops_*, decision=run|skip|force_run, reason, base/head/pr）を記録する

#### 1.3 次アクション
- `scripts/ui_audit_run.py` を `.venv\Scripts\python.exe` 固定で実行できる runner プロファイル（`ui-audit`）を `scripts/runner.py` に追加し、JA/EN 両ビューの結果を `ui_gate_pass_sync` イベントとして集約。
- `rules/APPROVALS.md` の 2 人承認ルールに、SafeOps Phase2（CMD + AUDIT）と UI Gate プロモーションに必要な証跡一覧を追記。
- `docs/plans/migration_up_down.md` では `missions/tasks/artifacts/knowledge` の Up/Down SQL スクリプト名と実行順序を記述し、`PLAN.json` `scope[0]` の SafeOps bootstrap とリンクさせる。

### 1.4 Council PoC (ChatGPT CLI / 正確性のみ)
- プロファイル: 生成=creative/concise/code、ジャッジ=fact_checker（正確性 0–10）、議長=chair。直列・timeout=60s・再試行なし。
- 匿名化: プロファイル名/自己紹介/挨拶除去、ですます統一、回答順シャッフル。
- 評価: 減点方式（10=完全正確…0=無回答）、3以下は不採用候補として議長に通知。`Score: X/10` 形式を強制。
- エラーハンドリング: 個別失敗はスキップ記録、生成全滅で status=failed、fact_checker 全滅時は評価なしで議長が素回答から選択。
- ログ/証跡: `artifacts/council/<run_id>/` に成果物保存、`ci_evidence.jsonl` へ `council_run` を追記（question は `question_hash` のみ記録）。

## 2. 設計書・追加ドキュメント

## 2. 設計書・追加ドキュメント

### 2.1 Migration Draft
- `docs/plans/migration_up_down.md` を新規作成し、agents/ missions/ artifacts/ knowledge の up/down 手順を明文化。
- `docs/legacy/plans/agent_registration_ui_plan.md` の「起動時 ALTER」項を引用し、本番適用前に SQL ファイル化する方針を書く。

### 2.2 API 仕様 & 詳細設計
- **[NEW]** `docs/plans/mvp_detailed_technical_design.md`: Phase 2 の詳細設計（Mission/Task/Artifactスキーマ、WorkflowEngine、UI三面構成）を策定済み。
- create_agent_identity のオプション 4 項（task_description/summary/skills/primary_model）を追加。
- Missions/Tasks/Artifacts のエンドポイント（GET/POST）のペイロード・レスポンス例を追記。

### 2.3 UI / Workflow 設計
- `multi_agent_terminal_milestones_v2.md` に Manager/Graph/Inbox 三面構成のマイルストンを追加（Phase 1: Manager, Phase 2: Graph, Phase 3: Inbox 統合）。
- `multi_agent_terminal_checklist_v2.md` の UI Gate セクションへ Agent Mail 向けの具体タスク（言語トグル、Plan/Test、プロンプト確認）を追記。

## 3. マイルストン（例）

| Milestone | 目的 | 完了条件 |
|-----------|------|-----------|
| M0 | 基盤整備 | REST/JSON-RPC CRUD、init_db、自動テスト（`scripts/test_api_smoke.py`）が green |
| M1 | UI 土台 | Lang toggle + `/plan` `/test` + `/health/ui` + runner + UI-Audit pipeline (Phase 1 Completed) |
| M2 | Workflow/Artifacts | WorkflowEngine v1 (Sequential+Self-heal)、新スキーマ (Missions/Tasks/Artifacts)、Manager UI (Next.js) |
| M3 | Manager/Graph/Inbox | 三面 UI、ミッションタイムライン、Graph 可視化、Inbox メール連携 |

## 4. 運用メモ
- ドキュメントは `docs/legacy/` から参照しつつ、新規計画は `docs/plans/` 以下にまとめる。
- 変動の大きいチェックリストでも Git 管理を継続し、更新履歴でレビュアブルにする。
- UI/runner 資産を新リポ上で実行確認し、Playwright 監査や runner が単独で完結することを確認してから「移植完了」とする（確認前は legacy 証跡の日時を流用しない）。
- `observability/policy/ci_evidence.jsonl` はサンプルではなく実行結果に置き換え、ジョブ毎の SHA と日付を必ず残す。
- **[NEW]** `rules/APPROVALS.md` は `multi-agent` の運用ルール（Gate/Audit）に準拠し、厳格な承認フローを適用する。
- **Worktree/ブランチ運用（並走作業）**: 基本ブランチ=`feature/mvp-ui-audit`（worktree: `agent-missions-hub-remote`）、派生作業用ブランチ=`feature/mvp-ui-audit-work`（worktree: `../agent-missions-hub-work`）。作業は派生側で行い、適宜 rebase → PR/マージで基本ブランチへ統合する。
