version: 6
name: "project_rules"
product: "Trae"
role: "Single source of truth for automated PLAN→TEST→PATCH→PROMOTION→RELEASE with strict safety, verifiable evidence, and agent orchestration"
language: "English"
persona: "Synthetic and precise"

ssot:
  canonical_file: ".trae/rules/project_rules.yaml"
  mirrors: ["docs/project_rules.md"]
  md_sync_rule: "YAML is canonical; MD mirrors via CI; manual edits to MD are rejected"

principles:
  priority_order: ["safety","accuracy","reproducibility","speed","brevity"]
  style: ["concise","declarative","no small talk","no speculation"]
  determinism: {seed: 42, venv_enforced: true}
  change_policy: "Dry-Run by default; -Apply required to write; minimal unified diff only; full-file replacement forbidden"
  quotes_policy: {max_words_per_source: 25, summarize_instead_of_copy: true}
  visibility: "Every gate emits machine-verifiable artifacts and human-verifiable visuals"

context:
  workspace_root: "C:\\Users\\User\\Trae\\ORCH-Next"
  encoding: "UTF-8"
  eol: "LF"                        # "*.bat" only CRLF
  windows_paths: {absolute_required: true, separator: "\\", forbid: ["relative","..","/"]}
  paths:
    logs_dir:          "data/logs/current/"
    audit_dir:         "data/logs/current/audit/"
    safeops_rule_bootstrap_log: "data/logs/current/audit/rule_bootstrap.jsonl"
    safeops_rule_bootstrap_hash: "data/logs/current/audit/rule_bootstrap.sha256"
    safeops_dangerous_log: "data/logs/current/audit/dangerous_command_events.jsonl"
    locks_dir:         "data/locks/"
    artifacts_root:    "artifacts/"
    dashboards_dir:    "observability/dashboard/"
    coverage_dir:      "observability/coverage/"
    junit_dir:         "observability/junit/"
    policy_dir:        "observability/policy/"
    sbom_dir:          "observability/sbom/"
    provenance_dir:    "observability/provenance/"
    screenshots_dir:   "observability/ui/screens/"
    traces_dir:        "observability/ui/traces/"
    reports_dir:       "observability/ui/report/"
    sandbox_root:      ".sandbox/"
    backups_dir:       "backups/"
    approvals_ledger:  "APPROVALS.md"
    review_checklist:  "ORCH/STATE/CHECKLISTS/<task_id>.md"
  io_formats_in:  ["code","markdown","yaml","json"]
  io_formats_out: ["patch","json","yaml","html","png"]

specs:                         # required agent specs
  work_rules:        {file: ".trae/rules/WORK_rules.yaml",         min_version: 2}
  orchestrator:      {file: ".trae/rules/MCP-Orchestrator.yaml"}
  design_ui:         {file: ".trae/rules/Design-UI.yaml"}
  web_verify:        {file: ".trae/rules/Web-Verify.yaml"}
  audit_rules:       {file: ".trae/rules/AUDIT_rules.yaml"}
  approvals:         {file: ".trae/rules/APPROVALS.yaml"}
  cmd:               {file: ".trae/rules/CMD.yaml"}
  git_ops:           {file: ".trae/rules/codexcli_git_ops_policy.md"}
  agent_spec_shared: {file: ".trae/rules/Agent Spec.yaml"}

tools:
  python: ".\\.venv\\Scripts\\python.exe"
  pip: ".\\.venv\\Scripts\\python.exe -m pip"
  formatting: ["black","isort"]
  typing: ["mypy"]
  test: ["pytest","pytest-cov"]
  coverage_diff: ["diff-cover"]
  security: ["detect-secrets","bandit"]
  ui_audit: ["playwright","axe-core","visual-diff"]
  sbom: ["syft","cyclonedx"]
  signing: ["cosign"]
  doc: ["pandoc"]

adoption_and_enablement:       # adoption accelerators
  pr_template: ".github/pull_request_template.md"
  issue_template: ".github/ISSUE_TEMPLATE/change_request.md"
  policy_bot:
    enabled: true
    comments:
      - "Gate status grid (PASS/FAIL)"
      - "Coverage diff vs thresholds"
      - "License/Vulnerability delta"
      - "UI screenshots and audit badges"
  dashboards:
    index: "observability/dashboard/index.html"
    tiles:
      - {id: "gates",      source: "observability/policy/ci_evidence.jsonl", viz: "status-grid"}
      - {id: "coverage",   source: "observability/coverage/summary.json",    viz: "bar"}
      - {id: "perf_p95",   source: "observability/bench/perf.json",          viz: "line"}
      - {id: "security",   source: "observability/vuln_scan.json",           viz: "badges"}
      - {id: "sbom",       source: "observability/sbom/manifest.spdx.json",  viz: "table"}
      - {id: "ui_screens", source: "observability/ui/screens/",              viz: "gallery"}
  rituals:
    weekly_review: "Top violations & fixes"
    monthly_drill: "Rollback & Freeze tabletop"

governance:
  approvals_required: true
  codeowners_required: true
  forbid_self_approval: true
  change_window: ["Mon-Fri 10:00-17:00 JST"]
  freeze_flag: ".trae/RELEASE_FREEZE"
  kill_switch: ".trae/disable_autostart"
  waivers:                        # time-bounded exceptions
    dir: ".trae/waivers/"
    required_fields: ["id","rule","justification","owner","mitigations","approver","expiry"]
    max_expiry_days: 14
    approver_roles: ["Security","Platform","Product"]
    min_approvers: 2
    audit_log: "observability/policy/waivers.jsonl"

agents:
  registry:
    orchestrator: "MCP-Orchestrator"
    verify:       "Web-Verify"
    design:       "Design-UI"
    ui_audit:     "UI-Audit"
    audit:        "AUDIT"
    cmd:          "CMD"
  routing:
    - {match: "contains(figma|shadcn|component|design)", delegate: "Design-UI",      mode: "design"}
    - {match: "contains(verify|source|news|latest|today|pdf)", delegate: "Web-Verify", mode: "verify"}
    - {match: "contains(ui-audit|axe|playwright|visual|lcp|tti|cls)", delegate: "UI-Audit", mode: "ui_audit"}
    - {match: "preview_dir present", delegate: "UI-Audit", mode: "ui_audit"}
    - {match: "default", delegate: "MCP-Orchestrator", mode: "auto"}
  contracts:
    cmd_accepts_status: ["OK","INCONCLUSIVE","DENIED","ERROR"]
    design_ui_handoff:  "artifacts/design_ui/"
    ui_audit_handoff:   "artifacts/audit_handoff.json"
    verify_sources_out: "observability/policy/sources.json"
    approvals_ledger:   "APPROVALS.md"

language_routing:
  goal: "Use Python or Go per workload to hit SLOs while preserving determinism"
  choices:
    - name: "python_gateway"
      prefer_for: ["rapid iteration","ml-evaluation","glue"]
      oracle: true
    - name: "go_service"
      prefer_for: ["high RPS","low p95","static binaries"]
      require_oracle_parity: true
  parity_tests:
    golden_dir: "tests/golden/"
    requirement: "Go output equals Python oracle output (diff==0) for the same inputs"

pipeline:                       # enforced gates
  order: ["WORK:LOCK","PLAN","TEST","APPROVALS","PATCH","PROMOTION","RELEASE"]
  gates:

    WORK:LOCK:
      spec: ".trae/rules/WORK_rules.yaml"
      require:
        - "Lock acquired or two-person steal with ledger update"
        - "State in {LOCKED, PLAN}"
      ui_change_rules:
        evidence_required: true
        artifacts:
          - "artifacts/<task_id>/ui/desktop.png"
          - "artifacts/<task_id>/ui/mobile.png"
          - "artifacts/<task_id>/ui/axe_report.json"
          - "artifacts/<task_id>/ui/baseline/"
          - "artifacts/<task_id>/ui/visual_diff/"
        manual_verification: {field: "manual_verified: YES", signed_by: true, checklist_path: true}

    PLAN:
      outputs:
        - "PLAN.json {scope, minimal_diff, impacted_files, risks, rollback}"
        - "backups/pre_change/<task_id>/manifest.sha256"
      rules:
        - "Emit dry-run patch proposal only"
        - "Record safeops.rule_bootstrap hashes/log entries before executing destructive commands or CLI Apply."
        - "If UI/templates/assets touched → set ui_preview_required=true"

    TEST:
      run:
        - "black --check && isort --check-only"
        - "mypy (progressive_strict)"
        - "pytest -q"
        - "diff-cover thresholds for added/changed lines"
        - "detect-secrets + bandit"
        - "SBOM generate → sbom_dir"
      thresholds:
        coverage_min:      {unit: 0.85, integration: 0.75, e2e: 0.70}
        diff_coverage_min: {added_lines: 0.85, changed_lines: 0.80}
        vulnerabilities_max: {high: 0, critical: 0}
        perf_p95_sec: 2.0
      ui_required_if_flag:
        screenshots:           ["desktop.png","mobile.png"]
        axe_serious_plus_max:  0
        visual_diff_pct_max:   0.10
        cls_max:               0.10
        lcp_s_max:             2.5
        tti_s_max:             3.0
      outputs:
        - "TEST_REPORT.json"
        - "artifacts/<task_id>/ui/baseline/  # if UI"

    APPROVALS:
      ledger: "APPROVALS.md"
      roles:  ["CMD","AUDIT"]
      two_person_rule:      true
      forbid_self_approval: true
      required_fields: ["id","owner","scope","status","signed_by","ts_utc","manual_verification","expiry_utc"]
      ui_manual_verification:
        required_if: "UI/UX affected"
        fields: ["manual_verified: YES","signed_by","ts_utc","checklist_path"]
      codeowners_required: true

    PATCH:
      policy: "Dry-Run default; require -Apply to write"
      write_flow: "*.tmp → validate → *.bak → rename"
      post_verify: ["EOL=LF (except *.bat)", "SHA256(in/out)", "SafeOps logs+hash refreshed before Apply"]
      forbid: ["full-file replacement","writes outside workspace_root"]
      on_failure: "auto-rollback; state=ROLLED_BACK; root-cause logged"
      idempotency_check: "Two consecutive PATCH runs with no content change must yield identical SHA256"

    PROMOTION:
      actions:
        - "Publish junit & coverage summaries → dashboards_dir"
        - "Generate provenance attestation → provenance_dir"
        - "Cosign verify SBOM + artifacts"
        - "Policy-bot posts gate grid, coverage diff, license/vuln delta, UI badges"
      outputs:
        - "observability/policy/ci_evidence.jsonl"
        - "observability/provenance/attestation.json"

    RELEASE:                   # Blue/Green + SLO-driven freeze
      strategy: "blue_green"
      canary:
        traffic_pct: 10
        window_sec: 300
        require: ["success_rate≥0.995","p95≤pipeline.gates.TEST.thresholds.perf_p95_sec"]
      on_slo_breach: "auto-rollback + set freeze_flag"
      flags:
        freeze_flag: ".trae/RELEASE_FREEZE"
        kill_switch: ".trae/disable_autostart"

compliance_and_supply_chain:    # automated audits
  sbom_required:       true
  provenance_required: true
  signatures:
    signer:        "cosign"
    verify_on_read: true
  license_policy:
    allowlist: ["MIT","BSD-2-Clause","BSD-3-Clause","Apache-2.0"]
    denylist:  ["AGPL-3.0-only","AGPL-3.0-or-later","GPL-3.0-only","GPL-3.0-or-later"]
    action_if_violation: "block_release"
  vulnerability_policy:
    thresholds:   {high: 0, critical: 0}
    evidence_file: "observability/vuln_scan.json"
  ui_evidence:
    screenshots_dir: "observability/ui/screens/"
    traces_dir:      "observability/ui/traces/"
    reports_dir:     "observability/ui/report/"
    required_when:   "templates|static|front-end|dashboard changes"
    budgets: {lcp_s: 2.5, tti_s: 3.0, cls_max: 0.10, visual_diff_pct: 0.10, axe_serious_plus_max: 0}

security_and_privacy:
  secrets_placeholders: ["REDACTED","CHANGEME","jwt-ci","webhook-ci"]
  tokens_in_outputs:    false
  pii_allowed:          false
  network:
    allowed_http_methods: ["GET","HEAD"]
    forbid_post_unless:   ["signed_webhook_to_internal_ci"]

observability:
  logs: ["structured_json"]
  metrics:
    - "p95_latency_s"
    - "tool_fail_rate"
    - "coverage_unit"
    - "coverage_integration"
    - "coverage_e2e"
    - "diff_coverage_added"
    - "diff_coverage_changed"
    - "vuln_count_high"
    - "vuln_count_critical"
    - "a11y_serious_plus"
    - "visual_diff_pct"
    - "cls"
    - "lcp_s"
    - "tti_s"
  retention_days: 30
  notifications:
    channels: ["slack:#release-notify","email:ops@company.local"]
    on_events: ["gate_failed","auto_rollback","freeze_on","release_published","waiver_applied","ui_audit_failed"]
  dashboards:
    index: "observability/dashboard/index.html"
    publish_on: ["PROMOTION","RELEASE"]
    tiles_ref: "@adoption_and_enablement.dashboards.tiles"

automation:
  schedules:
    - id: "weekly-figma-scan"
      cron: "0 3 * * 1"
      action:
        delegate: "Design-UI"
        inputs:
          figma_ref: "team://recent"
          context: {preview: false}
    - id: "nightly-ui-audit"
      cron: "0 2 * * *"
      action:
        delegate: "UI-Audit"
        inputs:
          preview_dir: "artifacts/preview/"
          routes: ["/"]
    - id: "watch-claims"
      cron: "0 6 * * *"
      action:
        delegate: "Web-Verify"
        inputs:
          claim: "tracked claim"
          context: {run_mode: "watch", recency_days: 30}
  events:
    - on: "pull_request:opened"
      do:
        - delegate: "Web-Verify"
          inputs:
            claim: "PR description"
            context: {topic_hint: "news"}
    - on: "release:tagged"
      do:
        - delegate: "UI-Audit"
          inputs: {preview_dir: "artifacts/preview/"}
    - on: "observability:freeze_on"
      do:
        - delegate: "AUDIT"
          inputs: {task: "open_postmortem", template: "docs/postmortem.md"}
  queues:
    lanes:
      - {name: "P0", match: "contains(release|hotfix|rollback)", concurrency: 1}
      - {name: "P1", match: "contains(audit|verify|design)",     concurrency: 2}
      - {name: "P2", match: "default",                           concurrency: 3}
    backpressure: {max_queue: 50, action: "shed_P2_then_pause"}
  retries:
    policy: "exponential_backoff_jitter"
    params: {base_ms: 500, factor: 2.0, max_retries: 3, max_ms: 8000}
    idempotency_key: "sha1(task+params)"
    dedup_window_s: 600
  circuit_breaker:
    rules:
      - {tool: "Hyperbrowser",  fail_rate_pct: 40, window: "10m", action: "open_5m_then_half_open"}
      - {tool: "Brave Search",  timeout_rate_pct: 40, window: "10m", action: "reduce_concurrency"}

ci:
  required_steps:
    - "pre_commit"
    - "black"
    - "isort"
    - "flake8"
    - "mypy"
    - "pytest"
    - "diff_coverage"
    - "golden_parity"           # Python↔Go parity check
    - "sbom_generate_sign_verify"
    - "secret_scan"
    - "eol_check"
    - "bandit"
  enforce_order: true
  continue_on_mypy_error: true
  evidence_bundle: "observability/policy/ci_evidence.jsonl"
  approvals:
    required_reviewers: 2
    labels_required: ["security","release"]
    dismiss_stale_reviews: true
    linear_history: true
  branch_protection:
    required_checks:
      - "pre_commit"
      - "flake8"
      - "mypy"
      - "pytest"
      - "coverage"
      - "sbom_sign_verify"
      - "secret_scan"
      - "eol_check"
      - "pre_commit"
      - "flake8"
      - "mypy"
      - "pytest"
      - "diff_coverage"
      - "sbom_generate_sign_verify"
      - "secret_scan"
      - "eol_chec"
    required_reviews: 1
    codeowners_enforced: true
    dismiss_stale_reviews: true
    linear_history: true

acceptance_criteria:
  must:
    - "WORK_rules v2+ enforced (locks, two-person approval, UI evidence, manual verification)"
    - "PLAN.json exists with minimal diff and rollback steps"
    - "Coverage thresholds + diff-cover thresholds met"
    - "SBOM + provenance generated; cosign verify passed"
    - "License denylist violations blocked; vuln thresholds met"
    - "EOL=LF verified; *.bat=CRLF; atomic write SHA256(in/out) logged"
    - "If UI affected: screenshots + axe report + visual diff + manual verification signed"
    - "CODEOWNERS non-author review present; APPROVALS two-person where required"
    - "Policy-bot comments posted; dashboards updated; overview.html published"
    - "SafeOps rule_bootstrap hash manifest and dangerous command log entries captured with matching approvals"
    - "Git operations (edit/test/commit/push/PR) follow codexcli_git_ops_policy.md (MODE + REMOTE_WRITE_ALLOWED + audit Status gates)"
    - "Python↔Go parity tests pass (golden diff==0) where applicable"
    - "Two consecutive PATCH runs with no content change produce identical SHA256"
  must_not:
    - "Full-file replacement"
    - "Edits outside workspace_root"
    - "Secrets in repo/logs"
    - "Virtual-only UI claims without observable evidence"

final_checks:
  - "All referenced spec files exist and parse"
  - "SafeOps logs/hash (paths.safeops_rule_bootstrap_log/hash, paths.safeops_dangerous_log) include current task entry"
  - "Routing delegates produce artifacts at declared handoff paths"
  - "Blue/Green canary + SLO freeze configured and verifiable"
  - "Waiver flow exists, time-bounded, and logged"
  - "MD mirror synchronized by CI"
