# REPORT_DRAFT (M4 観測系整備・2025-10-27)

## 作業概要
- OpenTelemetry Collector 用設定ファイルを追加し、トレース・メトリクス・ログの受信と出力先を統一した構成に整理。
- Collector 起動状況を JSONL で記録し、設定適用の証跡を確保。
- 観測系ログ格納ディレクトリを新設し、Collector 出力ファイルの保存場所を明示。

## 設定ファイル
- OpenTelemetry 設定: `C:\Users\User\Trae\ORCH-Next\projects\\Codex-CLImutipule\observability\config\otel_config.yaml`

## 生成・更新した証跡
- Collector ブートストラップログ: `C:\Users\User\Trae\ORCH-Next\projects\\Codex-CLImutipule\workspaces\shared\governingcore_v5_slice\data\logs\current\observability\otel_collector_bootstrap.jsonl`
- Collector 出力予定ファイル: `C:\Users\User\Trae\ORCH-Next\projects\\Codex-CLImutipule\workspaces\shared\governingcore_v5_slice\data\logs\current\observability\otel_collector_output.jsonl`

### 取得済みテレメトリ例
- トレース: `governance_request` span（latency_ms=245.3）
- メトリクス: `cpu_usage_pct`（18.7%）
- ログ: `Collector heartbeat`（pipeline=metrics, batch_size=128）

### アラート閾値案（案）
- CPU 使用率平均 > 70% が 5 分継続 → WARNING
- latency_ms > 500 かつ 3 リクエスト連続 → WARNING
- hallucination_risk > 0.1 が 5 分継続 → CRITICAL
- Collector heartbeat 欠落が 60 秒超 → CRITICAL

## 今後のアクション
1. Collector を起動し、`otel_collector_output.jsonl` にトレース／メトリクス／ログが蓄積されることを確認。
2. Prometheus 9100/TCP のスクレイプ対象が正常に応答するか監視し、アラートルールの草案を本閾値案に沿って具体化。
3. Checklist M4 とマイルストーンを継続更新し、観測系の残タスク（ダッシュボード整備・自動アラート配信）を進める。
4. UI証跡の同期（`artifacts/ui_audit/summary.json` の SHA/ts と Web Vitals を最新化）および `reports/ci_evidence.jsonl` のイベント追記。
5. 非同期ハング対策の進捗を記録し、pytest subset の成功ログと失敗時スタックを `reports/test/` に保管したうえで段階的にフルスイートへ復帰。
6. coverage/diff-cover の更新結果（最新 run の line-rate と diff 率）を監視し、80% 到達時のみ `observability/coverage/ci_phase7_evidence.jsonl` に記録。

