import json
import os
import subprocess
import sys
from pathlib import Path
import shutil

try:
    import tomllib  # Python 3.11+
except Exception:  # pragma: no cover
    import tomli as tomllib  # type: ignore


def load_paths() -> dict:
    cfg_path = Path(".trae/test_paths.toml")
    if not cfg_path.exists():
        return {}
    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    return data


def check_exists(path: str) -> bool:
    p = Path(path)
    return p.exists()


def log(msg: str):
    print(msg)


def fail(msg: str):
    log(f"ERROR: {msg}")
    sys.exit(1)


def verify_assets(paths: dict) -> dict:
    ui = paths.get("ui_gate", {})
    art = paths.get("artifacts", {})
    rep = paths.get("reports", {})
    ev = paths.get("evidence", {})

    results = {
        "exists": {},
        "npm_script": None,
        "npm_available": None,
    }

    required = {
        "package_json": ui.get("package_json"),
        "pytest_file": ui.get("pytest_file"),
        "summary": art.get("summary"),
        "screens_dir": art.get("screens_dir"),
        "npm_log": rep.get("npm_log"),
        "ci_evidence": ev.get("ci_evidence"),
    }

    for k, v in required.items():
        results["exists"][k] = bool(v) and check_exists(v)

    # Check npm availability (robust on Windows)
    npm_path = shutil.which("npm") or shutil.which("npm.cmd")
    if npm_path:
        results["npm_available"] = True
    else:
        # Fallback probe via subprocess (may still fail if PATH incomplete)
        try:
            subprocess.run(["npm", "--version"], check=True, capture_output=True)
            results["npm_available"] = True
        except Exception:
            results["npm_available"] = False

    # Check npm script mapping
    pkg_path = ui.get("package_json")
    if pkg_path and check_exists(pkg_path):
        pkg = json.loads(Path(pkg_path).read_text(encoding="utf-8"))
        scripts = pkg.get("scripts", {})
        results["npm_script"] = scripts.get(ui.get("npm_script", ""))

    return results


def maybe_run_ui_gate(paths: dict) -> int:
    """Optionally run npm UI Gate to validate executability.

    Controlled by env VERIFY_RUN=1
    """
    if os.environ.get("VERIFY_RUN") != "1":
        log("VERIFY_RUN!=1: skip actual test execution")
        return 0
    script = paths.get("ui_gate", {}).get("npm_script", "test:ui-gate")
    if not script:
        fail("npm script name missing in TOML")

    # Prefer npm when available; otherwise fallback to pytest directly
    npm_path = shutil.which("npm") or shutil.which("npm.cmd")
    if npm_path:
        cmd = [npm_path, "run", script]
        log(f"Running: {' '.join(cmd)}")
        proc = subprocess.run(cmd, text=True)
        return proc.returncode
    else:
        # Fallback: run pytest UI Gate directly
        py_cmd = [sys.executable, "-m", "pytest", "tests/test_ui_gate.py", "-v", "--tb=short"]
        log(f"npm not found; fallback to pytest: {' '.join(py_cmd)}")
        proc = subprocess.run(py_cmd, text=True)
        return proc.returncode


def main():
    paths = load_paths()
    if not paths:
        fail(".trae/test_paths.toml not found or empty")

    results = verify_assets(paths)
    log(json.dumps(results, ensure_ascii=False, indent=2))

    # Append normalized evidence event for CI integrity
    try:
        ev_path = paths.get("evidence", {}).get("ci_evidence")
        if ev_path:
            payload = {
                "event": "ui_gate_assets_verified",
                "status": "ok" if all(results["exists"].values()) else "partial",
                "npm_available": results.get("npm_available"),
                "npm_script": bool(results.get("npm_script")),
            }
            with open(ev_path, "a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception as e:
        log(f"WARN: failed to append ci evidence: {e}")

    # Hard fail if core assets missing
    core_ok = results["exists"].get("package_json") and results["exists"].get("pytest_file")
    if not core_ok:
        fail("Core UI Gate assets missing (package.json or tests/test_ui_gate.py)")

    # Optional execution
    rc = maybe_run_ui_gate(paths)
    # Append success/failure event for CI clarity
    try:
        ev_path = paths.get("evidence", {}).get("ci_evidence")
        if ev_path:
            payload = {
                "event": "ui_gate_run",
                "status": "pass" if rc == 0 else "error",
                "note": "VERIFY_RUN=1 executed" if os.environ.get("VERIFY_RUN") == "1" else "VERIFY_RUN!=1 skip",
            }
            with open(ev_path, "a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception as e:
        log(f"WARN: failed to append ui_gate_run evidence: {e}")
    if rc != 0:
        fail(f"npm UI Gate run failed with code {rc}")

    log("verify_ui_gate_assets: OK")


if __name__ == "__main__":
    main()