# Shadow Audit 署名手順（恒久版）

## 前提
- cosign がインストール済み。
- 署名/検証の生成物（manifest.sig / manifest.sig.bundle）は Git 管理外。
- 鍵ファイルは Git 管理外の安全な場所に置く。

## 手順
1. 鍵生成（パスフレーズなしの例）
   ```
   cosign generate-key-pair
   $env:COSIGN_KEY = "$PWD\cosign.key"
   $env:COSIGN_KEY_VERIFY = "$PWD\cosign.pub"
   $env:COSIGN_PASSWORD = ""
   ```
   ※既存ファイルがある場合は上書き確認で `y`。

2. 署名（tlog無効、bundle付き）
   ```
   cosign sign-blob --tlog-upload=false --yes `
     --key $env:COSIGN_KEY `
     --output-signature observability/policy/shadow_audit/manifest.sig `
     --bundle observability/policy/shadow_audit/manifest.sig.bundle `
     observability/policy/shadow_audit/manifest.jsonl
   ```

3. 検証（trusted_root を指定）
   ```
   $root = "$env:USERPROFILE\.sigstore\root\tuf-repo-cdn.sigstore.dev\targets\trusted_root.json"
   cosign verify-blob `
     --key $env:COSIGN_KEY_VERIFY `
     --bundle observability/policy/shadow_audit/manifest.sig.bundle `
     --trusted-root $root `
     observability/policy/shadow_audit/manifest.jsonl
   ```

4. 記録
   - `observability/policy/ci_evidence.jsonl` に結果を追記（例: signed+verified、tlog_upload=false、ts）。
   - 鍵パスやパスフレーズは記載しない。

5. 後片付け
   - 鍵は Git に含めない。必要なら環境変数を `Remove-Item Env:COSIGN_*` でクリア。

## 注意
- `manifest.sig` / `.bundle` は Git に含めない（既存 .gitignore を維持）。
- tlog を無効にしているため、透明性ログが不要な場合の手順。tlog が必要な運用では `--tlog-upload` を有効にし、運用ポリシーに従うこと。
