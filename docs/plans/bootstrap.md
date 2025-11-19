# bootstrap

新リポジトリの初期構成メモ。

## 目的
Mission/Task/Artifact/Knowledge を中心としたマルチエージェント基盤の検証を進める。

## スコープ（初期）
- スキーマ雛形を用意し、MCP/HTTP スタブを立てる。
- UI ベース（言語トグル、/plan、/test）の移植用土台を作る。
- Evidence/Gate のパスと運用ログファイルを最初から置く。

## TODO（次アクション）
- [x] FastMCP のネイティブマウントを http.py に実装し、ensure_project/create_agent_identity/send_message を最小で接続。
- [x] missions/task_groups/tasks/artifacts/knowledge の永続化層を追加（SQLModel/SQLAlchemy 前提）。
- [ ] REST/JSON-RPC CRUD（missions/task_groups/tasks/artifacts/knowledge）を追加。
- [ ] WorkflowEngine v1 / self-heal フックの抽出。
- [ ] UI-Audit パス、ci_evidence.jsonl 追記フローを scripts/ に追加。
- [ ] `docs/plans/mission_control_plan.md` を順次更新し、マイルストン・設計差分を反映。
