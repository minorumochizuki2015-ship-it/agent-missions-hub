# Mail / LightningStore 監査手順（Codex-CLImutipule）

## 目的
- LightningStore の task_id と Mail アーカイブの thread_id を照合し、監査証跡とハッシュ値を確実に保全する。
- 再監査指示を受領した際の Dry-Run→Apply→確認を標準化し、再発を防止する。

## 前提条件
- 仮想環境: `C:\Users\User\Trae\ORCH-Next\.venv\Scripts\python.exe`
- LightningStore エクスポート: `workspaces/shared/governingcore_v5_slice/data/lightning_store_export.json`（実データ受領時に更新）
- Mail アーカイブ: `mcp_agent_mail/threads/*.md`（`thread-id:` 行を含む）
- 出力先: `data/logs/current/audit/` に `mail_lightning_audit_YYYYMMDD_HHMMSS.log`

## 手順
1. **入力確認（Dry-Run）**
   ```powershell
   C:\Users\User\Trae\ORCH-Next\.venv\Scripts\python.exe scripts/mail_lightning_audit.py --help
   ```
   - 必要引数（`--store-json`, `--mail-root`, `--output`）を確認し、欠落がないことを検証する。
2. **監査実行（Apply）**
   ```powershell
   cd C:\Users\User\Trae\ORCH-Next\projects\Codex-CLImutipule
   $ts = Get-Date -Format 'yyyyMMdd_HHmmss'
   $log = "data/logs/current/audit/mail_lightning_audit_$ts.log"
   .\.venv\Scripts\python.exe scripts/mail_lightning_audit.py `
       --store-json workspaces/shared/governingcore_v5_slice/data/lightning_store_export.json `
      --mail-root mcp_agent_mail `
       --output $log
   ```
3. **結果検証**
   ```powershell
   Get-FileHash -Algorithm SHA256 $log
   ```
   - `thread_id` が 0 件でないこと、および LightningStore task_id と Mail thread_id の件数が一致することを確認する。
   - 参考例: `mail_lightning_audit_20251103_003248.log`（SHA256=fa6a254c4e88f2e98e0fa5d4042f1f90594ca5288988093b8f68fa1c45c2a455）。
4. **報告**
   - `cmd報告書.txt` に実行時刻・ログパス・SHA256 を記載し、AUDIT 指示へ回答する。
   - 本手順書の更新日を併記し、再監査時の参照バージョンを明確化する。
5. **アーカイブ整理**
   - `mail_lightning_audit_20251102_210146.log` など旧ログは「旧環境アーカイブ」と明記して保管する。
   - 監査ログとハッシュを一覧管理する `data/logs/current/audit/manifest_mail_lightning.csv` を整備予定。

## 再発防止メモ
- Mail アーカイブ未展開のまま実行すると `thread_id=0` となるため、手順1を必須チェックとする。
- 実行前後の `mcp_agent_mail/threads` の件数・更新日時を記録し、差分を追跡する。
- LightningStore 実データ受領後は JSONL span 取得と自動化スクリプト（Dry-Run→Apply→検証→manifest 更新）を次タスクとする。

更新履歴
- 2025-11-06: 現在のリポジトリ `C:\Users\User\Trae\Codex-CLImutipule-CMD` における監査ログ出力先を `data/logs/current/audit/` に統一。手順本体の既存パス（ORCH-Next系）は参照用途のため残置し、差分検証時に併記する。
