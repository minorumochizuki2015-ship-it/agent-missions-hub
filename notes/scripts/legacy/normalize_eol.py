from __future__ import annotations

import os
import subprocess
from pathlib import Path

EXCLUDE_DIRS = {".git", ".venv", "node_modules", "tmp", "__pycache__"}
TEXT_EXTS = {".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".jsonl", ".md", ".toml", ".yaml", ".yml", ".ini", ".env", ".html", ".txt", ".bak_init", ".bak_auto", ".bak_doc", ".bak_mailbox", ".example"}
ALLOWLIST_NAMES = {"Dockerfile", "Makefile", ".envrc"}


def _ls_tracked(root: Path) -> list[Path]:
    try:
        out = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True, check=False)
        if out.returncode == 0:
            paths = [root / p for p in out.stdout.splitlines() if p.strip()]
            return [p for p in paths if (p.suffix.lower() in TEXT_EXTS) or (p.name in ALLOWLIST_NAMES)]
    except Exception:
        pass
    results: list[Path] = []
    for dirpath, _, filenames in os.walk(root):
        parts = Path(dirpath).parts
        if any(seg in EXCLUDE_DIRS for seg in parts):
            continue
        for fn in filenames:
            p = Path(dirpath) / fn
            if (p.suffix.lower() in TEXT_EXTS) or (p.name in ALLOWLIST_NAMES):
                results.append(p)
    return results


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    files = _ls_tracked(root)
    total = 0
    changed = 0
    for p in files:
        total += 1
        try:
            data = p.read_bytes()
        except Exception:
            continue
        text = data.decode("utf-8", errors="ignore")
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        if normalized != text:
            p.write_bytes(normalized.encode("utf-8"))
            changed += 1
    report_dir = root / "observability" / "policy"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "normalize_eol_report_current.txt"
    lines = [
        f"files_scanned={total}",
        f"files_changed={changed}",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(str(report_path))


if __name__ == "__main__":
    main()
