# CLI Multi-Agent Orchestrator v1 実装ガイド（ショート版）

## 1. v1 ゴールとスコープ（実装サマリ）
- ゴール: 親 Orchestrator CLI から複数 CLI エージェント（Codex/Claude）を ConPTY 経由で起動し、Mission/Task を Sequential + 簡易並列(TaskGroup)で完走させる。
- v1 スコープ: OS=Windows、Shell=PowerShell 7、親CLI=`.\.venv\Scripts\python.exe src\orchestrator\cli.py`、子CLI=CodexCLI/Claude Code CLI（ConPTY + subprocess）。DAG/LangGraph は Phase3+。
- 外部API: コアv1では `allow_external_api: false` を起動時バリデーションとし、HTTPベース従量LLM/SaaSは禁止する。`config/engines.yaml` には kind=cli のみ列挙する。一方で、Aレーンや検証専用プロジェクトでは `allow_external_api: true` ＋ `engines_external.yaml` のような別設定を用意し、`@openai/codex-sdk` 等を利用した外部APIエンジンを「オプションの拡張」として接続する余地を残す（コアDoDには含めない）。
- チャット連携: 現状は非対話バッチ（`codex exec`）で完走を確認済み。`codex chat` を用いた双方向連携は未実装で、ConPTY ストリーミング＋attach 機能を追加する Phase3+ タスクとして扱う。
- 本ブランチは Phase3+（chat/ConPTY/attach）の先行 PoC であり、v1 DoD（非対話 exec 完走）には含めない。
- Phase3+ の進め方（推奨）: attach/複数ロールチャットは新規ブランチ `feature/chat-attach`（Bレーン）で着手し、最小ゴールを「人間が既存 chat セッションへ TTY attach できる」に限定する。ロール間ハンドオフは Message Bus 拡張で別管理とし、テストは Tレーン（tests/**）に分離する。

## 2. 必須設定（抜粋）
```yaml
engine:
  allow_external_api: false
  config_file: "config/engines.yaml"
  enabled_engines:
    - codex-cli
    - claude-cli
```
- 起動前に `allow_external_api != false` や HTTP エンドポイントがあればエラーで弾く。

## 3. 実行コマンドと DoD
- エントリポイント: `.\.venv\Scripts\python.exe src\orchestrator\cli.py`
- 代表コマンド: `orchestrator run --roles planner,coder,tester --mission <id>`
  - DoD: Codex/Claude CLI が ConPTY で起動し、SequentialWorkflow が完走。ログは `data/logs/current/`、トレースは `workflow_runs` + `ci_evidence.jsonl`。Shadow Audit に PLAN/TEST/PATCH/APPLY 記録。

## 4. 並列・評議会・自律度
- 並列定義: CLI並列＝子CLI同時起動、Workflow並列＝TaskGroup/DAG。v1は TaskGroup の簡易並列のみ。DAG/LangGraph系は Phase3+。
- 評議会: P3+で実装（候補生成→評価→本線マージ）。v1は設計予約のみ。
- 自律度: v1/P2 は Human Overseer 必須（Signals/Approvals）。完全自律は Phase3+ 目標。

## 5. データモデル連携の最小セット
- Mission/TaskGroup/Task: Missionを選択し、TaskGroup(kind=sequential|parallel)＋Task(agent_id=Codex/Claude)で定義。
- Artifact/Knowledge: v1は `plan/diff/test_result` をartifact保存。必要に応じ promote→Knowledge。
- Signals/Shadow Audit: `session_id` / `role_id` を共通キーとして記録。危険コマンド/承認要求は Signals に保存し、ci_evidence/Shadow Audit にもイベントを残す。

## 6. ログと証跡の仕分け
- runner raw logs: `data/logs/current/runner/**`
- 監査: Shadow Audit (manifest.jsonl + hash chain + cosign署名) ※ manifest は `observability/policy/shadow_audit/manifest.jsonl`
- CI証跡: `observability/policy/ci_evidence.jsonl`
- verify_chain は関数直呼び出しで実行（余計な PLAN 追加を防ぐ）。

## 7. フェーズ別 DoD（CLI 観点）
- P0: `allow_external_api: false` バリデーション実装、Codex/Claude CLI を ConPTY で起動可。
- P1: Mail/Lease から Mission を取得し Runner が Orchestrator を起動（前提設計に従う）。
- P2 (v1完成ライン / goal_id=cli-v1-orchestrator): `orchestrator run --roles ...` で Mission 完走し、logs/workflow_runs/ci_evidence/Shadow Audit が一貫して残る。
- P3+: DAG/評議会/branching/self-healを拡張し、HITL 依存を段階的に縮小。
