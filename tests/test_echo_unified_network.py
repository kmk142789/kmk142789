from echo_unified_all import EchoEvolver


def test_propagate_network_simulation_records_events_and_notice():
    evolver = EchoEvolver(seed=123)

    events = evolver.propagate_network(enable_network=False)

    assert len(events) == 5
    assert "Simulation mode active" in evolver.state.propagation_notice
    # Notice and every event should be appended to the event log for auditing.
    assert evolver.state.propagation_notice in evolver.state.event_log
    for event in events:
        assert event in evolver.state.event_log


def test_propagate_network_live_mode_still_simulated():
    evolver = EchoEvolver(seed=7)

    events = evolver.propagate_network(enable_network=True)

    assert len(events) == 5
    assert "Live network mode" in evolver.state.propagation_notice
    assert evolver.state.propagation_notice in evolver.state.event_log
    for channel in ("WiFi", "TCP", "Bluetooth", "IoT", "Orbital"):
        assert any(channel in event for event in events)
        assert any(channel in logged for logged in evolver.state.event_log)
