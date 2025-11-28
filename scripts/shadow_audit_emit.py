from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("observability/policy/shadow_audit")
MANIFEST = ROOT / "manifest.jsonl"
CHAIN = ROOT / "manifest.sha256"
SIG = ROOT / "manifest.sig"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _atomic_write(path: Path, content: str, *, validate_jsonl: bool = False) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8", newline="\n")
    if validate_jsonl:
        for line in content.splitlines():
            if line.strip():
                json.loads(line)
    tmp.replace(path)


def _sign_manifest(manifest: Path, sig: Path, key_env: str = "COSIGN_KEY") -> str:
    cosign = shutil.which("cosign")
    if not cosign:
        return "skip:cosign_missing"
    key = os.environ.get(key_env, "")
    if not key:
        return "skip:key_missing"
    result = subprocess.run(
        [
            cosign,
            "sign-blob",
            "--yes",
            "--key",
            key,
            "--output-signature",
            str(sig),
            str(manifest),
        ],
        capture_output=True,
        text=True,
    )
    return "signed" if result.returncode == 0 else f"error:{result.returncode}"


def emit_event(record: dict, root: Path = ROOT, *, sign: bool = False) -> str:
    root.mkdir(parents=True, exist_ok=True)
    manifest = root / "manifest.jsonl"
    chain = root / "manifest.sha256"
    sig = root / "manifest.sig"
    lines: list[str] = []
    if manifest.exists():
        lines = manifest.read_text(encoding="utf-8").splitlines()
    prev = chain.read_text(encoding="utf-8").strip() if chain.exists() else ""
    new_line = json.dumps(record, ensure_ascii=False)
    new_hash = _sha256(prev + "\n" + new_line if prev else new_line)
    _atomic_write(manifest, "\n".join([*lines, new_line]), validate_jsonl=True)
    _atomic_write(chain, new_hash)
    if sign:
        _sign_manifest(manifest, sig)
    return new_hash


def verify_chain(root: Path = ROOT) -> bool:
    manifest = root / "manifest.jsonl"
    chain = root / "manifest.sha256"
    if not manifest.exists():
        return True
    lines = manifest.read_text(encoding="utf-8").splitlines()
    expected = ""
    for line in lines:
        expected = _sha256(expected + "\n" + line if expected else line)
    current = chain.read_text(encoding="utf-8").strip() if chain.exists() else ""
    if expected != current:
        raise ValueError("shadow audit hash mismatch")
    return True


def rebuild_chain(root: Path = ROOT) -> str:
    manifest = root / "manifest.jsonl"
    chain = root / "manifest.sha256"
    if not manifest.exists():
        raise FileNotFoundError("manifest.jsonl not found")
    lines = [
        ln for ln in manifest.read_text(encoding="utf-8").splitlines() if ln.strip()
    ]
    expected = ""
    for line in lines:
        expected = _sha256(expected + "\n" + line if expected else line)
    _atomic_write(chain, expected)
    return expected


if __name__ == "__main__":
    emit_event(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "actor": "WORK",
            "event": "PLAN",
            "rule_ids": [],
            "policy_refs": [],
            "reasoning_digest": "",
            "inputs_hash": "",
            "outputs_hash": "",
            "approval_state": "none",
            "approvals_row_id": "",
        }
    )
