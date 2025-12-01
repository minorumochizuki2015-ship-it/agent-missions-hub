# UI起動・Playwright実行手順書

## 環境要件

- **Node.js**: >=18.0.0
- **Python**: 3.12+ (`.venv312/Scripts/python.exe`)
- **依存パッケージ**:
  - `@playwright/test`: ^1.40.0
  - `axe-core`: ^4.8.0
  - `Pillow`: (Python)
  - `playwright`: (Python)

---

## セットアップ

### 1. Node.js依存関係のインストール

```bash
npm install
```

### 2. Python依存関係のインストール

```bash
.\.venv312\Scripts\python.exe -m pip install playwright pillow
.\.venv312\Scripts\playwright.exe install chromium
```

---

## UI起動手順

### FastAPI HTTPサーバー起動

```bash
# 環境変数設定
$env:STORAGE_ROOT="C:\tmp\mcp-ui-test"
$env:HTTP_RBAC_ENABLED="false"
$env:HTTP_JWT_ENABLED="false"
$env:HTTP_ALLOW_LOCALHOST_UNAUTHENTICATED="true"

# サーバー起動（デフォルトポート: 8765）
.\.venv312\Scripts\python.exe -m uvicorn mcp_agent_mail.http:app --host 127.0.0.1 --port 8765 --factory
```

### UIアクセスURL

- **Unified Inbox**: `http://127.0.0.1:8765/mail/unified-inbox?lang=en`
- **Home**: `http://127.0.0.1:8765/mail?lang=en`
- **Lite版**: `http://127.0.0.1:8765/mail/unified-inbox-lite`

---

## Playwright UI Audit実行手順

### 基本実行（開発モード）

```bash
# デフォルト設定で実行
npm run ui:audit

# カスタムURL指定
npm run ui:audit:dev

# CI モード（ヘッドレス）
npm run ui:audit:ci
```

### 環境変数でカスタマイズ

```bash
# ポート変更
$env:UI_AUDIT_PORT="8766"

# 言語変更（日本語）
$env:UI_AUDIT_LANG="ja"
npm run ui:audit
```

### Python直接実行

```bash
.\.venv312\Scripts\python.exe scripts/ui_audit_run.py
```

---

## 出力ファイル

### Artifacts生成場所

```
artifacts/ui_audit/
├── summary.json          # テスト結果サマリー（Gate判定含む）
├── axe_result.json       # axe-coreのアクセシビリティ監査結果
├── screens/
│   ├── unified_inbox.png         # 最新スクリーンショット
│   └── unified_inbox.baseline.png # ベースライン比較用
└── html/
    └── route_unified_inbox.html  # HTMLダンプ

observability/policy/
└── ci_evidence.jsonl     # CI証跡ログ（UI Gate PASS/FAILイベント）
```

### summary.json構造

```json
{
  "page": "http://127.0.0.1:8765/mail/unified-inbox?lang=en",
  "timestamp": "2025/11/19 13:45:00",
  "script_version": "ui-audit-v2",
  "document": {
    "title": "Unified Inbox",
    "lang": "en"
  },
  "axe": {
    "violations": 0,
    "serious": 0,
    "by_rule": []
  },
  "web_vitals": {
    "CLS": 0.05,
    "LCP": 1200,
    "FID": 50,
    "TTI": 2.5
  },
  "visual_diff": {
    "baseline_present": true,
    "ssim": 0.98,
    "pixel_diff_ratio": 0.02
  },
  "gate": {
    "pass": true,
    "budgets": {
      "LCP_ms<=2500": true,
      "CLS<=0.1": true,
      "FID_ms<=100": true,
      "TTI_s<=5": true
    },
    "vitals_missing": false
  }
}
```

---

## UI Gate判定基準

### PASS条件（全て満たす必要あり）

1. **アクセシビリティ**: `serious/critical` 違反が0件
2. **Web Vitals予算**:
   - `LCP` <= 2500ms
   - `CLS` <= 0.1
   - `FID` <= 100ms
   - `TTI` <= 5s

### FAILの場合

- スクリプトは自動的に`/mail/unified-inbox-lite`でリトライ
- リトライでもFAILなら`gate.pass = false`

---

## pytest統合テスト

### UI Gate検証

```bash
# UI Gateテスト単体
npm run test:ui-gate

# HTTP Transportテスト
npm run test:http-transport

# 全テスト
npm run test:all
```

---

## トラブルシューティング

### ポート衝突

```bash
# ポート変更
$env:UI_AUDIT_PORT="9000"
```

### Playwright未インストール

```bash
.\.venv312\Scripts\playwright.exe install chromium
```

### Web Vitals取得失敗

- CDN (`unpkg.com`, `cdnjs.cloudflare.com`) がブロックされている場合、フォールバック実装が動作
- `summary.json` の `vitals_missing: true` を確認

### 日本語UIテスト

```bash
$env:UI_AUDIT_LANG="ja"
npm run ui:audit
```

---

## 次のステップ（STEP2_UI_SMOKE）

1. **サーバー起動**:
   ```bash
   .\.venv312\Scripts\python.exe -m uvicorn mcp_agent_mail.http:app --host 127.0.0.1 --port 8765 --factory
   ```

2. **UI Audit実行**:
   ```bash
   npm run ui:audit:dev
   ```

3. **結果確認**:
   ```bash
   Get-Content artifacts\ui_audit\summary.json | ConvertFrom-Json | Select gate
   ```

4. **Gate PASS確認**:
   - `gate.pass = true` なら STEP2_UI_SMOKE: ✅ PASS
   - `gate.pass = false` なら改善が必要

---

## 参考: package.json scripts

```json
{
  "scripts": {
    "ui:audit": "python scripts/ui_audit_run.py",
    "ui:audit:dev": "python scripts/ui_audit_run.py --url http://127.0.0.1:8766/mail/unified-inbox",
    "ui:audit:ci": "python scripts/ui_audit_run.py --url http://127.0.0.1:8766/mail/unified-inbox --ci-mode",
    "test:ui": "pytest tests/test_ui_gate.py -v",
    "test:ui-gate": "pytest tests/test_ui_gate.py -v --tb=short"
  }
}
```

---

## 証跡管理（プロジェクトルール準拠）

### CI Evidence更新

UI Audit実行時、自動的に以下が記録されます：

```jsonl
{"ts":"2025/11/19 13:45:00","event":"ui_audit_executed","files":[...]}
{"ts":"2025/11/19 13:45:05","event":"ui_gate_pass_en","status":"pass","metrics":{...}}
```

### 手動でGate状態更新

```bash
# 最新のGate状態を確認
Get-Content observability\policy\ci_evidence.jsonl | Select-String "ui_gate_pass" | Select-Object -Last 1
```
