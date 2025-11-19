# Llama サーバー運用手順（18080/18081）

## 目的
- Codex-CLImutipule 環境で llama_cpp.server をポート 18080 / 18081 に常駐させる。
- `tools/monitoring/validate_ports.py` で /v1/models を監視し、健全性ログを取得する。

## 前提条件
- 仮想環境: `C:\Users\User\Trae\ORCH-Next\.venv\Scripts\python.exe`
- モデル: `workspaces/shared/governingcore_v5_slice/models/qwen2-7b-instruct-q4_k_m.gguf`

## 手順
1. サーバー起動
   ```powershell
   cd C:\Users\User\Trae\ORCH-Next\projects\Codex-CLImutipule
   .\scripts\start_llama_servers.ps1 -Ports 18080,18081 -CheckEndpoint
   ```
   - 起動ログ: `data/logs/current/monitoring/server_18080_stdout.log` / `server_18080_stderr.log`（18081 も同様）。
2. 健全性確認
   ```powershell
   .\.venv\Scripts\python.exe tools/monitoring/validate_ports.py --ports 18080 18081 --output-dir data/logs/current/monitoring/api_models_test.json
   ```
   - 例: `api_models_20251102_145719.json`（SHA256=a1678e2b5f07836b4043d115a3b24f01ec04b14c8156980a84b153535b61ec4c）。
3. 停止
   - `Ctrl+C` で停止、または別コンソールから `Get-Process -Name python | Where-Object { $_.Path -like '*Codex-CLImutipule*.venv*' } | Stop-Process -Force`。

## 運用メモ
- 旧ポート (8080/8081/38080) は使用禁止とする。
- 監視ログは `data/logs/current/monitoring/` 以下に時刻付きで保存する。
- ポート競合は `data/logs/current/audit/port_conflict_events.jsonl` を参照。
