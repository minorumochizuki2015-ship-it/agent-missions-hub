# マルチエージェント端末 マイルストーン v2

更新日時: 2025-11-30T18:52:00Z (UTC換算)

## 現在の状況
- UI Gate: PASS（preview_dir=artifacts/preview/, UI-Audit=ui-audit-v2, EN/JA=2025/11/30 18:48–18:52, vitals_missing=true 許容）
- 備考: Web Vitals が取得できない場合（vitals_missing=true）は警告として許容し、axe=0 なら Gate=PASS と扱う。取得できた場合は LCP<=2.5s / CLS<=0.10 / FID<=100ms の予算で判定する。
- engines.yaml を外部化し load_engine_config で loader 統合済み（2025-12-01、pytest tests/test_workflow_engine.py 4/4 PASS で確認）。
- CLI: `/api/missions` を CLI (serve+call) から叩く E2E を実施し、ci_evidence に `cli_call` / `cli_e2e_run` を記録。Mail/Lease smoke OK (2025-11-30 07:35:00Z) を ci_evidence に追記。
- 前提: UI Gate/Playwright/Jest 実行時は FastAPI 起動＋Seed 済み（`/health`=200, `/api/missions` 非空）を必須とし、未起動・空レスポンスは Gate=FAIL とする。
- serve 起動時に /health の結果を `cli_runs/<run_id>_health.log` に記録し、call 側で api_up/run_id/path を echo 済み（2025-12-02 wrapper pytest 4 passed）。
- Phase2D ログ補強は完了し、次は Phase2C 実データ UI への移行を進める。
- Phase2C: /api/missions 実データ表示を再有効化し、backend up+seed 前提で UI Gate EN/JA を再実行する計画を策定（次バッチで実装着手）。
- 次バッチで UI Gate EN/JA を再実行し、ci_evidence (Git外) に `ui_audit_executed`/`ui_gate_pass_*` を追記予定（backend up+seed 前提）。既存 right パネル骨組みは完了済み。
- Legacy UI 差分（要追従）: 旧UI（`C:\Users\User\Trae\Codex-CLImutipule-CMD`, Flask/Alpine/Tailwind拡張）で実装していた lang クエリ自動付与、ダークモード持続、トースト/チュートリアル等の共通コンポーネントは未移植。Phase2C〜P3で段階移植し、各バッチ開始時に legacy を参照してギャップを潰すこと。
- 移植優先順位（Phase2C〜P3）: ①lang/dark 持続＋トースト基盤 ②Agent登録/送信フォーム ③メッセージ検索・予約・添付 ④プロジェクト一覧・Unified Inbox ⑤ Signals/Approvals 実データ連動 ⑥ テーマ拡張（色/影/グラデ/フォント）
- ゴール管理: PLANに必ず goal_id/closes を記載し、1バッチ=1 goal_id・WIP=1を徹底。DoD達成時のみ `goal_completed` を発行し、PARKEDで中断を明示する。
- 新規ゴール: CLI単体でマルチエージェント実行を完了させる（goal_id=cli-v1-orchestrator）。DoD: `orchestrator run --roles planner,coder,tester --mission <id>` が ConPTY 経由で Codex/Claude を起動・完走し、必要時に `:attach <agent>` で介入でき、Shadow Audit/ci_evidence に記録が残ること。

## ロードマップ（P0〜P4：Phase3 以降を含む）
- **P0 設計同期**: v1 スコープ（Sequential＋Windows/PS7＋ConPTY、CodexCLI+Claudeのみ、CodeMachineは外部扱い）、mcp_agent_mail 中核化、役割プリセット・Signals 方針を設計・checklist・plan_diff に反映。
- **P1 Mail/Lease 統合**: mcp_agent_mail をマウントし Inbox/Outbox/予約 API を UI/CLI で利用、ci_evidence に mail/lease イベントを追記。
- **P2 Orchestration UI + Signals**: planner/executor/reviewer/overseer をプリセット（ターミナル上限3〜4）、ログストリームから Dangerous Commands/Approvals/Signals を検知し UI 表示。
- **P3 Dashboard/Inbox 拡充**: 旧 `/mail` の Smoke Test/メッセージ/プロジェクトカード/検索・フィルタを実データで復元し、UI Gate/テスト/UI Audit を再実行。
- **P4 Mission/Task/Artifact/Knowledge**: 中期スキーマを追加し、Manager/Graph/Knowledge の基盤を整備。
- **UI移植ゴール（段階）**: ①旧UIレイアウト移植完了（ナビ/右パネル/赤帯/カードをReact化）、②新機能追加（Signals/Approvals等の実データ連携）、③既存バックエンドとの完全統合（/api/missions 等を安定表示・UI Gate PASS）、④その上でUI/UXの高度化（パフォーマンス・アクセシビリティ・操作性強化）。

-## Phase 3（UI ダッシュボード刷新）※計画
- 旧 `/mail` ダッシュボード要素（Smoke Test / メッセージ / プロジェクトカード等）を統合し、実データ（MISSIONS_HUB_API_BASE + `/api/missions`）を表示する新レイアウトを実装する。UI Gate/Playwright 実行時は FastAPI 起動中（/health 200）かつ `/api/missions` 非空を必須条件とし、未起動・空レスポンスは Gate=FAIL とする。
- i18n (EN/JA) を維持しつつ axe=0 を目標。Web Vitals は取得を試み、未取得の場合は vitals_missing 許容を継続。
- Playwright/Jest/UI Audit EN/JA を再実行し PASS、ci_evidence に最新の `ui_audit_executed` / `ui_gate_pass_*` を記録。
- エビデンス:
  - 英語ビュー `ui_gate_pass_en`（summary SHA=40233969C1BE9A6585B74D3EF3E0B5EAE395B64CB937F220401180DE8B7889C0、screenshot SHA=4CFF8863068629E431823861FF3BD5078AAB990D89A4BEE7B9BBC31036515DDD、LCP=428ms / TTI=0.030s、baseline SSIM=1.0、HTML SHA=0B10909A08A3E99F3765C7C83770B97BAE5FA31821279BD5092A81A75CF5DB69）
  - 日本語ビュー `ui_gate_pass_ja`（summary SHA=241C2B14C896C18DCC86AE40FFE47072D8B3209DE5C22E8E4544441506629715、screenshot SHA=4CFF8863068629E431823861FF3BD5078AAB990D89A4BEE7B9BBC31036515DDD、LCP=448ms / TTI=0.052s、baseline SSIM=1.0、HTML 同一 SHA）
  - `observability/policy/ci_evidence.jsonl` に 11:01:37 / 11:02:09 の `ui_audit_executed` / `ui_gate_pass_ja|en` を追記（coverage_updated: 2025/11/17 16:47:42 / line_coverage=0.03864 は UI Gate より前の時刻）

## 直近で完了した項目
1. preview 生成（`artifacts/preview/index.html` + README）を整備。
2. UI-Audit（Playwright + axe + WebVitals、日本語ビュー）を再実行し、serious=0 を確認。
3. Gate=PASS に更新し、`summary.json` の `gate.pass=true` を確認（JA/EN 両ビュー）。
4. `ci_evidence.jsonl` に最新 SHA と `ui_gate_pass_ja` / `ui_gate_pass_en` を追記。
5. 統合受信箱ソートメニュー日本語化（新しい順/古い順/送信者順）と戻りリンクの言語伝搬を完了。

## 次のマイルストーン
- **Phase 2A (データモデル/マイグレーション)**  
  - missions/task_groups/tasks/artifacts/knowledge を追加し、マイグレーション＋ ER 差分を `plans/diff-plan.json` に記録。
- **Phase 2B (WorkflowEngine/self-heal)**  
  - SequentialWorkflow と self-heal フックを実装し、workflow_runs と ci_evidence にトレースを残す。
- **Phase 2C (Manager UI)**  
  - Mission 一覧／TaskGroup タイムライン／Artifact タイルを Manager View に実装し、Playwright で検証。
- **Phase 2D (CLI 接続 / Knowledge/Inbox/Graph 計画)**  
  - v1 は SequentialWorkflow＋簡易並列、Windows/PS7＋ConPTY、初期サポート CLI（CodexCLI＋Claude Code CLI）のみを対象とし、DAG/AsyncThink/WSL+tmux などは Phase 3 以降の拡張とする。Artifact promote→Knowledge、Inbox スレッド化、Graph View は Phase 3。
  - CLI call 成功時に cli_runs の run_id/path を echo 済み（2025-12-02、wrapper pytest 4 passed）。
- **Auto Gate v1（Phase 2B〜2C で完了想定）**  
  - `auto_gate_rules.yaml` で UI Gate / SBOM / secret-scan / bandit / GitOps ゲートを判定し、CI で `auto_gate_decider.py` が run/skip/force_run を決定する。  
  - 判定結果を `event=auto_gate_decision` として `observability/policy/ci_evidence.jsonl` に記録する。判定失敗時は全て実行し、理由を記録する。  
  - `plans/diff-plan.json` と APPROVALS/SafeOps/LOCK はルールに該当する差分がある PR で必須とし、未更新なら CI fail とする。
  - 2025-11-28 現在: auto_gate_decider で UI Gate は `skip`（no_ui_affecting_files）判定。UI Gate の再実行は保留中（差分なし）。
- **Council PoC v1 (CLI/正確性のみ)**  
  - 生成プロファイル=creative/concise/code、fact_checker で正確性スコア（0–10）、議長が最高スコア回答を採用＋講評。  
  - 匿名化（プロファイル名/自己紹介/挨拶除去、ですます統一、順序シャッフル）、timeout=60s、再試行なし。  
  - ci_evidence に `council_run`（question_hash、run_id、scores:{accuracy} 等）を追記し、artifacts/council/<run_id>/ を保存。
- **運用タスク**  
  - docs/operations/handover_recovery_checklist.md の PASS 維持、nightly UI-Audit 監視、週次 preview 差分レポート。

## 参照ドキュメント
- `docs/multi_agent_terminal_checklist_v2.md`
- `docs/operations/handover_recovery_checklist.md`

## 備考
- すべて UTF-8 / LF・Plan→Test→Patch を順守し、SafeOps ログと SHA 記録を欠かさない。
- preview_dir 不備や UI 予算超過時は即時に Blocker を掲示し、ci_evidence へ記録する（`houkokuzenbun.txt` はユーザーのみが記載し、AI は触れない）。
### 追加マイルストン（UI Breadcrumb/i18n）
- 導入範囲拡張: 統合受信箱／プロジェクト／Inbox／Compose にBreadcrumb適用
- 監査合格: 日本語ビューで `nav[aria-label="Breadcrumb"]`・`aria-current="page"`・リンクへの `?lang` 伝搬を確認、UI Gate PASS維持
- Runner整備: DOM/スクリーンのピン留めと Evidence 追記（`ci_evidence.jsonl`）
