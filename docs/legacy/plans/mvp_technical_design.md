# MVP 技術設計（並列CLI + API専用モード）

## 目的
- ローカルLLMを使用しないAPI専用モードを確立し、複数CLI（Codex, Cline, Cursor, Gemini）を並列運用する。
- 運用安定性のため、ポート競合回避と最小構成のキャッシュ・コスト管理を実装する。

## アーキテクチャ概要
- `MCP HTTP Server`:
  - 実体: `uvicorn mcp_agent_mail.http:build_http_app --factory`
  - 既定ポート: `8765`（競合時、近傍の空きポートへ自動回避）
- `並列CLI起動`:
  - スクリプト: `scripts/start_parallel_cli.ps1`
  - 役割: MCPサーバー起動 + 対象CLIの個別コンソールを同時に開く。
- `API専用モード（ローカルLLM無効化）`:
  - 強制環境変数: `LLM_ENABLED=false`, `LLM_CACHE_BACKEND=memory`, `LLM_CACHE_REDIS_URL=""`
  - アプリ側ガード: `src/mcp_agent_mail/llm.py` で `settings.llm.enabled` が false の場合、補助出力に短絡復帰。

## 主要コンポーネント
- `scripts/start_parallel_cli.ps1`
  - 機能: MCPサーバー起動、CLIコンソール（Codex/Cline/Cursor/Gemini）起動、API専用モード用の環境変数設定。
  - ポート競合対処: `Get-NetTCPConnection` による監視と近傍検索（+1 ~ +20）で未使用ポートを選択。
  - 使用例: `pwsh -File scripts/start_parallel_cli.ps1 -OpenCodex -OpenCline -OpenCursor -OpenGemini -ServerPort 8765`
- `src/mcp_agent_mail/config.py`
  - `LlmSettings`: 有効/無効, 既定モデル, 温度, max_tokens, キャッシュ種別/URL, コストログ有効化。
- `src/mcp_agent_mail/llm.py`
  - LiteLLM統合（直接 `litellm.completion` ルート）。
  - キャッシュ: in-memory（既定）/Redis（URL設定時）。
  - コストログ: `success_callback` による費用記録（Rich対応時は装飾出力）。
  - API専用ガード: `LLM_ENABLED=false` 時は空出力で短絡復帰。

## CLI統合
- 統合スクリプト（例）:
  - `scripts/integrate_codex_cli.sh --yes`
  - `scripts/integrate_cline.sh --yes`
  - `scripts/integrate_cursor.sh --yes`
  - `scripts/integrate_gemini_cli.sh --yes`
- 補助起動: `scripts/run_server_with_token.sh`（各統合スクリプトが生成・利用）

## 設定
- `.env.example`
  - `LLM_ENABLED=false`
  - `LLM_CACHE_BACKEND=memory`
  - `LLM_CACHE_REDIS_URL=`（空）
  - `LLM_DEFAULT_MODEL=gpt-5-mini`（プレースホルダ、外部APIキーに応じて自動エイリアス解決）
- `docker-compose.yml`
  - `server` サービスが `8765:8765` を公開。
  - DB（Postgres）とアーカイブ用ボリュームを定義。

## 運用フロー（マルチコンソール）
1. PowerShellで `start_parallel_cli.ps1` を起動（必要なCLIフラグを指定）。
2. 最初のコンソールで MCP HTTP サーバー起動ログを確認。
3. 各CLI用コンソールが開くので、クライアント側の設定（MCPインポート/トークン適用）を実施。
4. APIキーを設定している場合のみ、外部APIで推論が可能（ローカルLLMは無効）。

## 注意点
- 機密情報（APIキー）は `.env`/環境変数で管理し、ログ/ドキュメントに出力しない。
- Windows環境前提のため、ポート監視は `Get-NetTCPConnection` を使用。
- 行末はLF推奨（`.gitattributes` で `* text=auto eol=lf` を設定）
## MCP ツール仕様（追記）
### codex_get_config
- 役割: Codex CLI 等の外部クライアントへ、MCP HTTP接続情報と認証トークンを提供する。
- 入力: JSON-RPC `tools/call` （arguments: なし）
- 出力: `{"mcp":{"http":{"host","port","path"}},"auth":{"bearer":""|token}}`
- セキュリティ: bearer が未設定時は空文字を返却。ログへトークン値は出力しない。

### orchestrate（serve_http_status / ui_audit）
- 役割: オーケストレーション用の軽量操作。状態取得とRunner連携を行う。
- serve_http_status 入力/出力: `{"mcp":{"http":{"host","port","path"}},"auth":{"bearer":""|token}}`
- ui_audit 入力: `{action:"ui_audit"}`／出力: `{"status":"ok|error","code":int,"summary":artifacts/ui_audit/summary.json}`
- セキュリティ: 実行はローカルRunnerのみ。外部コマンド注入不可。成果物はアーティファクト配下に保存。