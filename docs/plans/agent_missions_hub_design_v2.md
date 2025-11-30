# Agent Missions Hub / マルチエージェント端末 統合設計書 v2

## 0. ゴールとスコープ
- CodexCLI を親オーケストレータとし、複数 CLI エージェント（Claude/Gemini/自作 CLI など）を PTY 経由で制御するマルチエージェント端末を構築する。
- これらを Agent Missions Hub（データ・WorkflowEngine・UI・Observability）と統合し、Plan→Test→Patch の開発フローを直列＋並列で安全に自動化できる基盤にする。
- 既存 UI Gate / UI Audit・テスト・observability を壊さず、Phase 2A〜2D のロードマップで順次完成させる。

## 1. 現状サマリ（2025-11-20 時点）
1. UI / テスト状況  
   - Unified Inbox UI Gate: EN/JA 両方 PASS。LCP/TTI も性能基準クリア。エビデンスは `observability/policy/ci_evidence.jsonl` に記録済み。  
   - `tests/test_workflow_engine.py` と HTTP Liveness 最小テストが `.venv` 上で PASS。  
   - orchestrator-ui の lint/unit/e2e テストも 2025-11-20 実行で PASS 済（※現リポには未移植。移植後に再実行して証跡更新が必要）。
2. ドメイン／Workflow 拡張の状態  
   - `missions/task_groups/tasks/artifacts/knowledge` を導入する計画とチェック項目は定義済みだが、ER/マイグレーションの本実装はこれから。  
   - WorkflowEngine（Sequential＋self-heal）はスケルトン＋テスト雛形あり。完全実装は未。  
3. 移植状況  
   - 旧リポ `Codex-CLImutipule-CMD` → 新リポ `agent-missions-hub` への移植チェックリストが整理済み。Category 1〜4（コアアプリ・テスト・UI Audit・ドキュメント）を最優先。  
   - 必須ファイルチェック用 PowerShell スクリプト・初期セットアップ手順も記載済み。  
4. アーキテクチャコンセプト  
   - 低レイヤ: CodexCLI + PTY による multi-agent terminal（実行エンジン）。  
   - 高レイヤ: Agent Mail（メールボックス UI）＋ Manager View（Mission/TaskGroup/Artifact UI）。  
   - Agent Missions Hub として統合し、CodexCLI から Workflow API を叩く構造。方針メモは `kakunin.txt` を参照。  
5. マイルストーン定義  
   - Phase 2A: 移植＋データモデル確定  
   - Phase 2B: WorkflowEngine＋self-heal  
   - Phase 2C: UI 統合（Agent Mail / Manager View）  
   - Phase 2D: CLI / Multi-Agent Terminal 接続  
   - 追加: Breadcrumb/i18n 拡張、observability の運用タスク。旧マイルストーン v2 と整合。

## 2. 全体アーキテクチャ
### 2.1 レイヤ構成
- Core Domain / Storage: `missions/task_groups/tasks/artifacts/knowledge` テーブル、`data/` ストレージ、`observability/policy/ci_evidence.jsonl` ログツリー。  
- Workflow / Orchestrator: SequentialWorkflow（Mission→TaskGroup→Task）、self-heal フック、`workflow_runs` トレース。  
- UI: Unified Inbox（現行 UI Gate PASS）、Manager View（Mission/TaskGroup/Artifact）、Agent Mail（協調 UI）。  
- CLI / Multi-Agent Terminal: 親 CodexCLI が Workflow API を叩き、各エージェント CLI を PTY 経由で起動。役割ごとにセッション分離。

## 3. データモデル設計（Phase 2A）
### 3.1 テーブル概要
- missions: ゴール（ステータス/優先度/owner/timestamps）。  
- task_groups: Mission の論理分割（並列エージェント割当単位）。  
- tasks: 実作業単位（planned→in_progress→testing→done/failed）。  
- artifacts: diff/log/test-result/design-doc 等。`sha/version/tags/mission_id/task_id`。  
- knowledge: artifacts から promote した長期知識。`promote` API で昇格。
### 3.2 マイグレーション方針
1. 既存 DB に新テーブルを追加するマイグレーションを作成。  
2. `plans/diff-plan.json` に ER 差分（旧→新）を記録。  
3. 既存 Inbox スレッドや Agent Mail プロジェクトを `missions` などへマップする初期移行スクリプトを用意。  
4. マイグレーション実行ログは `data/logs/current/audit/` に保存。  
**完了条件:** マイグレーション適用＋pytest 最小セット PASS＋`plans/diff-plan.json` に差分記録。

## 4. WorkflowEngine 設計（Phase 2B）
### 4.1 SequentialWorkflow
1. mission_id から task_groups を優先度順に取得。  
2. 各 group 内の tasks を順次または並列に実行。  
3. 各 Task が Plan→Test→Patch を 1 サイクル。  
出力: `workflow_runs` レコード（status/started_at/finished_at/evidence_id）。
### 4.2 self-heal フック
- 失敗時に retry / 別ロールへの escalate / Human Overseer 介入を自動判断し、`ci_evidence.jsonl` と audit log に記録。
### 4.3 API（Missions Hub）
- `POST /missions/{id}/run` 起動、`GET /workflow_runs/{id}` 取得、`POST /tasks/{id}/override` でオーバーシア指示を反映。  
**完了条件:** `tests/test_workflow_engine.py` E2E PASS＋ci_evidence でトレース確認。

## 5. UI 統合設計（Phase 2C）
### 5.1 Manager UI
- Mission 一覧、TaskGroup タイムライン、Task 状態＋関連 artifacts を表示。  
- orchestrator-ui に新ルート追加し、Jest/Playwright に Manager 用テストを追加（UI Gate PASS 維持）。
### 5.2 Agent Mail 統合
- プロジェクト＝Mission、スレッド＝TaskGroup/Mission と対応付け。File Reservation を artifact/knowledge と連携。  
- メッセージと添付を Git/artifacts に紐付け「すべて記録」を満たす。
### 5.3 i18n / Breadcrumb
- Breadcrumb を Manager/View/Inbox/Compose 全体に適用。`?lang` 伝搬と `aria-current="page"` を UI Gate で検証。  
**完了条件:** `scripts/ui_audit_run.py` で Inbox＋Manager ルート PASS、Agent Mail 経由で優先度変更が一通り動作。

## 6. CLI / Multi-Agent Terminal 設計（Phase 2D）
### 6.1 実行エンジン（低レイヤ）
- 親オーケストレータは Python 製 CLI とし、Windows/PowerShell 7 からは常に  
  `.\.venv\Scripts\python.exe src\orchestrator\cli.py`  
  で起動する。これを **唯一の親 CLI 実行経路** とする（PS7 スクリプトはこのコマンドをラップするだけ）。
- 親 Orchestrator からは、各エージェント CLI を **Python の `subprocess.Popen`（または等価の標準ライブラリ API）で子プロセスとして起動** し、`stdin` / `stdout` / `stderr` を接続する。PowerShell の `Start-Process` は人間の手動起動用に限定し、オーケストレーション経路では使用しない。
- 初期サポート対象とするエージェント CLI は **CodexCLI** と **Claude Code CLI** の 2 種のみとする。Gemini CLI やその他 CLI は将来の拡張候補として `config/engines.yaml` などでプレースホルダ定義だけ行い、v1 実装では実際の起動ロジックを持たない。
- 各エージェント CLI（CodexCLI／Claude Code CLI）は見えない PTY（ConPTY 等）を伴う子プロセスとして起動し、親 Orchestrator が stdin/out/err を制御する。`:attach <agent>` は親 Orchestrator 経由で当該 PTY のストリームに一時的に直接接続する機能として実装する。
### 6.2 協調 UI（高レイヤ）
- Agent Mail でエージェント名ごとにスレッド整理し、PTY ログ要約をメッセージ化。  
- Missions Hub: CodexCLI から Workflow API を叩き、Plan→Test→Patch を Mission として登録。並列エージェントは複数 TaskGroup/Task に割当。
### 6.3 Observability
- CLI ログ ID・`workflow_runs` ID・`ci_evidence` を相互参照できるキー設計。  
**完了条件:** CodexCLI 起動→複数エージェント CLI 起動→Missions Hub 登録→Agent Mail/Manager View で追跡できるデモ完走。

### 6.5 実装結果（2025-11-30 更新）
- Typer ベースで親 CLI を実装し、`serve` で uvicorn（`agent_missions_hub.http:build_app`, factory）を起動、`call` で MISSIONS_HUB_API_BASE（デフォルト http://127.0.0.1:8000）配下のエンドポイントを GET/POST できるようにした。
- E2E: pytest `tests/test_cli_e2e.py` で uvicorn をサブプロセス起動→`cli call --endpoint /api/missions`→200/JSON 配列を検証し PASS。ci_evidence に `cli_call` / `cli_e2e_run` を記録。
- 制限: PTY 起動・複数エージェント同時制御・Message Bus 連携は未実装（Phase3以降で対応）。

### 6.4 実装タスク粒度
- 親オーケストレータ入口: `src/orchestrator/cli.py`（新設想定）に CodexCLI/multi-agent terminal の起動を実装し、Missions Hub API を呼び出す。Windows/PS7 からは常に `.\.venv\Scripts\python.exe src\orchestrator\cli.py` で起動することを前提とする。
- PTY: v1 では **Windows ConPTY ベース**で各エージェント CLI を分離し、親が `subprocess.Popen`＋擬似端末ラッパ経由で入出力を制御する。`tmux` を利用する WSL/Linux 構成は Phase 3 以降の PoC に限定し、本設計書の v1 実装範囲には含めない。
- ログ連携: PTY ログに run/session ID を付与し、`workflow_runs` と `ci_evidence.jsonl` に相互参照キーを記録。

## 7. マイグレーション & セットアップ
### 7.1 ファイル移植
- 移植元: `C:\Users\User\Trae\Codex-CLImutipule-CMD` → 移植先: `C:\Users\User\Trae\ORCH-Next\projects\agent-missions-hub`。  
- Category 1〜4 を優先（コアアプリ、テスト、UI Audit、ドキュメント）。Category 5〜8 はマトリクスに従い順次。  
### 7.2 環境セットアップ
- `.env.example`→`.env` コピー＋`STORAGE_ROOT` 等を相対パスで設定。  
- `.venv` 作成→`pip install -e .`。`npm install` / `playwright install chromium`。  
- `pytest tests/`・`npm run ui:audit` で基本動作確認。

## 8. フェーズ別 Plan→Test→Patch
- Phase 2A: Plan=ER/マイグレーション設計 → Test=マイグレーション＋pytest 最小 → Patch=差分修正。  
- Phase 2B: Plan=状態遷移/self-heal ポリシー → Test=`tests/test_workflow_engine.py` → Patch=失敗パターン修正。  
- Phase 2C: Plan=Manager/Agent Mail ワイヤー → Test=Playwright+axe/Jest → Patch=文言/A11y/Breadcrumb。  
- Phase 2D: Plan=CodexCLI→Workflow API フロー → Test=小規模リポで E2E → Patch=セッション/ログ連携修正。

## 9. 実装チェック ToDo（抜粋）
1. MIGRATION_CHECKLIST Category 1〜4 が全てチェック済み。  
2. `multi_agent_terminal_checklist_v2.md` の「Mission/Workflow 拡張チェック」が実装・テスト済み。  
3. マイルストーン v2 記載の Phase 2A〜2D の完了条件が `ci_evidence.jsonl` で確認できる。  
4. `kakunin.txt` の二段構成（CodexCLI+PTY / Agent Mail）と本設計書のロードマップが一致している。  
5. orchestrator-ui の lint/unit/e2e は移植後に再実行し、最新日付で証跡を更新する。
