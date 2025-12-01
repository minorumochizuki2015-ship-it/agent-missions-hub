# ハンドオーバー / 復旧チェックリスト (SSOT)

このドキュメントは SafeOps / UI Gate / Builder Report / runner の復旧手順をまとめた唯一の参照点です。
全作業は **Plan → Test → Patch** を守り、保存時は **UTF-8 + LF** を徹底してください。
**注意**: `houkokuzenbun.txt` はユーザー専用の手入力ログです。AI は参照・追記を行わず、必要な場合はユーザーへ更新依頼のみ伝えます。

## 1. 初動確認
1. `plans/plan_diff.json` を参照し、タスク状態 (Pending / Blocked / Completed) が最新であることを確認する（ローカル版は未運用のため不要）。
2. `TRAE SOLO Builder Report*.txt` の記述が runner ログと SHA 証跡に整合しているか確認する。`houkokuzenbun.txt` はユーザー管理ファイルのため存在のみチェックし、内容へは触れない。
3. UI Gate: `artifacts/ui_audit/summary.json` の `gate.pass` が **true** (ts=2025/11/17 10:12:00 JST, script=ui-audit-v2) であることを確認し、`FAIL` 時は checklist / diff-plan を Blocked に戻す。
4. CI エビデンス: `observability/policy/ci_evidence.jsonl` に最新テストの SHA・coverage・runner ログが追記されているか検証する。
5. SafeOps KPI: `observability/policy/safeops_kpi.json` の `system_health_score` が閾値以上で `status != warning` になっているか確認する。
6. 危険コマンド: `data/logs/current/audit/dangerous_command_events.jsonl` に Approver ID とコマンド本文が残っているか確認する。
7. Runner ログ: `data/logs/current/runner/runner_*.jsonl` の `cwd` が **C:\Users\User\Trae\Codex-CLImutupule-CMD** で統一されていること。
8. TMP/TEMP SSOT (PowerShell プロファイル) の内容と実環境変数を突き合わせる。

## 2. TMP/TEMP 再マップ (SSOT)
- 設定ファイル: `C:\Users\User\Documents\PowerShell\Microsoft.PowerShell_profile.ps1`
- 必須設定 (変更禁止):
  ```powershell
  $env:TMP  = 'C:\Users\User\Trae\Codex-CLImutupule-CMD\tmp'
  $env:TEMP = $env:TMP
  $env:Path = 'C:\Users\User\Trae\Codex-CLImutupule-CMD\.venv\Scripts;' + $env:Path
  ```
- 検証手順:
  1. `Get-Content $PROFILE` で上記 3 行が存在することを確認。
  2. 新しい PowerShell セッションで `Write-Host $env:TMP` / `$env:TEMP` が repo 内 `tmp` を指すことを確認。
  3. `python scripts/runner.py -- python --version` を実行し、`data/logs/current/runner/*.jsonl` の `environ.TMP/TEMP` が repo `tmp` を示すことを確認。
  4. `artifacts/SAFEOPS-*/sha256_hashes.log` まで SHA を残したら、以降の `houkokuzenbun.txt` 追記はユーザーへ依頼する。

## 3. リポジトリ状態確認
- `python scripts/runner.py -- git status -sb` を Dry-Run で実行し、意図しない変更が無いか確認。
- ステージングや削除時は `RUNNER_ALLOW_GIT_WRITE=1` / `RUNNER_ALLOW_DELETE=1` を付け、runner ログに証跡を残す。
- クリーン系コマンドは `python scripts/runner.py -- git clean -ndX` → (ユーザーが `houkokuzenbun.txt` に承認記録) → 本実行の順。
- `docs/operations/root_structure_filerule.md` に定義されたライト制限へ違反していないか再確認する。

## 4. Runner 運用
1. **全コマンド**を `python scripts/runner.py -- <command>` で実行する。
2. 代表例:
   - `python scripts/runner.py --profile medium -- .\.venv\Scripts\python.exe -m pytest -q tests/test_http_logging_and_errors.py --cov=mcp_agent_mail.http`
   - `python scripts/runner.py -- pnpm run ui:audit`（Node/pnpm が無い場合: `python scripts/runner.py -- .\.venv\Scripts\python.exe scripts/ui_audit_run.py`）
   - `python scripts/runner.py -- node scripts/ci/append_ci_evidence.js --output observability/policy/ci_evidence.jsonl`
3. 実行結果は以下 4 箇所に必ず保存する:
   - `data/logs/current/runner/runner_<timestamp>.jsonl`
   - `observability/policy/ci_evidence.jsonl`（コマンド・SHA・coverage）
   - `artifacts/SAFEOPS-YYYYMMDD/sha256_hashes.log`
   - （ユーザー作業）`houkokuzenbun.txt` への手入力
4. UI Gate 再検証フロー:
   1. `python scripts/runner.py -- pnpm run ui:audit`（または `.\\.venv\Scripts\python.exe scripts/ui_audit_run.py`）
   2. `python scripts/runner.py -- .\.venv\Scripts\python.exe -m pytest -q tests/test_ui_gate.py`
   3. `python scripts/runner.py -- node scripts/ci/append_ci_evidence.js --output observability/policy/ci_evidence.jsonl`
   4. `artifacts/ui_audit/summary.json` と `ci_evidence.jsonl` の SHA を確認し Gate=PASS を証明。ユーザーには `houkokuzenbun.txt` への記載を依頼する。
5. TMP/TEMP の Dry-Run → Apply → 検証ログを `data/logs/current/runner/` に残し、`houkokuzenbun.txt` へはユーザーが追記する。
6. UI 日本語監査後は `python scripts/runner.py -- .\.venv\Scripts\python.exe scripts/runner_validation.py --event ui_gate_pass_ja` を実行し、DOM/スクリーン/summary の SHA・SafeOps/Runner/ユーザー手動ログ・Checklist/Milestone「更新日時」がすべて同期していることを自動検証する（失敗時は Gate を Blocked に戻す）。

## 5. バックアップ / 証跡
1. `backups/` に diff-plan・cmd報告書・ci evidence をまとめた最新スナップショットを保存。
2. `scripts/mail_lightning_audit.py` で取得したログは `data/logs/current/` と `observability/` へ格納。
3. 重要ファイル (plan_diff、checklist、README 等) を更新したら `plans/plan_diff.json` の該当項目を更新する。
4. `TRAE SOLO Builder Report.txt` は runner コマンドと対応 SHA を記録し、`houkokuzenbun.txt` での共有はユーザーへ依頼する。

## 6. レポート更新
- `TRAE SOLO Builder Report.txt`: Gate 結果・危険コマンド・SafeOps KPI・coverage を runner ログとセットで記載。
- `houkokuzenbun.txt`: ユーザーのみが追記する。AI は「更新依頼済み」である旨を別途報告すればよい。
- `cmd報告書.txt`: SHA256 を記録し、UTF-8 (LF) で保存。
- `python scripts/runner.py -- git diff --stat` を用いて差分が Plan と一致しているか確認し、逸脱した場合は即座に中断して報告。

## 7. 連絡 / エスカレーション
- 連絡先: #safeops / #ui-audit / #runner-support (Slack)。
- Gate BLOCKER や SafeOps KPI warning が継続した場合は 30 分以内にエスカレーション。
- Trae SOLO へ依頼するのは「こちらで実作業できないタスクのみ」。それ以外は本リポで完遂する。
### UI Breadcrumb / 言語伝搬 確認（日本語ビュー）
1. `http://127.0.0.1:8765/mail/unified-inbox?lang=ja` を開く
2. `nav[aria-label="Breadcrumb"]` の存在と `ol/li` 構造を確認
3. 末尾項目に `aria-current="page"` が付与されていること
4. パンくずリンクへ `?lang=ja` が伝搬することを確認（Home/Projects/Project/Back to Project）
5. 統合受信箱のソートメニュー（新しい順/古い順/送信者順）と一括操作（既読にする/クリア）が日本語表示であること
6. RunnerでDOM/スクリーンを取得し `observability/policy/ci_evidence.jsonl` へリンクを追加（最新実行: 2025/11/17 10:12 JST, event=`ui_gate_pass_ja`）
備考: Nightly (`nightly_preview_diff`) は朝のスナップショット時刻（例: 08:10:20）で記録し、UI Gate の最新基準時刻（例: 17:10:xx）とは用途を分離する（Nightlyは差分検知、UI Gateは最新状態の基準）。
