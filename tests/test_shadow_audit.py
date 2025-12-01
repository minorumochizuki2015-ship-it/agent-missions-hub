from pathlib import Path

import pytest

from scripts.shadow_audit_emit import emit_event, verify_chain


def _record(n: int) -> dict:
    return {
        "ts": f"2025-01-01T00:00:0{n}Z",
        "actor": "WORK",
        "event": "PLAN",
        "rule_ids": [],
        "policy_refs": [],
        "reasoning_digest": f"r{n}",
        "inputs_hash": f"in{n}",
        "outputs_hash": f"out{n}",
        "approval_state": "none",
        "approvals_row_id": "",
    }


def test_chain_appends_and_verifies(tmp_path: Path):
    root = tmp_path / "shadow"
    h1 = emit_event(_record(1), root)
    h2 = emit_event(_record(2), root)
    assert h1 != h2
    assert verify_chain(root)
    assert (root / "manifest.jsonl").read_text(encoding="utf-8").count("\n") == 1


def test_emit_no_json_error(tmp_path: Path):
    root = tmp_path / "shadow2"
    emit_event(_record(1), root, sign=False)
    emit_event(_record(2), root, sign=False)
    assert verify_chain(root)


def test_tamper_detected(tmp_path: Path):
    root = tmp_path / "shadow"
    emit_event(_record(1), root)
    emit_event(_record(2), root)
    manifest = root / "manifest.jsonl"
    manifest.write_text(
        manifest.read_text(encoding="utf-8") + "\nTAMPER", encoding="utf-8"
    )
    with pytest.raises(ValueError):
        verify_chain(root)
