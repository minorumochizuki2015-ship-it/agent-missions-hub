param(
    [string]$Event = "PLAN",
    [string]$Actor = "WORK",
    [string]$InputsHash = "",
    [string]$OutputsHash = "",
    [switch]$Sign
)

$repoRoot = (Resolve-Path "$PSScriptRoot/..").Path
$py = Join-Path $repoRoot ".venv\Scripts\python.exe"
$tmp = New-TemporaryFile

$signFlag = if ($Sign) { "True" } else { "False" }

$code = @"
from scripts.shadow_audit_emit import emit_event
from datetime import datetime, timezone
record = {
    "ts": datetime.now(timezone.utc).isoformat(),
    "actor": "$Actor",
    "event": "$Event",
    "rule_ids": [],
    "policy_refs": [],
    "reasoning_digest": "pshook",
    "inputs_hash": "$InputsHash",
    "outputs_hash": "$OutputsHash",
    "approval_state": "none",
    "approvals_row_id": "",
}
emit_event(record, sign=$signFlag)
"@

$code | Set-Content -Path $tmp -Encoding UTF8
& $py $tmp
Remove-Item $tmp -ErrorAction SilentlyContinue
