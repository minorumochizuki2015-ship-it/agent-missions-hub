# GitHub への接続メモ（WSL 推奨設定）

WSL からの push タイムアウトを避けるため、リモートを SSH（443/tcp）に切り替え済み。

- リモート URL: `git@github.com:minorumochizuki2015-ship-it/agent-missions-hub.git`
- SSH 設定: `~/.ssh/config`
  - Host github.com / HostName ssh.github.com / Port 443 / IdentityFile `~/.ssh/id_ed25519_github`
- キー: `~/.ssh/id_ed25519_github`（権限 600、公開鍵は GitHub 登録済み）
- PAT 用 `~/.git-credentials` は未使用（HTTPS push 時のみ参照）。SSH 利用なら不要。

使い方:

```bash
# 接続確認
ssh -T git@github.com

# push
git push origin feature/mvp-ui-audit
```

PowerShell 側からも同じリモートで push 可能。***
