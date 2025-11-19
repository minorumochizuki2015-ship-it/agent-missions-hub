# リポジトリ直下配置ルール（FILE RULE）

本ドキュメントは Codex-CLImutipule のルートディレクトリ構成と、追加資産を配置する際のルールを定義します。新規参加者は最初に本書と `docs/operations/handover_recovery_checklist.md` を確認し、作業前に環境を把握してください。

## ルートディレクトリ一覧と用途
| パス | 用途 | 備考 |
|---|---|---|
| `.claude`, `.codex`, `.mcp.json` など | MCP/エージェント設定 | 変更時は `cmd報告書-AUDIT.txt` に記録 |
| `.github/` | CI/CD 設定 | ワークフローの追加・修正時は diff-plan 更新必須 |
| `AGENTS.md` | ガイドライン（日本語） | ルール変更は必ず diff-plan に反映 |
| `docs/` | 仕様・運用ドキュメント | `docs/operations/` に Runbook とチェックリストを格納 |
| `src/` | アプリケーション本体 | モジュール単位で 300 行以下を目安 |
| `tests/` | テストコード | pytest 基準。1 ファイル 300 行以内 |
| `scripts/` | 運用スクリプト | PowerShell は Dry-Run→Apply→検証のテンプレ実装を徹底 |
| `tools/` | 監視・補助ツール | 生成物は `observability/` 配下に出力 |
| `observability/` | ログ・指標アーカイブ | Dashboards など人が参照する成果物を配置 |
| `backups/` | バックアップ保存領域 | 取得時は README 記載手順に従う |
| `screenshots/` | UI 監査スクリーンショット | `pending/`, `archive/` など用途別に整理 |
| `reports/` | 報告ログの集約 | `work/`（作業）、`audit/`（監査）、`test/`（テスト）に分類 |
| `plans/` | 計画ファイル | `diff-plan.json` 等の計画・ステータス管理を配置 |
| `tmp/` | 暫定データ | 評価済みのモックやサンプルのみ格納。定期的に見直す |
| `third_party_docs/` | 参考資料 | 更新時は出典（URL/バージョン）を追記 |
| `cmd報告書-*.txt`, `AUIDIT監査報告.txt` | 報告ログ | すべての実行結果・ハッシュをここに追記（現状は `reports/` 配下へ移行） |

## 追加/変更時のルール
1. **ディレクトリ作成**: 新規ディレクトリは用途を `docs/operations/root_structure_filerule.md` に追記し、`diff-plan.json` で承認フローを管理する。
2. **ファイル作成**: ルート直下にファイルを追加する場合は、目的と更新手順を必ず日本語で記載した README かドキュメントを同時に用意する。
3. **命名規則**: スネークケースまたはケバブケースを用い、意味のない省略を避ける。ログ類は `YYYYMMDD_HHMMSS` 形式を使用。
4. **禁止事項**: `backup`, `logs`, `output` などの大容量フォルダをルート直下に増やさない。必ず上記表にある既存領域を活用する。

## 新規参加者が最初に行う確認
1. `AGENTS.md` と本ドキュメントを読み、変更禁止事項を理解する。
2. `cmd報告書-AUDIT.txt` / `cmd報告書-WORKー.txt` を確認し、未完了タスクと最新ハッシュを把握する。
3. `diff-plan.json` を参照して現在進行中の計画を把握する。
4. `.venv\Scripts\python.exe -m pytest -q --maxfail=1` を Dry-Run (実行せずコマンド確認) で指差し確認し、依存の有無をチェックする。

## 既存ファイルの整理指針
- 不要資産を見つけても **勝手に削除しない**。`diff-plan.json` に検討タスクを追加し、ユーザーの明確な承認を得ること。
- 暫定的なメモや作業ログは `tmp/` か `docs/operations/` のワークスペースに整理し、放置しない。

## 更新手順の記録
- 本ファイルを更新した場合は、更新内容とハッシュを `cmd報告書-AUDIT.txt` に追記する。
- 変更に伴うスクリプトやドキュメント更新は、必ず Dry-Run→Apply→確認の順で行い、証跡（ログ・スクリーンショット）を `observability/` または `backups/` に保管する。
