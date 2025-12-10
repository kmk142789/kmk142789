# Alignment Fabric & Governance Router

This document outlines the "policy → agent → enforcement" pipeline implemented in
`governance.alignment_fabric`. The goal is to keep the governance layer simple,
still capture how policies are mapped to capable agents, and ensure every action
leaves an auditable trace.

## Components

### PolicyCondition
- Declarative predicate evaluated against an event context.
- Helper builders are provided:
  - `attribute_match_condition` ensures a context field is in an allowed set.
  - `threshold_condition` requires a context field to be above a minimum value.
  - `expression_condition` compiles a small, safe condition language (e.g.,
    `risk_score >= 0.7 and region == "eu"`).

### EnforcementAction
- Specifies **where** a policy should be enforced via a channel name.
- Carries a payload builder so enforcement calls can be deterministic and
  traceable.
- Supports an optional `fallback_channel` when the primary channel is not
  registered.
- Optional `dynamic_callback` allows runtime mutation or enrichment of
  enforcement results before they are logged.

### Policy
- Groups conditions and actions under a policy identifier.
- Uses tags and severity to guide agent selection.
- Supports role affinity, explicit versions, inheritance from a parent policy,
  and optional timed rotations to alternate rules.
- Optional `minimum_trust` forces agent selection to respect a trust floor so
  sensitive actions are only executed by vetted actors.
- `evaluate_conditions` returns a tuple of `(passed, failures)` so callers can
  surface which predicates blocked enforcement.

### Agent & AgentMesh
- Represents a responsible actor with capabilities, tags, trust, and optional
  role, offline, service, or self-healing capabilities.
- `AgentMesh` keeps separate pools of offline agents, local service modules,
  self-healing routines, and role-specific agents so routing can happen even in
  offline-only environments.
- Router prefers mesh candidates that match policy tags/roles and then sorts by
  trust.

### GovernanceRouter
- Central orchestrator that connects policies to agents and channels.
- Hooks into the offline persistence layer for audit logs and state snapshots.
- Ships with a default `record` channel that captures enforcement payloads
  without external dependencies.
- Maintains policy versions, resolves inheritance, and enforces timed
  rotations.
- Exposes `last_route_trace`, a structured log of why policies were dispatched,
  skipped, or failed so governance authority can be audited offline.
- Emits audit log events for skipped/failed policies and snapshots the full
  trace for offline review. Utilities `load_audit_log`, `list_snapshots`, and
  `load_snapshot` are exposed from `governance` for inspection or testing.
- Provides `policy_readiness()`, which reports which policies currently have
  eligible agents (respecting trust minimums) and persists the report to
  `.offline_state/policy_readiness.json` for gap remediation.

## Example

```python
from governance import (
    Agent,
    Role,
    EnforcementAction,
    GovernanceRouter,
    Policy,
    attribute_match_condition,
    expression_condition,
    simple_payload,
)

router = GovernanceRouter()
router.register_agent(
    Agent(
        "sentinel",
        capabilities=["containment"],
        tags=["safety"],
        trust=0.9,
        kind="self-healing",
        offline_ready=True,
    )
)
router.register_role(Role("guardian", "Handles safety escalations", tags=["safety"]))

policy = Policy(
    policy_id="p-high-risk",
    description="Escalate when risk score crosses the threshold for safety-tagged events.",
    conditions=[
        attribute_match_condition("safety-tag", "tag", ["safety"]),
        expression_condition("high-risk", "risk_score >= 0.7"),
    ],
    actions=[
        EnforcementAction(
            action_id="contain",
            channel="record",
            payload_builder=simple_payload("contain", "Contain the request"),
        ),
    ],
    severity="high",
    tags=["safety"],
    roles=["guardian"],
    version="1.2.0",
)

router.register_policy(policy)
results = router.route({"tag": "safety", "risk_score": 0.8})
print(results)
```

The example registers a single policy and agent, then routes an event. The
router selects the matching agent, builds an enforcement payload, records the
action via the default channel, and writes an audit entry plus a snapshot for
post-incident review.
