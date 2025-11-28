from scripts.shadow_audit_emit import emit_event, verify_chain


def test_emit_updates_chain(tmp_path):
    root = tmp_path / "shadow"
    first = emit_event(
        {
            "ts": "2025-01-01T00:00:00Z",
            "actor": "WORK",
            "event": "PLAN",
            "rule_ids": [],
            "policy_refs": [],
            "reasoning_digest": "a",
            "inputs_hash": "in1",
            "outputs_hash": "out1",
            "approval_state": "none",
            "approvals_row_id": "",
        },
        root,
    )
    second = emit_event(
        {
            "ts": "2025-01-01T00:00:01Z",
            "actor": "WORK",
            "event": "TEST",
            "rule_ids": [],
            "policy_refs": [],
            "reasoning_digest": "b",
            "inputs_hash": "in2",
            "outputs_hash": "out2",
            "approval_state": "none",
            "approvals_row_id": "",
        },
        root,
    )
    assert first != second
    assert verify_chain(root)
