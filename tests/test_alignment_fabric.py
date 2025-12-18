from governance import (
    Agent,
    EnforcementAction,
    GovernanceRouter,
    Policy,
    PolicyCondition,
    Role,
    clear_offline_state,
    list_snapshots,
    load_audit_log,
    load_policy_readiness,
    load_snapshot,
    simple_payload,
)
from governance import persistence


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


def test_audit_log_tracks_skipped_policies_and_snapshots():
    """Skipped policies should create audit entries and snapshot traces."""

    clear_offline_state()

    policy = Policy(
        policy_id="p-audit",
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
    router.route({"tag": "deny"}, actor="tester")

    events = load_audit_log()
    assert any(event["action"] == "route_skipped" for event in events)

    snapshots = list_snapshots()
    assert snapshots, "expected snapshot after routing trace"

    latest = load_snapshot(snapshots[-1])
    assert latest["trace"][0]["status"] == "skipped"
    assert latest["trace"][0]["reason"] == "conditions_failed"


def test_route_failures_are_audited_with_trace():
    """Routing failures (no agents) should be persisted for offline audits."""

    clear_offline_state()

    policy = Policy(
        policy_id="p-fail",
        description="Requires nonexistent agents",
        conditions=[PolicyCondition("always", "always", evaluator=lambda ctx: True)],
        actions=[
            EnforcementAction(
                action_id="noop",
                channel="record",
                payload_builder=simple_payload("noop"),
            )
        ],
        minimum_trust=0.5,
    )

    router = GovernanceRouter(policies=[policy], agents=[])
    router.route({}, actor="tester")

    events = load_audit_log()
    assert any(event["action"] == "route_failed" for event in events)

    snapshots = list_snapshots()
    latest = load_snapshot(snapshots[-1])
    assert latest["trace"][0]["status"] == "failed"
    assert "No agents" in latest["trace"][0]["reason"]


def test_policy_readiness_reports_unroutable_policies_and_persists_gap():
    """Readiness report should flag policies without eligible agents."""

    clear_offline_state()

    guardian_policy = Policy(
        policy_id="p-guardian",
        description="Guardian policy with enforceable trust",
        conditions=[PolicyCondition("always", "always", evaluator=lambda ctx: True)],
        actions=[
            EnforcementAction(
                action_id="contain",
                channel="record",
                payload_builder=simple_payload("contain"),
            )
        ],
        minimum_trust=0.75,
        roles=["guardian"],
        tags=["safety"],
    )

    ombuds_policy = Policy(
        policy_id="p-ombudsman",
        description="Ombudsman policy requires higher trust than available",
        conditions=[PolicyCondition("always", "always", evaluator=lambda ctx: True)],
        actions=[
            EnforcementAction(
                action_id="escalate",
                channel="record",
                payload_builder=simple_payload("escalate"),
            )
        ],
        minimum_trust=0.95,
        roles=["ombudsman"],
    )

    agents = [
        Agent("guardian-1", capabilities=["contain"], tags=["safety"], trust=0.9, role="guardian"),
        Agent("observer", capabilities=["observe"], tags=["insight"], trust=0.4, role="ombudsman"),
    ]

    router = GovernanceRouter(
        policies=[guardian_policy, ombuds_policy],
        agents=agents,
        roles=[Role("guardian", ""), Role("ombudsman", "")],
    )

    report = router.policy_readiness()

    assert any(entry["policy_id"] == "p-guardian" and entry["eligible_agents"] == ["guardian-1"] for entry in report["policies"])
    assert "p-ombudsman" in report["unroutable"]

    persisted = load_policy_readiness()
    assert persisted["counts"]["unroutable"] == 1


def test_clear_offline_state_removes_nested_directories(tmp_path):
    """Offline state cleanup should remove nested files and directories."""

    temp_base = tmp_path / ".offline_state"
    temp_base.mkdir(parents=True)
    nested = temp_base / "nested" / "deeper"
    nested.mkdir(parents=True)
    (temp_base / "root.txt").write_text("root", encoding="utf-8")
    (nested / "inner.txt").write_text("inner", encoding="utf-8")

    original_base = persistence.BASE
    persistence.BASE = temp_base
    try:
        persistence.clear_offline_state()
    finally:
        persistence.BASE = original_base

    assert temp_base.exists()
    assert list(temp_base.iterdir()) == []
