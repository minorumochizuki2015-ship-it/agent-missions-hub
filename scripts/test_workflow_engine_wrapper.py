"""pytest の出力をファイルへリダイレクトして flush エラーを回避するラッパー。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    """workflow_engine 向けの pytest をファイル出力で実行する。"""
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "tests/test_workflow_engine.py",
        "--maxfail=1",
        "--disable-warnings",
    ]
    out_path = Path("pytest_workflow_engine.out.txt")
    with out_path.open("w", encoding="utf-8") as fp:
        proc = subprocess.Popen(cmd, stdout=fp, stderr=subprocess.STDOUT)
        return proc.wait()


if __name__ == "__main__":
    raise SystemExit(main())
