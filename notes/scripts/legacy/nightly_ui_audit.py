from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence
from urllib.error import URLError
from urllib.request import Request, urlopen

CI_EVIDENCE_PATH = Path("observability/policy/ci_evidence.jsonl")
PREVIEW_HTML_DEFAULT = Path("artifacts/preview/index.html")
REPORT_DIR_DEFAULT = Path("reports/work")
HTML_CAPTURE_PATH = Path("artifacts/ui_audit/html/route_unified_inbox.html")
SCREENSHOT_PATH = Path("artifacts/ui_audit/screens/unified_inbox.png")
SUMMARY_PATH = Path("artifacts/ui_audit/summary.json")


@dataclass
class DiffResult:
    """各言語の UI-Audit 実行と差分情報を保持する."""

    lang: str
    summary: dict[str, object]
    summary_path: Path
    html_path: Path
    screenshot_path: Path
    diff_text: str
    diff_exists: bool
    diff_lines: int


def parse_args() -> argparse.Namespace:
    """コマンドライン引数を解析する."""
    parser = argparse.ArgumentParser(description="Nightly UI-Audit を実行し証跡・差分レポートを作成するユーティリティ")
    parser.add_argument(
        "--langs",
        nargs="+",
        default=["ja", "en"],
        help="UI_AUDIT_LANG の実行順序。省略時は ja -> en。",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("UI_AUDIT_HOST", "127.0.0.1"),
        help="UI_AUDIT_HOST の上書き値。",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("UI_AUDIT_PORT", "8765")),
        help="UI_AUDIT_PORT の上書き値。",
    )
    parser.add_argument(
        "--preview-html",
        type=Path,
        default=PREVIEW_HTML_DEFAULT,
        help="差分比較に用いる preview HTML パス。",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=REPORT_DIR_DEFAULT,
        help="nightly preview 差分レポートを保存するディレクトリ。",
    )
    parser.add_argument(
        "--jira-webhook",
        default=os.environ.get("JIRA_WEBHOOK_URL", ""),
        help="差分検出時に通知する Jira Webhook URL（未設定ならスキップ）。",
    )
    return parser.parse_args()


def sha256_path(path: Path) -> str:
    """ファイルの SHA256 を算出する."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def write_text_atomic(path: Path, content: str) -> None:
    """テキストファイルを Atomic に保存する."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    bak = path.with_suffix(path.suffix + ".bak")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tmp.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    if path.exists():
        if bak.exists():
            bak.unlink()
        existing = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        with bak.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(existing)
    tmp.replace(path)


def copy_binary_atomic(src: Path, dest: Path) -> None:
    """バイナリファイルを Atomic にコピーする."""
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    bak = dest.with_suffix(dest.suffix + ".bak")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with src.open("rb") as reader, tmp.open("wb") as writer:
        shutil.copyfileobj(reader, writer)
    if dest.exists():
        if bak.exists():
            bak.unlink()
        with dest.open("rb") as reader, bak.open("wb") as writer:
            shutil.copyfileobj(reader, writer)
    tmp.replace(dest)


def append_ci_evidence(
    event: str, files: list[dict[str, str]], status: str, note: str, metrics: dict[str, object] | None = None
) -> None:
    """ci_evidence.jsonl にイベントを追記する."""
    CI_EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "ts": datetime.now(timezone.utc).strftime("%Y/%m/%d %H:%M:%S"),
        "event": event,
        "files": files,
        "status": status,
        "note": note,
    }
    if metrics is not None:
        payload["metrics"] = metrics
    with CI_EVIDENCE_PATH.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def load_summary(path: Path) -> dict[str, object]:
    """UI-Audit summary.json を読み込む."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("summary.json が辞書形式ではありません")
    return data


def run_ui_audit(lang: str, host: str, port: int) -> dict[str, object]:
    """指定言語の UI-Audit を実行し summary を返す."""
    env = os.environ.copy()
    env["UI_AUDIT_LANG"] = lang
    env["UI_AUDIT_HOST"] = host
    env["UI_AUDIT_PORT"] = str(port)
    cmd = [sys.executable, "scripts/ui_audit_run.py"]
    print(f"[Nightly] UI-Audit start lang={lang}")
    result = subprocess.run(cmd, env=env, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"UI-Audit lang={lang} が失敗しました (exit={result.returncode})")
    summary = load_summary(Path("artifacts/ui_audit/summary.json"))
    return summary


def snapshot_artifacts(lang: str) -> tuple[Path, Path, Path]:
    """UI-Audit 実行結果を言語別ファイルとしてスナップショットする."""
    if not HTML_CAPTURE_PATH.exists():
        raise FileNotFoundError(f"{HTML_CAPTURE_PATH} が存在しません")
    html_copy = HTML_CAPTURE_PATH.with_name(f"route_unified_inbox_{lang}.html")
    html_text = HTML_CAPTURE_PATH.read_text(encoding="utf-8").replace("\r\n", "\n")
    write_text_atomic(html_copy, html_text)
    if not SCREENSHOT_PATH.exists():
        raise FileNotFoundError(f"{SCREENSHOT_PATH} が存在しません")
    screenshot_copy = SCREENSHOT_PATH.with_name(f"unified_inbox_{lang}.png")
    copy_binary_atomic(SCREENSHOT_PATH, screenshot_copy)
    if not SUMMARY_PATH.exists():
        raise FileNotFoundError(f"{SUMMARY_PATH} が存在しません")
    summary_copy = SUMMARY_PATH.with_name(f"summary_{lang}.json")
    summary_text = SUMMARY_PATH.read_text(encoding="utf-8").replace("\r\n", "\n")
    write_text_atomic(summary_copy, summary_text)
    return html_copy, screenshot_copy, summary_copy


def build_diff(preview_html: Path, target_html: Path, lang: str) -> tuple[str, bool, int]:
    """preview と実際の HTML の差分文字列を生成する."""
    preview_lines = preview_html.read_text(encoding="utf-8").splitlines()
    target_lines = target_html.read_text(encoding="utf-8").splitlines()
    diff_lines = list(
        difflib.unified_diff(
            preview_lines,
            target_lines,
            fromfile=f"preview[{preview_html.name}]",
            tofile=f"actual[{lang}]",
            lineterm="",
        )
    )
    diff_text = "\n".join(diff_lines)
    effective = any(line and line[0] in {"+", "-"} and not line.startswith(("+++", "---")) for line in diff_lines)
    delta_lines = sum(
        1 for line in diff_lines if line and line[0] in {"+", "-"} and not line.startswith(("+++", "---"))
    )
    return diff_text, effective, delta_lines


def create_report(results: Sequence[DiffResult], preview_html: Path, report_dir: Path) -> Path:
    """Nightly preview 差分レポートを生成する."""
    ts = datetime.now(timezone.utc)
    slug = ts.strftime("%Y%m%d")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"nightly_preview_diff_{slug}.md"
    lines: list[str] = [
        f"# Nightly Preview Diff ({ts.isoformat()})",
        "",
        f"- Preview HTML: `{preview_html}` (SHA256={sha256_path(preview_html)})",
        f"- Languages: {', '.join(r.lang for r in results)}",
        "",
    ]
    for result in results:
        gate = result.summary.get("gate", {})
        gate_pass = isinstance(gate, dict) and bool(gate.get("pass"))
        web_vitals = gate.get("budgets") if isinstance(gate, dict) else {}
        lines.append(f"## 言語 `{result.lang}`")
        lines.append(f"- gate.pass: `{gate_pass}`")
        if isinstance(web_vitals, dict):
            budget_flags = ", ".join(f"{k}={'OK' if v else 'NG'}" for k, v in web_vitals.items())
            lines.append(f"- Budgets: {budget_flags}")
        lines.append(f"- Summary: `{result.summary_path}` (SHA256={sha256_path(result.summary_path)})")
        lines.append(f"- HTML: `{result.html_path}` (SHA256={sha256_path(result.html_path)})")
        lines.append(f"- Screenshot: `{result.screenshot_path}` (SHA256={sha256_path(result.screenshot_path)})")
        lines.append(f"- Diff status: {'差分あり' if result.diff_exists else '差分なし'} ({result.diff_lines} 行)")
        lines.append("")
        lines.append("```diff")
        lines.append(result.diff_text if result.diff_text else "(差分なし)")
        lines.append("```")
        lines.append("")
    write_text_atomic(report_path, "\n".join(lines) + "\n")
    return report_path


def post_jira_if_needed(webhook: str, results: Sequence[DiffResult], report_path: Path) -> None:
    """差分検出時に Jira Webhook へ通知する."""
    if not webhook.strip():
        print("[Nightly] Jira Webhook 未設定のため通知をスキップします")
        return
    diff_targets = [r for r in results if r.diff_exists]
    if not diff_targets:
        print("[Nightly] 差分なしのため Jira 通知は行いません")
        return
    payload = {
        "summary": f"Nightly UI preview diff detected ({datetime.now(timezone.utc).isoformat()})",
        "description": (
            "Nightly UI-Audit が preview と実際の DOM に差分を検出しました。"
            f"\nReport: {report_path}"
            + "\n"
            + "\n".join(
                f"- lang={item.lang}, diff_lines={item.diff_lines}, html={item.html_path}" for item in diff_targets
            )
        ),
        "labels": ["ui-audit", "nightly", "preview-diff"],
    }
    req = Request(
        webhook.strip(),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(req, timeout=20) as resp:
            resp.read()
        print(f"[Nightly] Jira Webhook 通知を送信しました ({len(diff_targets)} 言語)")
    except URLError as exc:
        print(f"[Nightly] Jira Webhook 通知に失敗しました: {exc}")


def build_ci_evidence_records(results: Sequence[DiffResult], preview_html: Path) -> None:
    """差分結果を ci_evidence.jsonl へ記録する."""
    for result in results:
        files = [
            {"path": str(preview_html), "sha256": sha256_path(preview_html)},
            {"path": str(result.summary_path), "sha256": sha256_path(result.summary_path)},
            {"path": str(result.html_path), "sha256": sha256_path(result.html_path)},
            {"path": str(result.screenshot_path), "sha256": sha256_path(result.screenshot_path)},
        ]
        status = "diff" if result.diff_exists else "match"
        note = f"lang={result.lang} diff_lines={result.diff_lines}"
        append_ci_evidence(
            "nightly_preview_diff",
            files,
            status=status,
            note=note,
            metrics={
                "diff_lines": result.diff_lines,
                "diff_exists": result.diff_exists,
                "lang": result.lang,
                "gate": result.summary.get("gate"),
                "web_vitals": result.summary.get("web_vitals"),
            },
        )


def main() -> None:
    """Nightly UI-Audit 自動化のエントリーポイント."""
    args = parse_args()
    preview_html = args.preview_html
    if not preview_html.exists():
        raise FileNotFoundError(f"preview HTML が存在しません: {preview_html}")

    results: list[DiffResult] = []
    for lang in args.langs:
        lang_code = lang.lower()
        summary = run_ui_audit(lang_code, args.host, args.port)
        html_copy, screenshot_copy, summary_copy = snapshot_artifacts(lang_code)
        diff_text, diff_exists, diff_lines = build_diff(preview_html, html_copy, lang_code)
        results.append(
            DiffResult(
                lang=lang_code,
                summary=summary,
                summary_path=summary_copy,
                html_path=html_copy,
                screenshot_path=screenshot_copy,
                diff_text=diff_text,
                diff_exists=diff_exists,
                diff_lines=diff_lines,
            )
        )

    report_path = create_report(results, preview_html, args.report_dir)
    build_ci_evidence_records(results, preview_html)
    post_jira_if_needed(args.jira_webhook, results, report_path)
    print(f"[Nightly] 差分レポートを生成しました: {report_path}")


if __name__ == "__main__":
    main()
