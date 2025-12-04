from __future__ import annotations

from typing import Optional


def should_auto_approve_dangerous(
    command: str,
    mission_id: Optional[str],
    *,
    automation_level: str = "manual",
) -> bool:
    """危険コマンドを自動承認すべきかどうかを判定するプレースホルダ関数。

    現時点では automation_level=manual を前提とし、常に False（自動承認しない）を返す。
    将来は WORK_rules.yaml の Dangerous command guard・Signals API・APPROVALS.md を参照し、
    automation_level（manual / auto-safeops / auto-all）に応じて分岐する実装へ差し替える。
    """
    level = (automation_level or "manual").strip().lower()
    if not level:
        level = "manual"
    # manual: 常に自動承認しない（SafeOps + APPROVALS による人間確認が前提）
    if level == "manual":
        return False
    # auto-safeops / auto-all などの将来拡張は別バッチで実装する
    return False

