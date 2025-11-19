# テストカバレッジ向上計画 v1（目標90%）

更新日時: 2025-11-08T06:49:00Z
現状: 全体≈23%（storage単体≈38%）
目標: 段階的に 50%→70%→90%

## 戦略（Plan→Test→Patch）
- フェーズ1（→50%）
  - storageの優先強化：画像境界・巨大画像・非画像バイト・破損画像・トレーラ解析の網羅
  - utils/guard/config の単体テスト追加（純粋関数・I/O最小依存）
  - HTTP系はタイムアウト除外で安全サブセットに限定（pytest-timeout導入済み）
- フェーズ2（→70%）
  - models/db の制約テスト（型・必須項目・不正値）
  - llmブリッジの環境変数分岐テスト（ダミー環境で副作用ゼロ）
  - CLI ヘルパーのエラーパス・ガード導入の検証
- フェーズ3（→90%）
  - HTTPミドルウェアの統合テスト（モック・ローカルサーバ、ネットワークI/O最小化）
  - 例外系・境界値・並行パス（AsyncFileLock）
  - property-based（Hypothesis）でストレージ入力の多様性テスト

## 優先テスト（storage）
- 巨大画像→file選択の一貫性
- 非画像バイト列→安全にスキップ/メタ記録
- 破損画像（PIL例外）→例外の健全化と処理結果
- INLINE_IMAGE_MAX_BYTES 境界（0/最小/最大）
- KEEP_ORIGINAL_IMAGES=true 時のoriginal_path記録
- convert_markdown=False 時のメタ記録（inline/file）

## 実施/証跡
- pytestを安全サブセットで継続（reports/test/** に保存）
- coverage.xml と coverage_summary.json を更新し、ci_evidence.jsonl へSHA追記
- すべてUTF-8/LF・最小差分を徹底

## ロールバック/可用性
- テスト追加は小刻み・最小パッチ、失敗時は直前版へロールバック可能

## 成功基準
- 各フェーズの達成率と主要モジュールの≥80%を目安に、最終的に全体≥90%