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
