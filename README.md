# agent-missions-hub

新しいマルチエージェント基盤（Mission/Task/Artifact/Knowledge＋Manager/Graph/Inbox 三面構成）を検証するリポジトリです。`Codex-CLImutipule-CMD` で進めた agent-role-skills-ui 改修や multi-agent プロジェクトの言語トグル／Plan-Test ダッシュボード／runner／health エンドポイント等を段階的に移植します。

## 当面の進め方（ドラフト）
- スキーマ初版: missions / task_groups / tasks / artifacts / knowledge を projects/agents に紐付ける。
- HTTP/JSON-RPC: ensure_project / create_agent_identity / send_message の最小ルートを FastMCP ネイティブマウント＋stateless_http=true で実装。
- フロント: 言語トグルと `/plan` `/test` 相当のビューを追加し、UI Gate/Audit と連動。
- Evidence/Gate: UI-Audit (JA/EN) と ci_evidence.jsonl のパイプラインを最初から整備。
- Workflow/Mission: Sequential Workflow v1（self-heal フック付き）→ 将来 Graph/Parallel/Loop へ拡張。

## リモート
- origin: https://github.com/minorumochizuki2015-ship-it/agent-missions-hub
