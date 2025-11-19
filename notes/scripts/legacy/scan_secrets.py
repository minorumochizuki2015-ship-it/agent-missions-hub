from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable

ALLOWLIST = {"REDACTED", "CHANGEME", "jwt-ci", "webhook-ci"}

PATTERNS: dict[str, re.Pattern[str]] = {
    "pem_key": re.compile(r"-----BEGIN (?:RSA|DSA|EC|PRIVATE) KEY-----"),
    "aws_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "long_hex": re.compile(r"\b[0-9a-fA-F]{40,}\b"),
    "base64": re.compile(r"\b[A-Za-z0-9+/]{40,}={0,2}\b"),
    "kv_secret": re.compile(r"(?i)(api_?key|secret|token|password)\s*[:=]\s*['\"][^'\"]{12,}['\"]"),
}

EXCLUDE_DIRS = {".git", ".venv", "node_modules", "tmp", "__pycache__"}
TEXT_EXTS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".md",
    ".toml",
    ".yaml",
    ".yml",
    ".ini",
    ".env",
}


def _ls_tracked(root: Path) -> list[Path]:
    try:
        out = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True, check=False)
        if out.returncode == 0:
            paths = [root / p for p in out.stdout.splitlines() if p.strip()]
            return [p for p in paths if p.suffix.lower() in TEXT_EXTS]
    except Exception:
        pass
    results: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        parts = Path(dirpath).parts
        if any(seg in EXCLUDE_DIRS for seg in parts):
            continue
        for fn in filenames:
            p = Path(dirpath) / fn
            if p.suffix.lower() in TEXT_EXTS:
                results.append(p)
    return results


def _mask(value: str) -> str:
    return "***" if value and value not in ALLOWLIST else value


def _scan_file(path: Path) -> Iterable[dict[str, Any]]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    findings: list[dict[str, Any]] = []
    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        if any(token in line for token in ALLOWLIST):
            continue
        for name, pat in PATTERNS.items():
            for m in pat.finditer(line):
                val = m.group(0)
                if val in ALLOWLIST:
                    continue
                if name in {"long_hex", "base64"} and _is_hash_context(line):
                    continue
                # Ignore config declarations without concrete values
                if name == "kv_secret" and ("_config_value" in line or "default=\"" in line):
                    continue
                findings.append(
                    {
                        "path": path.as_posix(),
                        "line": i,
                        "type": name,
                        "snippet": line[:200],
                        "value_masked": _mask(val),
                    }
                )
    return findings


def _is_hash_context(line: str) -> bool:
    l = line.lower()
    return any(key in l for key in ("sha256", "sha1", "checksum", "hash", "digest"))

def main() -> None:
    root = Path(__file__).resolve().parents[2]
    files = []
    for p in _ls_tracked(root):
        posix = p.as_posix()
        if posix == (root / "observability/policy/detect_secrets_report_current.json").as_posix():
            continue
        if "/artifacts/" in posix or "/docs/" in posix or "/plans/" in posix:
            continue
        files.append(p)
    findings: list[dict[str, Any]] = []
    for p in files:
        findings.extend(_scan_file(p))
    report_dir = root / "observability" / "policy"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "detect_secrets_report_current.json"
    payload = {
        "violations_count": len(findings),
        "findings": findings,
    }
    report_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(str(report_path))


if __name__ == "__main__":
    main()
