import json
import time
from pathlib import Path

from echo.orbital_loop import (
    HEARTBEAT_PATH,
    GRAPH_PATH,
    LEDGER_STREAM,
    STATE_PATH,
    OrbitalState,
    advance_cycle,
)


def test_advance_cycle_creates_artifacts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    GRAPH_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_STREAM.parent.mkdir(parents=True, exist_ok=True)

    msg = advance_cycle()
    assert isinstance(msg, str) and msg

    assert HEARTBEAT_PATH.exists()
    heartbeat = HEARTBEAT_PATH.read_text().strip()
    assert "echo_heartbeat" in heartbeat

    assert STATE_PATH.exists()
    state_payload = json.loads(STATE_PATH.read_text())
    assert state_payload["cycles"] == 1
    assert state_payload["last_next_step"]

    assert LEDGER_STREAM.exists()
    entries = LEDGER_STREAM.read_text().splitlines()
    assert len(entries) == 1
    record = json.loads(entries[0])
    assert record["event"] == "orbital_cycle"
    assert "next_step" in record["payload"]


def test_multiple_cycles_increment(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for _ in range(3):
        advance_cycle()
        time.sleep(0.01)

    state = OrbitalState.load()
    assert state.cycles == 3
