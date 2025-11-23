import random

from echo.evolver import EchoEvolver


def test_protocol_sentience_snapshot_tracks_convergence() -> None:
    evolver = EchoEvolver(rng=random.Random(7), time_source=lambda: 123456789)

    evolver.advance_cycle()
    snapshot = evolver.activate_protocol_sentience_layer()

    assert snapshot.version == "phase-viii"
    assert evolver.state.protocol_sentience is snapshot
    assert "protocol_sentience" in evolver.state.network_cache
    assert snapshot.convergence_index >= 0.55
    assert "phase-viii-scan-" in snapshot.optimization_cycles[0]
    assert "protocol-sentience" in evolver.state.event_log[-1].lower()


def test_protocol_sentience_scoring_spans_requested_domains() -> None:
    evolver = EchoEvolver(rng=random.Random(11), time_source=lambda: 987654321)
    evolver.advance_cycle()

    snapshot = evolver.activate_protocol_sentience_layer()

    expected_domains = {
        "governance",
        "identity",
        "routing",
        "attestation",
        "dns",
        "authority",
        "blueprint",
    }

    assert set(snapshot.cross_domain_scores) == expected_domains
    assert snapshot.convergence_index == round(
        sum(snapshot.cross_domain_scores.values()) / len(expected_domains), 3
    )
