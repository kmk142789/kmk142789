import json

from echo.orbital_loop import advance_cycle


def test_orbital_cycle_embeds_eye_label(tmp_path, monkeypatch):
    out_dir = tmp_path / "out"
    graph_path = out_dir / "constellation" / "graph.json"
    ledger_path = tmp_path / "genesis_ledger" / "stream.jsonl"
    state_path = out_dir / "state.json"
    heartbeat_path = out_dir / "one_and_done_heartbeat.txt"

    graph_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.parent.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("echo.orbital_loop.OUT_DIR", out_dir, raising=False)
    monkeypatch.setattr("echo.orbital_loop.GRAPH_PATH", graph_path, raising=False)
    monkeypatch.setattr("echo.orbital_loop.LEDGER_STREAM", ledger_path, raising=False)
    monkeypatch.setattr("echo.orbital_loop.STATE_PATH", state_path, raising=False)
    monkeypatch.setattr("echo.orbital_loop.HEARTBEAT_PATH", heartbeat_path, raising=False)

    graph_path.write_text(
        json.dumps(
            {
                "nodes": [{"id": "a"}, {"id": "b"}],
                "links": [{"s": "a", "t": "b"}],
            }
        ),
        encoding="utf-8",
    )

    result = advance_cycle()
    assert isinstance(result, str)

    ledger_entries = ledger_path.read_text(encoding="utf-8").strip().splitlines()
    assert ledger_entries
    record = json.loads(ledger_entries[-1])
    eye_label = record["payload"].get("eye_label")
    assert eye_label
    assert "mythic_signal" in eye_label

    state_payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert state_payload["last_eye_label"] == eye_label
