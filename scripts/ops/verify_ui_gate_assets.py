from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


DEFAULT_PATHS: Dict[str, str] = {
    "package_json": "package.json",
    "pytest_file": "tests/test_ui_gate.py",
    "npm_script": "test:ui-gate",
    "ci_evidence": "observability/policy/ci_evidence.jsonl",
}


def load_paths() -> Dict[str, str]:
    """`.trae/test_paths.toml` があれば上書きし、なければ既定パスを返す。"""
    paths = dict(DEFAULT_PATHS)
    cfg = Path(".trae/test_paths.toml")
    if not cfg.exists():
        return paths
    data = tomllib.loads(cfg.read_text(encoding="utf-8"))
    ui_gate = data.get("ui_gate") or {}
    evidence = data.get("evidence") or {}
    if isinstance(ui_gate, dict):
        paths["package_json"] = ui_gate.get("package_json", paths["package_json"])
        paths["pytest_file"] = ui_gate.get("pytest_file", paths["pytest_file"])
        paths["npm_script"] = ui_gate.get("npm_script", paths["npm_script"])
    if isinstance(evidence, dict):
        paths["ci_evidence"] = evidence.get("ci_evidence", paths["ci_evidence"])
    return paths


def log(message: str) -> None:
    """標準出力にシンプルなログを出す。"""
    print(message)


def append_evidence(ci_evidence: Path, payload: dict) -> None:
    """ci_evidence が存在すればイベントを追記する。"""
    if not ci_evidence.exists():
        return
    with ci_evidence.open("a", encoding="utf-8", newline="\n") as fp:
        fp.write(json.dumps(payload, ensure_ascii=False) + "\n")


def ensure_assets(paths: Dict[str, str]) -> Dict[str, bool]:
    """必須アセットの存在を確認する。"""
    required = {
        "package_json": Path(paths["package_json"]).exists(),
        "pytest_file": Path(paths["pytest_file"]).exists(),
    }
    return required


def check_npm_available() -> bool:
    """npm が呼び出せるか確認する。"""
    npm_path = shutil.which("npm") or shutil.which("npm.cmd")
    if npm_path:
        return True
    try:
        subprocess.run(["npm", "--version"], check=True, capture_output=True)
        return True
    except Exception:
        return False


def maybe_run_ui_gate(paths: Dict[str, str]) -> int:
    """VERIFY_RUN=1 のときのみ UI Gate を実行する。"""
    if os.environ.get("VERIFY_RUN") != "1":
        log("VERIFY_RUN!=1: 実行をスキップ")
        return 0
    script_name = paths["npm_script"]
    npm_path = shutil.which("npm") or shutil.which("npm.cmd")
    if npm_path:
        cmd = [npm_path, "run", script_name]
        log(f"Running: {' '.join(cmd)}")
        proc = subprocess.run(cmd, text=True)
        return proc.returncode
    py_cmd = [sys.executable, "-m", "pytest", paths["pytest_file"], "-v", "--tb=short"]
    log(f"npm not found; fallback to pytest: {' '.join(py_cmd)}")
    proc = subprocess.run(py_cmd, text=True)
    return proc.returncode


def main() -> int:
    """UI Gate アセットの存在確認と（必要に応じて）実行を行う。"""
    paths = load_paths()
    exists = ensure_assets(paths)
    npm_available = check_npm_available()

    result = {
        "exists": exists,
        "npm_available": npm_available,
        "npm_script": paths["npm_script"],
    }
    log(json.dumps(result, ensure_ascii=False, indent=2))

    ci_evidence_path = Path(paths["ci_evidence"])
    append_evidence(
        ci_evidence_path,
        {
            "event": "ui_gate_assets_verified",
            "status": "ok" if all(exists.values()) else "missing",
            "npm_available": npm_available,
        },
    )

    if not all(exists.values()):
        log("ERROR: 必須アセットが不足しています")
        return 1

    rc = maybe_run_ui_gate(paths)
    append_evidence(
        ci_evidence_path,
        {
            "event": "ui_gate_run",
            "status": "pass" if rc == 0 else "error",
            "note": "VERIFY_RUN=1 executed" if os.environ.get("VERIFY_RUN") == "1" else "VERIFY_RUN!=1 skip",
        },
    )
    if rc != 0:
        return rc

    log("verify_ui_gate_assets: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
