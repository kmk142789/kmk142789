import pytest

from governance import (
    Agent,
    EnforcementAction,
    GovernanceRouter,
    Policy,
    PolicyCondition,
    simple_payload,
)


def test_route_trace_reports_failed_conditions():
    """Router should record why a policy was skipped for offline audits."""

    policy = Policy(
        policy_id="p-safety",
        description="Requires allow tag",
        conditions=[
            PolicyCondition(
                name="allow-tag",
                description="tag must be allow",
                evaluator=lambda ctx: ctx.get("tag") == "allow",
            )
        ],
        actions=[
            EnforcementAction(
                action_id="noop",
                channel="record",
                payload_builder=simple_payload("noop"),
            )
        ],
    )

    router = GovernanceRouter(policies=[policy], agents=[Agent("sentinel", capabilities=[])])

    results = router.route({"tag": "deny"})

    assert results == []
    assert router.last_route_trace[0]["status"] == "skipped"
    assert router.last_route_trace[0]["failures"] == ["allow-tag"]


def test_minimum_trust_filters_agents_and_records_trace():
    """Minimum trust should prevent low-trust agents from executing."""

    trusted = Agent("trusted", capabilities=["contain"], trust=0.9)
    untrusted = Agent("shadow", capabilities=["contain"], trust=0.2)

    policy = Policy(
        policy_id="p-trust",
        description="Only trusted agents should run",
        conditions=[PolicyCondition("always", "always", evaluator=lambda ctx: True)],
        actions=[
            EnforcementAction(
                action_id="contain",
                channel="record",
                payload_builder=simple_payload("contain"),
            )
        ],
        minimum_trust=0.5,
    )

    router = GovernanceRouter(policies=[policy], agents=[trusted, untrusted])

    results = router.route({"tag": "any"})

    assert results[0]["agent"] == "trusted"
    assert router.last_route_trace[0]["agent"] == "trusted"
    assert router.last_route_trace[0]["actions"] == ["contain"]
