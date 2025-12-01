# SafeOps Multi-Agent Rules（Dangerous Commands / Approvals）

本ルールは CLI エージェントの実行ログ・SSE ストリームから検知し、Signals（type=dangerous_command / approval_required）を生成するための基準とする。ルール更新時は Phase P2 の完了条件に「ルール定義＋テスト」を含め、CI/E2E で検証する。

## 危険コマンド（dangerous_command）
- rm -rf /, rm -rf *, del /s /q C:\*
- format, mkfs.*
- reg delete HKLM\*, reg delete HKCU\*
- chmod 777 -R, takeown /f /r
- dd if=/dev/zero of=/dev/sda, diskpart
- systemctl stop *, sc stop *, net stop *

## 外部送信（approval_required）
- curl http://*, curl https://*
- Invoke-WebRequest http://*
- wget http://*
- powershell -c "Invoke-RestMethod *"
- outbound ssh/scp/sftp

## 危険なソースコード生成/変更
- terraform apply, terraform destroy
- kubectl apply, kubectl delete
- helm install / upgrade
- docker rm -f, docker system prune -a
- git push --force, git reset --hard

## Secret/Key Access
- gcloud secrets access
- aws secretsmanager get-secret-value
- vault kv get
- ENV や .env 読み取り

---

## Phase P2 完了条件（追加）
- 本ルールセットを Signals 検知器に組み込み、
  - 危険コマンド検知テスト（regex）
  - 外部送信検知テスト
  - approval_required 状態の UI 反映
  を CI/E2E で通すこと。
