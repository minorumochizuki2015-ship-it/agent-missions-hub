"""SafeOps ヘルパーの自動承認判定を検証する。"""

from __future__ import annotations

from orchestrator.safeops import should_auto_approve_dangerous


def test_should_auto_approve_manual_variants() -> None:
    """manual/空/None は常に False になることを確認する。"""
    for level in (None, "", "manual", " MANUAL "):
        assert not should_auto_approve_dangerous(
            "dummy", "mission", automation_level=level
        )


def test_should_auto_approve_future_values_placeholder() -> None:
    """auto-safeops/auto-all など将来値でも現状は False を返す。"""
    for level in ("auto-safeops", "auto-all", "unknown"):
        assert not should_auto_approve_dangerous(
            "dummy", "mission", automation_level=level
        )
