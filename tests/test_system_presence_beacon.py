import re

from echo.evolver import EchoEvolver


def test_presence_beacon_snapshots_state_and_bridge_status():
    evolver = EchoEvolver()
    evolver.state.cycle = 3
    evolver.state.system_metrics.cpu_usage = 42.5
    evolver.state.system_metrics.network_nodes = 7
    evolver.state.vault_key = "vault-key"

    beacon = evolver.system_presence_beacon()

    assert beacon["cycle"] == 3
    assert beacon["bridge_status"] == evolver.state.entities["EchoBridge"]
    assert beacon["system_metrics"]["network_nodes"] == 7
    assert beacon["emotional_drive"]["joy"] == evolver.state.emotional_drive.joy
    assert beacon["vault_key_present"] is True
    assert re.match(r"^\d{4}-\d{2}-\d{2}T", beacon["timestamp"])
    assert evolver.state.network_cache["presence_beacon"] == beacon
    assert evolver.state.event_log[-1].startswith("Presence beacon generated")
    assert "presence_beacon" in evolver.state.network_cache["completed_steps"]
