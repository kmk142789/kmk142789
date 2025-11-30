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

### EnforcementAction
- Specifies **where** a policy should be enforced via a channel name.
- Carries a payload builder so enforcement calls can be deterministic and
  traceable.
- Supports an optional `fallback_channel` when the primary channel is not
  registered.

### Policy
- Groups conditions and actions under a policy identifier.
- Uses tags and severity to guide agent selection.

### Agent
- Represents a responsible actor with capabilities, tags, and a trust score.
- Router prefers agents whose tags overlap policy tags and then sorts by trust.

### GovernanceRouter
- Central orchestrator that connects policies to agents and channels.
- Hooks into the offline persistence layer for audit logs and state snapshots.
- Ships with a default `record` channel that captures enforcement payloads
  without external dependencies.

## Example

```python
from governance import (
    Agent,
    EnforcementAction,
    GovernanceRouter,
    Policy,
    attribute_match_condition,
    simple_payload,
    threshold_condition,
)

router = GovernanceRouter()
router.register_agent(Agent("sentinel", capabilities=["containment"], tags=["safety"], trust=0.9))

policy = Policy(
    policy_id="p-high-risk",
    description="Escalate when risk score crosses the threshold for safety-tagged events.",
    conditions=[
        attribute_match_condition("safety-tag", "tag", ["safety"]),
        threshold_condition("risk", "risk_score", minimum=0.7),
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
)

router.register_policy(policy)
results = router.route({"tag": "safety", "risk_score": 0.8})
print(results)
```

The example registers a single policy and agent, then routes an event. The
router selects the matching agent, builds an enforcement payload, records the
action via the default channel, and writes an audit entry plus a snapshot for
post-incident review.
