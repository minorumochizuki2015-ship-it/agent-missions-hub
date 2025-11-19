# Agent Registration & Messaging UI Plan

## ゴール
- ブラウザからエージェント登録（program/model/name_hint/説明）とメッセージ送信を完結させる。
- APIキーはブラウザ側のみ保持し、トグルで `localStorage` / `sessionStorage` を切替。
- 既存 MCP ツール (`ensure_project` / `create_agent_identity` / `send_message`) を直接叩く。

## スコープ
- `mail_project.html` に2カードを追加  
  - 登録カード: program/select, model/input, name_hint/input, desc/input, APIキー＋保存先トグル、登録ボタン  
- 送信カード: 送信者/input, 宛先/multi-select(既存agents), 件名, 本文, 送信ボタン
- JS: `/mcp/` への JSON-RPC POST（Bearerに入力APIキー）。成功後トースト＋リロード。
- サーバ: 追加API不要（MCP直叩き）。必要なら minimal `/mail/api/register-agent` を後続で検討。

## 前提（Codex CLI / オーケストレーション）
- DBの `agents` レコードは「Codex CLI 等で動く論理エージェント定義」として扱う。CLI/コンソール側は同じ project_key/agent 定義を参照し、send_message 経由でオーケストレーションする（Swarm/crewAI 的な handoff も同じモデルで可）。
- program `"codex-cli"` は APIキー不要を想定（UIは空キー許容）。モデル候補は当面静的 (`gpt-5.1-codex`, `gpt-5.1-codex-mini`, `gpt-5.1`) で運用し、将来 `fetchModelList` の動的取得に差し替える。
- 役割プロンプト・スキル・モデルは UI で宣言し、CLI 側はそれを用いてタスク配分・成果物統合を行う。

## チェックリスト
- [ ] スキーマ追加（NULL許容）：agents に `task_summary` `skills(JSONB)` `primary_model` を追加し、既存 `task_description` を TEXT 長に拡張（ORM の `max_length=2048` も撤廃）
- [ ] `create_agent_identity` API: 新フィールドをオプション受け取りで保存（後方互換維持、未指定は task_description 先頭N字で task_summary を自動生成）
- [ ] Agent API/レスポンスに新フィールドを含める（未設定は null/空配列）
- [ ] UIカード追加: 見出し・説明は lang=ja/en 切替済み
- [ ] 登録フォーム: 役割プロンプト textarea + スキル選択（タグ/マルチセレクト）+ モデル入力
- [ ] Agentカード: task_summary 抜粋 + skills タグ表示、詳細モーダルで全文＋モデル表示
- [ ] モデル選択は `fetchModelList(program)` フックに集約（現状静的、将来API差替え）
- [ ] 入力ID: `reg-program`, `reg-model`, `reg-name`, `reg-desc`, `reg-role`, `reg-skills`, `reg-api-key`、`msg-sender`, `msg-to`, `msg-subject`, `msg-body`
- [ ] data属性: `data-api-key-input`, `data-api-key-storage-toggle`, `data-api-key-storage-label`
- [ ] JSON-RPC 呼び出し順序: ensure_project(human_key) → create_agent_identity(project_key, …) → send_message(...)
- [ ] 成功/失敗トースト表示、送信中はボタンdisabled
- [ ] エラー表示: HTTPステータス/JSON-RPCエラーを要約してUIに表示
- [ ] 送信者: 登録済みエージェントセレクト＋自由入力併用
- [ ] 宛先: 未登録時のバナー表示＋登録導線
- [ ] 役割プロンプト確認リンク（モーダル）を送信UIに配置
- [ ] APIキー: ローカル保存のみを明示、空キーも許容される旨を文言化
- [ ] `localStorage`/`sessionStorage` 切替が動作することを確認
- [ ] スタイルが既存カードに干渉しないことを確認
- [ ] `lang=ja` で文言が日本語になることを確認
- [ ] UI Gate/Evidence: JA/EN の UI-Audit を再実行し、`observability/policy/ci_evidence.jsonl` と preview/SHA を `reports/ci_evidence*.jsonl` 系に追記（multi_agent_terminal_checklist_v2 に準拠）
- [ ] API 仕様ドキュメントに `create_agent_identity` のオプション引数（task_description/task_summary/skills/primary_model）を追記し、後方互換である旨を明記
- [ ] 依存確認: .venv312 で `sqlalchemy` / `sqlmodel` / `python-decouple` / `filelock` / `Pillow` / `gitpython` / `markdown2` / `fastmcp` / `structlog` / `httpx` が導入済み（pip list で確認）

## マイルストン
0. ブランチ作成: `feature/agent-role-skills-ui`
1. DBマイグレーション + モデル/DAO拡張（新カラム追加、NULL許容）
2. `create_agent_identity` 入出力拡張（task_description/task_summary/skills/primary_model）
3. Agent API レスポンス拡張（後方互換維持）
4. UI: 登録フォーム拡張（役割プロンプト＋スキル＋モデル、APIキー文言）
5. UI: Agentカード＋詳細モーダル（抜粋/スキル/モデル表示）
6. UI: モデル選択を `fetchModelList(program)` に一本化（静的→将来API）
7. UI: 送信UX調整（送信者セレクト＋自由入力、未登録バナー、役割確認リンク）
8. 動作確認: 登録→カード反映、送信→Inbox、キー保存トグル、lang切替
9. ドキュメント更新（操作手順/リリースノート、API仕様、UI Gate Evidence 記録）

## ロールバック手順
- `git checkout -- src/mcp_agent_mail/templates/mail_project.html src/mcp_agent_mail/templates/base.html` （該当ファイルのみ）  
- 追加JSを削除し、トースト/バリデーション周りの変更を戻す  
- 必要なら `docs/plans/agent_registration_ui_plan.md` を削除

## メモ
- APIキーはサーバに保存しない。Bearerヘッダのみで使用。
- 既存 CLI と同じプロジェクトキーを使うことで inbox/outbox が同期される。
