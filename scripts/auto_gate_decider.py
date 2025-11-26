"""Auto Gate の実行可否を判定し、ci_evidence に記録するユーティリティ。"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime
from fnmatch import fnmatch
from pathlib import Path
from typing import Iterable, Sequence

import yaml

ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = ROOT / "auto_gate_rules.yaml"
EVIDENCE_PATH = ROOT / "observability" / "policy" / "ci_evidence.jsonl"


def load_rules(path: Path = RULES_PATH) -> dict:
    """YAML ルールを読み込む。"""
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def get_changed_files(base: str | None, head: str | None) -> list[str]:
    """base...head の変更ファイル一覧を取得する。取得できない場合は空を返す。"""
    resolved_head = head or os.environ.get("GITHUB_SHA") or "HEAD"
    resolved_base = base or os.environ.get("GITHUB_BASE_REF")
    if not resolved_base:
        resolved_base = f"{resolved_head}~1"

    try:
        result = subprocess.check_output(
            ["git", "diff", "--name-only", f"{resolved_base}...{resolved_head}"],
            text=True,
        )
        return [line.strip() for line in result.splitlines() if line.strip()]
    except subprocess.CalledProcessError:
        return []


def match_any(path: str, patterns: Sequence[str]) -> bool:
    """パターンのいずれかに一致するか判定する。"""
    return any(fnmatch(path, pattern) for pattern in patterns)


def label_set() -> set[str]:
    """PR ラベルを環境変数から取得する。"""
    labels_env = os.environ.get("GITHUB_PR_LABELS", "")
    return {label.strip() for label in labels_env.split(",") if label.strip()}


def normalize_branch(ref: str | None) -> str:
    """refs/heads/main -> main のように正規化する。"""
    if not ref:
        return ""
    if ref.startswith("refs/heads/"):
        return ref.split("/", 2)[-1]
    return ref


def base_branch_name() -> str:
    """ベースブランチ名を環境から取得し正規化する。"""
    return normalize_branch(os.environ.get("GITHUB_BASE_REF"))


def head_ref_name() -> str:
    """HEAD 参照名を環境から取得し正規化する。"""
    return normalize_branch(
        os.environ.get("GITHUB_HEAD_REF") or os.environ.get("GITHUB_REF")
    )


def is_tag_ref() -> bool:
    """タグビルドかどうかを判定する。"""
    ref = os.environ.get("GITHUB_REF") or ""
    return ref.startswith("refs/tags/")


def decide_ui_gate(rules: dict, files: Sequence[str], branch: str, num_files: int, global_max: int | None) -> tuple[str, str]:
    """UI Gate の実行可否を決定する。"""
    component_max = rules.get("max_files_force_run")
    threshold = component_max or global_max
    if threshold and num_files > threshold:
        return "force_run", f"too_many_files({num_files})>={threshold}"

    for pattern in rules.get("always_on_branches", []):
        if branch and fnmatch(branch, pattern):
            return "run", f"branch_matches:{pattern}"

    labels = label_set()
    for label in rules.get("labels_any", []):
        if label in labels:
            return "run", f"label_matches:{label}"

    for file in files:
        if match_any(file, rules.get("paths_any", [])):
            return "run", f"matched_paths:{file}"

    return "skip", "no_ui_affecting_files"


def decide_sbom(rules: dict, files: Sequence[str], branch: str, num_files: int, global_max: int | None) -> tuple[str, str]:
    """SBOM の実行可否を決定する。"""
    threshold = global_max
    if threshold and num_files > threshold:
        return "force_run", f"too_many_files({num_files})>={threshold}"

    if branch and branch in rules.get("always_on_branches", []):
        return "run", f"branch_matches:{branch}"
    # CI 側でタグやスケジュールイベントのときに CI_ALWAYS_RUN_SBOM=1 を渡す想定
    if is_tag_ref() or os.environ.get("CI_ALWAYS_RUN_SBOM") == "1":
        return "run", "forced_by_event"

    dep_files = rules.get("dep_files", [])
    for file in files:
        if match_any(file, dep_files):
            return "run", f"dependency_file_changed:{file}"
    return "skip", "no_dependency_change"


def decide_secret_scan(rules: dict, files: Sequence[str], num_files: int, global_max: int | None) -> tuple[str, str]:
    """secret-scan の実行可否を決定する。デフォルトは実行。"""
    threshold = global_max
    if threshold and num_files > threshold:
        return "force_run", f"too_many_files({num_files})>={threshold}"

    targets = rules.get("paths_any", [])
    if not files:
        return "run", "no_diff_default_run"
    if any(match_any(file, targets) for file in files):
        return "run", "matched_paths"
    return "run", "default_full_scan"


def decide_bandit(rules: dict, files: Sequence[str], num_files: int, global_max: int | None) -> tuple[str, str]:
    """bandit の実行可否を決定する。"""
    threshold = global_max
    if threshold and num_files > threshold:
        return "force_run", f"too_many_files({num_files})>={threshold}"

    targets = rules.get("paths_any", [])
    if any(match_any(file, targets) for file in files):
        return "run", "python_diff_detected"
    return "skip", "no_python_change"


def decide_gitops(rules: dict, files: Sequence[str], num_files: int, global_max: int | None, component: str) -> tuple[str, str]:
    """GitOps 系ファイル更新の必須判定。"""
    threshold = global_max
    if threshold and num_files > threshold:
        return "force_run", f"too_many_files({num_files})>={threshold}"

    targets = rules.get("requires_update_if_paths_any", [])
    for file in files:
        if match_any(file, targets):
            return "run", f"requires_update:{file}"
    return "skip", "no_target_paths"


def write_evidence(component: str, decision: str, reason: str, base: str, head: str) -> None:
    """auto_gate_decision イベントを evidence に追記する。"""
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    pr_number = os.environ.get("PR_NUMBER")
    branch = head_ref_name()
    event = {
        "ts": ts,
        "event": "auto_gate_decision",
        "component": component,
        "decision": decision,
        "reason": reason,
        "base": base,
        "head": head,
        "branch": branch,
        "pr_number": pr_number,
    }
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with EVIDENCE_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")


def emit_outputs(decisions: dict[str, tuple[str, str]]) -> None:
    """GitHub Actions 互換の出力を行う。"""
    env_map = {
        "ui_gate": "AUTO_GATE_UI",
        "sbom": "AUTO_GATE_SBOM",
        "secret_scan": "AUTO_GATE_SECRET_SCAN",
        "bandit": "AUTO_GATE_BANDIT",
        "gitops_plan": "AUTO_GATE_GITOPS_PLAN",
        "gitops_approvals": "AUTO_GATE_GITOPS_APPROVALS",
    }
    lines = []
    for component, (decision, _) in decisions.items():
        env_name = env_map[component]
        os.environ[env_name] = decision
        lines.append(f"{env_name}={decision}")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with Path(github_output).open("a", encoding="utf-8") as fh:
            for line in lines:
                fh.write(line + "\n")
    else:
        for line in lines:
            print(line)


def main() -> None:
    parser = argparse.ArgumentParser(description="Auto Gate 判定スクリプト")
    parser.add_argument("--base", help="比較元のブランチ/コミット")
    parser.add_argument("--head", help="比較先のブランチ/コミット")
    args = parser.parse_args()

    base = args.base or os.environ.get("GITHUB_BASE_REF") or ""
    head = args.head or os.environ.get("GITHUB_SHA") or "HEAD"

    try:
        rules = load_rules()
        files = get_changed_files(base, head)
        num_files = len(files)
        branch = head_ref_name()
        global_max = (rules.get("global") or {}).get("max_files_force_run")

        decisions: dict[str, tuple[str, str]] = {}

        decisions["ui_gate"] = decide_ui_gate(
            rules["ui_gate"], files, branch, num_files, global_max
        )
        decisions["sbom"] = decide_sbom(
            rules["sbom"], files, branch, num_files, global_max
        )
        decisions["secret_scan"] = decide_secret_scan(
            rules["secret_scan"], files, num_files, global_max
        )
        decisions["bandit"] = decide_bandit(
            rules["bandit"], files, num_files, global_max
        )
        decisions["gitops_plan"] = decide_gitops(
            rules["gitops_plan"], files, num_files, global_max, "gitops_plan"
        )
        decisions["gitops_approvals"] = decide_gitops(
            rules["gitops_approvals"], files, num_files, global_max, "gitops_approvals"
        )

    except Exception as exc:  # pragma: no cover - フェイルセーフ
        msg = f"fallback_error:{type(exc).__name__}:{exc}"
        decisions = {
            "ui_gate": ("force_run", msg),
            "sbom": ("force_run", msg),
            "secret_scan": ("force_run", msg),
            "bandit": ("force_run", msg),
            "gitops_plan": ("force_run", msg),
            "gitops_approvals": ("force_run", msg),
        }

    for component, (decision, reason) in decisions.items():
        write_evidence(component, decision, reason, base, head)

    emit_outputs(decisions)


if __name__ == "__main__":
    main()
