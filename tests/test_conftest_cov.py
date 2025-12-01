from __future__ import annotations

import os
from typing import Any

import pytest

import tests.conftest as conftest

os.environ.setdefault("TEST_ALLOWLIST_APPEND", "tests/test_conftest_cov.py")
os.environ.setdefault("ENABLE_FULL_SUITE", "0")


class _DummyItem:
    """pytest_collection_modifyitems 用の簡易ダミーアイテム。"""

    def __init__(self, nodeid: str) -> None:
        self.nodeid = nodeid
        self.markers: list[Any] = []

    def add_marker(self, marker: Any) -> None:
        self.markers.append(marker)


def _marker_reasons(markers: list[Any]) -> list[str]:
    """付与されたマーカーの reason を抽出する。"""

    reasons: list[str] = []
    for marker in markers:
        reason = getattr(marker, "kwargs", {}).get("reason")
        if reason:
            reasons.append(str(reason))
    return reasons


def test_pytest_collection_modifyitems_allow_and_deny(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """allowlist/denylist の適用で skip 理由が切り替わることを確認する。"""

    monkeypatch.delenv("ENABLE_FULL_SUITE", raising=False)
    monkeypatch.setenv("TEST_ALLOWLIST_APPEND", "tests/test_storage_lock.py")
    allow_only = _DummyItem("tests/test_workflow_engine.py::test_case")
    allow_and_deny = _DummyItem("tests/test_storage_lock.py::test_case")
    denied_default = _DummyItem("tests/test_other.py::test_case")
    conftest.pytest_collection_modifyitems(
        config=object(),
        items=[allow_only, allow_and_deny, denied_default],
    )

    assert not allow_only.markers
    reasons_allow_deny = _marker_reasons(allow_and_deny.markers)
    assert any("denylist" in reason for reason in reasons_allow_deny)
    reasons_denied_default = _marker_reasons(denied_default.markers)
    assert reasons_denied_default
