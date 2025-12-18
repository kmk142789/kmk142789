from echo.autonomous_self_optimization import (
    AgentPerspective,
    AutonomousSelfOptimizer,
    CrossAgentNegotiationLayer,
    LeadProfile,
    LocalDeviceRuntime,
    OfflineTask,
    PolicyBundle,
    RealEstateQualificationModule,
)


def test_autonomous_self_optimization_cycle():
    bundle = PolicyBundle(name="core", version="v1", policies={"trust": 0.8})
    optimizer = AutonomousSelfOptimizer()

    outcome = optimizer.optimize(
        bundle, observed_convergence=0.72, streaming_health=0.65, hints=["baseline"]
    )

    assert outcome.policy_bundle.convergence_score == bundle.convergence_score
    assert outcome.convergence_delta != 0
    assert 0.1 <= outcome.streaming_threshold <= 0.9


def test_cross_agent_negotiation_layer_resolves_conflicts():
    layer = CrossAgentNegotiationLayer()
    decision = layer.negotiate(
        "refine-dossier",
        [
            AgentPerspective("alpha", priority=0.9, insights=["merge"], objections=[]),
            AgentPerspective("beta", priority=0.4, insights=["alert"], objections=["timing"]),
        ],
    )

    assert decision.resolved is True
    assert decision.selected_agent == "alpha"
    assert "timing" in decision.conflict_points
    assert "merge" in decision.merged_insights


def test_local_device_runtime_runs_offline_tasks():
    runtime = LocalDeviceRuntime()
    runtime.register_capability(
        "hash", lambda payload: {"length": len(payload["value"])}
    )

    runtime.submit_task(OfflineTask("hash", payload={"value": "offline"}))
    runtime.submit_task(OfflineTask("network", payload={}, requires_network=True))

    completed = runtime.run()
    assert any(task.executed for task in completed)
    assert runtime.pending and runtime.pending[0].requires_network


def test_local_device_runtime_executes_network_tasks_when_available():
    runtime = LocalDeviceRuntime()
    runtime.register_capability("network", lambda payload: {"ok": True, **payload})

    runtime.submit_task(OfflineTask("network", payload={"value": 3}, requires_network=True))

    runtime.run()  # should leave the network task pending
    assert runtime.pending and runtime.pending[0].requires_network

    runtime.run(network_available=True)
    assert not runtime.pending
    assert runtime.completed[-1].executed is True
    assert runtime.snapshot()["pending_requires_network"] == []


def test_local_device_runtime_surfaces_unregistered_capabilities():
    runtime = LocalDeviceRuntime()
    runtime.submit_task(OfflineTask("missing", payload={}, requires_network=False))

    runtime.run()

    assert runtime.pending[0].blocked_reason == "unregistered_capability"
    snapshot = runtime.snapshot()
    assert snapshot["pending_details"][0]["blocked_reason"] == "unregistered_capability"


def test_local_device_runtime_can_mark_capabilities_offline_only():
    runtime = LocalDeviceRuntime()
    runtime.register_capability(
        "sensitive",
        lambda payload: {"sealed": True, **payload},
        offline_ready=False,
        description="Requires network sync",
    )

    runtime.submit_task(OfflineTask("sensitive", payload={"value": 1}))
    runtime.run()

    assert runtime.pending[0].blocked_reason == "capability_offline_disabled"

    runtime.run(network_available=True)

    assert not runtime.pending
    assert runtime.completed[-1].executed is True
    assert runtime.snapshot()["capabilities"]["sensitive"]["offline_ready"] is False


def test_local_device_runtime_surfaces_handler_errors_and_continues():
    runtime = LocalDeviceRuntime()

    runtime.register_capability("boom", lambda payload: (_ for _ in ()).throw(ValueError("boom")))
    runtime.register_capability("ok", lambda payload: {"done": True})

    runtime.submit_task(OfflineTask("boom", payload={}))
    runtime.submit_task(OfflineTask("ok", payload={}))

    completed = runtime.run()

    assert runtime.pending[0].blocked_reason == "handler_error"
    assert runtime.pending[0].result == {"error": "boom"}
    assert any(task.executed for task in completed)


def test_real_estate_qualification_module_scores_leads():
    bundles = {
        "prime": PolicyBundle(name="prime", version="1.0", policies={}, convergence_score=0.9),
        "growth": PolicyBundle(
            name="growth",
            version="1.1",
            policies={},
            convergence_score=0.6,
            streaming_threshold=0.3,
        ),
    }
    module = RealEstateQualificationModule(policy_bundles=bundles)

    lead = LeadProfile(
        name="Ada",
        credit_score=720,
        liquidity=120000,
        jurisdictions=["US"],
        use_case="multi-family",
        intents=["buy"],
    )

    result = module.qualify(lead)
    assert result.qualification_score > 0.5
    assert result.recommended_bundle in {"prime", "growth"}
    assert result.risk_flags == []
