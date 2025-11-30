# CLI オーケストレータ設計（Plan→Test→Patch 多エージェント）

## 目的とスコープ
- CodexCLI 親オーケストレータが PTY 付き子プロセスとして各ベンダー公式 CLI（例: claude-cli, gemini-cli, 自作 codex-agent-cli）を起動し、Plan→Test→Patch を単独またはマルチエージェントで実行する。
- 課金・認証はユーザー自身の定額プラン/CLI ログインを利用し、オーケストレータ側は API キーやトークンを保持しない。
- UI/Agent Mail（FastAPI+Jinja）は協調・履歴表示の上位レイヤとして活用し、実行は CLI 側で完結させる。

## アーキテクチャ概要
- Orchestrator (親 CLI): セッション/エージェント ID 管理、PTY 生成、ロール別プロンプト適用、ログ集約、Plan→Test→Patch ループ制御。
- Agent CLI Workers: 各 CLI をロール別（Planner/Coder/Tester/Reviewer/Security など）に起動し、許可コマンドをマッピングしてサンドボックス化。
- Shared Context/Bus: MCP サーバまたは JSON ストアでハンドオフ／ブロードキャスト／並列タスクのコンテキストを共有し、テストログやプランを必要なエージェントに注入。
- Storage/Observability: `workflow_runs`・`observability/policy/ci_evidence.jsonl`・監査 JSONL に PTY 出力と結果を記録し、Agent Mail に要約を投下して Git/artifacts と突き合わせる。
- Workspace/Branching: エージェントごとに作業ディレクトリ/ブランチを分離（tmux/PTY ごと）。統合は親が実施（merge/patch 適用）。

## 認証・課金ポリシー
- 定額型 CLI: ユーザーに `claude-cli login` など公式ログインを事前実行してもらい、CLI が保存したトークンをそのまま利用。オーケストレータはトークン非保持。
- API キー型: ユーザーが環境変数または OS セキュアストアに設定し、子プロセス起動時に環境変数として引き渡すのみ。
- いずれも CodexCLI 側は鍵保存を行わず、課金はユーザーの契約枠に紐づける。

## ワークフロー（運用モード）
- シングルエージェント: 1 CLI が内在的に Plan→Code→Test→Fix を回す（Codex/Claude 標準ループ）。
- マルチエージェント階層: Planner→複数 Coder（並列）→Tester→Fixer/Reviewer→Integrator。失敗時はテストログをハンドオフし再プラン/再実装。
- モード切替: 手動承認ありのシーケンシャル／全自動ループを切替可能。`:attach <agent>` で任意 PTY に人間が介入できる。

## セキュリティとガードレール
- エージェント別 ExecPolicy/許可コマンドを明示（例: Tester は git commit 不可、Integrator のみ git push）。
- PTY セッション単位で kill/restart 可能にし、衝突時の被害範囲を限定。
- ログはリダクションフィルタを通して記録し、シークレット漏洩を防止。

## 実装ステップ
1. PTY 管理モジュール（Win: ConPTY/winpty、Py: pexpect、必要なら tmux）とセッション管理を実装し、ログ集約を `workflow_runs`/`ci_evidence` に配線。
2. ロール定義と起動プロファイル（Planner/Coder/Tester/Reviewer/Security）を用意し、許可コマンドマップを適用。
3. メッセージバス（MCP または JSON ストア）を実装し、Handoff/Broadcast/Parallel パターンで文脈を受け渡す。
4. Agent Mail 連携: CI/PTY ログ要約を投稿し、Human Overseer の指示を親が取り込み再計画。
5. 段階的 E2E テスト: 単独ループ → 並列 2 エージェント → フル役割編成で回し、証跡を `ci_evidence` に追加。

### 実装状況（2025-11-30 更新）
- 最小版 Typer CLI を追加し、`serve` で uvicorn factory（`agent_missions_hub.http:build_app`）を起動、`call` で MISSIONS_HUB_API_BASE（既定 http://127.0.0.1:8000）のエンドポイントを GET/POST 可能にした。
- pytest `tests/test_cli_e2e.py` で uvicorn サブプロセス起動→`cli call --endpoint /api/missions` の E2E を PASS。ci_evidence に `cli_call` / `cli_e2e_run` を記録。
- 未実装/制限: PTY 多段起動、ロール別エージェント管理、Message Bus 連携は未対応（Phase3 以降）。

## 依存・前提
- Windows 環境（PowerShell/WSL）での PTY サポート（ConPTY/winpty）を前提にする。Unix/macOS では pty/tmux に置換。
- 各 CLI は TTY 前提で動くため、非 TTY パイプではなく必ず PTY 経由で起動する。
- MCP/メッセージバスは最初はファイルベース JSON でも可。将来は MCP に揃える。

## 運用・証跡
- `ci_evidence.jsonl` に orchestrator-run ID・セッション ID・エージェント ID・実行コマンド・結果を記録。
- 失敗時は PTY ログとバスメッセージを紐付け、再現性を確保。
- UI Gate/pytest など既存の証跡フローと揃え、Agent Mail で人間承認ステップを挿入できるようにする。

## 今後の課題
- Manager UI からの attach/override 操作を API 化し、CLI/PTy と同期する。
- Security/Compliance 用の追加ガード（コマンド allowlist の強化、外部ネットワーク封鎖、SBOM/secret scan 連携）。
- 大規模並列時のコンフリクト解決フロー（ブランチ戦略、差分マージ、auto-cherry-pick）の設計。
